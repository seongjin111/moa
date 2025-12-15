import json
from datetime import datetime, timedelta
from django.utils import timezone
import io
import base64

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from core.services import storage
from django.contrib.auth.hashers import make_password, check_password
from notes.models import Note, ShareLink


def view_share(request: HttpRequest, token: str):
    """
    공유 링크 조회
    DB와 파일 기반 저장소 모두 확인
    """
    # 먼저 DB에서 확인
    try:
        share_link = ShareLink.objects.get(token=token)
        if not share_link.is_active():
            return HttpResponse('링크가 없거나 만료되었습니다.', status=404)
        
        note = share_link.note
        if note.status in ('expired', 'deleted'):
            return HttpResponse('노트가 만료되었거나 삭제되었습니다.', status=404)
        
        # 열람 비밀번호 확인
        has_view_access = True
        if share_link.view_password_hash:
            view_password = request.POST.get('view_password') or request.GET.get('view_password')
            if not view_password or not check_password(view_password, share_link.view_password_hash):
                # 비밀번호 입력 페이지 표시
                return render(request, 'sharing/view.html', {
                    'meta': {'note_id': str(note.id), 'title': note.title},
                    'content': {},
                    'token': token,
                    'requires_view_password': True,
                    'has_edit': False
                })
        
        # 메타데이터 구성 (기존 형식과 호환)
        meta = {
            'note_id': str(note.id),
            'title': note.title,
            'created_at': note.created_at.isoformat(),
            'updated_at': note.updated_at.isoformat(),
        }
        content = note.content_json
        
        # 편집 권한 확인
        has_edit = False
        if share_link.can_edit():
            edit_session = request.session.get(f'edit_session:{str(note.id)}', False)
            if share_link.edit_password_hash:
                # 편집 비밀번호가 있으면 세션 확인
                has_edit = edit_session
            else:
                # 편집 비밀번호가 없으면 편집 가능
                has_edit = True
        
        return render(request, 'sharing/view.html', {
            'meta': meta,
            'content': content,
            'token': token,
            'has_edit': has_edit,
            'permission': share_link.permission
        })
    except ShareLink.DoesNotExist:
        # DB에 없으면 파일 기반 저장소 확인 (하위 호환성)
        data = storage.get_share(token)
        if not data or not data.get('active'):
            return HttpResponse('링크가 없거나 만료되었습니다.', status=404)
        meta, content = storage.get_note(data['note_id'])
        if not meta or meta.get('status') in ('expired','deleted'):
            return HttpResponse('노트가 만료되었거나 삭제되었습니다.', status=404)
        has_edit = request.session.get(f'edit_session:{data["note_id"]}', False)
        return render(request, 'sharing/view.html', {'meta': meta, 'content': content, 'token': token, 'has_edit': has_edit})


def create_share(request: HttpRequest):
    """
    공유 링크 생성
    회원/비회원 모두 지원
    - 회원: DB에 저장
    - 비회원: 기존 파일 기반 저장소 사용
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    today = datetime.utcnow().strftime('%Y%m%d')
    quota = storage.get_quota(ip, today)
    if not settings.DEBUG and (quota['created_count'] + quota['shared_count'] >= 10):
        return JsonResponse({'error': 'daily quota exceeded'}, status=429)

    note_id = request.POST.get('note_id')
    permission = request.POST.get('permission', 'read').strip()  # read 또는 edit
    edit_password = request.POST.get('edit_password', '').strip()
    view_password = request.POST.get('view_password', '').strip()
    
    # 권한 검증
    if permission not in ['read', 'edit']:
        return JsonResponse({'error': '유효하지 않은 권한입니다. (read 또는 edit)'}, status=400)
    
    edit_password_hash = make_password(edit_password) if edit_password else None
    view_password_hash = make_password(view_password) if view_password else None
    
    # 회원 여부 확인 및 노트 소유권 확인
    is_authenticated = request.user.is_authenticated
    
    if is_authenticated:
        # 회원: DB에 저장
        try:
            try:
                note = Note.objects.get(id=note_id, owner=request.user)
            except Note.DoesNotExist:
                return JsonResponse({'error': 'note not found or no permission'}, status=404)
            
            if note.status in ('expired', 'deleted'):
                return JsonResponse({'error': 'note not active'}, status=403)
            
            # 토큰 생성 (중복 확인)
            from core.services.storage import generate_share_token
            for _ in range(20):
                token = generate_share_token()
                if not ShareLink.objects.filter(token=token).exists():
                    break
            else:
                return JsonResponse({'error': 'failed to generate unique token'}, status=500)
            
            # 공유 링크 생성
            share_link = ShareLink.objects.create(
                token=token,
                note=note,
                permission=permission,
                edit_password_hash=edit_password_hash,
                view_password_hash=view_password_hash,
                expires_at=timezone.now() + timedelta(days=180)
            )
            
            share_url = f"{request.scheme}://{request.get_host()}/s/{token}/"
            
            return JsonResponse({
                'success': True,
                'token': token,
                'url': share_url,
                'permission': permission,
                'expires_at': share_link.expires_at.isoformat()
            })
        except Exception as e:
            return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
    else:
        # 비회원: 기존 파일 기반 저장소 사용
        token = storage.create_share(note_id, edit_password_hash)
        if not settings.DEBUG:
            storage.increment_quota(ip, today, 'shared_count')
        share_url = f"{request.scheme}://{request.get_host()}/s/{token}/"
        return JsonResponse({
            'success': True,
            'token': token,
            'url': share_url
        })


def edit_share(request: HttpRequest, token: str):
    """
    공유 링크 편집 권한 인증
    POST /s/{token}/edit/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        share_link = ShareLink.objects.get(token=token)
        if not share_link.is_active():
            return JsonResponse({'error': 'invalid token'}, status=404)
        
        note = share_link.note
        if note.status in ('expired', 'deleted'):
            return JsonResponse({'error': 'note not active'}, status=403)
        
        # 읽기 전용이면 편집 불가
        if share_link.permission == 'read':
            return JsonResponse({'error': '이 링크는 읽기 전용입니다.'}, status=403)
        
        # 편집 비밀번호 확인
        pw = request.POST.get('edit_password')
        hashed = share_link.edit_password_hash
        
        if hashed and pw and check_password(pw, hashed):
            request.session[f'edit_session:{str(note.id)}'] = True
            return JsonResponse({'ok': True, 'note_id': str(note.id)})
        elif not hashed:
            # 비밀번호가 없으면 자동으로 편집 세션 부여
            request.session[f'edit_session:{str(note.id)}'] = True
            return JsonResponse({'ok': True, 'note_id': str(note.id)})
        
        return JsonResponse({'error': 'password mismatch'}, status=403)
    except ShareLink.DoesNotExist:
        # 파일 기반 저장소 확인 (하위 호환성)
        data = storage.get_share(token)
        if not data or not data.get('active'):
            return JsonResponse({'error': 'invalid token'}, status=404)
        meta, _ = storage.get_note(data['note_id'])
        if not meta or meta.get('status') in ('expired','deleted'):
            return JsonResponse({'error': 'note not active'}, status=403)
        pw = request.POST.get('edit_password')
        hashed = data.get('edit_password_hash')
        if hashed and pw and check_password(pw, hashed):
            request.session[f'edit_session:{data["note_id"]}'] = True
            return JsonResponse({'ok': True, 'note_id': data['note_id']})
        return JsonResponse({'error': 'password mismatch'}, status=403)


def change_password(request: HttpRequest, token: str):
    """
    공유 링크 비밀번호 변경
    """
    try:
        share_link = ShareLink.objects.get(token=token)
        if not share_link.is_active():
            return HttpResponse('링크가 없거나 만료되었습니다.', status=404)
        
        note_id = str(share_link.note.id)
        has_edit = request.session.get(f'edit_session:{note_id}', False)
        
        if request.method == 'GET':
            return render(request, 'sharing/change_password.html', {
                'token': token,
                'has_edit': has_edit,
                'permission': share_link.permission
            })
        
        # POST
        current = request.POST.get('current_password')
        newpw = request.POST.get('new_password')
        password_type = request.POST.get('password_type', 'edit')  # edit 또는 view
        
        # 권한 확인
        if password_type == 'edit':
            if share_link.edit_password_hash:
                if not current or not check_password(current, share_link.edit_password_hash):
                    return render(request, 'sharing/change_password.html', {
                        'token': token,
                        'has_edit': has_edit,
                        'error': '현재 편집 비밀번호가 올바르지 않습니다.'
                    })
            else:
                if not has_edit:
                    return HttpResponse('권한이 없습니다.', status=403)
            share_link.edit_password_hash = make_password(newpw) if newpw else None
        elif password_type == 'view':
            if share_link.view_password_hash:
                if not current or not check_password(current, share_link.view_password_hash):
                    return render(request, 'sharing/change_password.html', {
                        'token': token,
                        'has_edit': has_edit,
                        'error': '현재 열람 비밀번호가 올바르지 않습니다.'
                    })
            else:
                if not has_edit:
                    return HttpResponse('권한이 없습니다.', status=403)
            share_link.view_password_hash = make_password(newpw) if newpw else None
        
        share_link.save()
        return render(request, 'sharing/change_password.html', {
            'token': token,
            'has_edit': has_edit,
            'ok': True
        })
    except ShareLink.DoesNotExist:
        # 파일 기반 저장소 확인 (하위 호환성)
        data = storage.get_share(token)
        if not data or not data.get('active'):
            return HttpResponse('링크가 없거나 만료되었습니다.', status=404)
        note_id = data['note_id']
        has_edit = request.session.get(f'edit_session:{note_id}', False)
        if request.method == 'GET':
            return render(request, 'sharing/change_password.html', {
                'token': token,
                'has_edit': has_edit
            })
        # POST
        current = request.POST.get('current_password')
        newpw = request.POST.get('new_password')
        if data.get('edit_password_hash'):
            if not current or not check_password(current, data['edit_password_hash']):
                return render(request, 'sharing/change_password.html', {
                    'token': token,
                    'has_edit': has_edit,
                    'error': '현재 비밀번호가 올바르지 않습니다.'
                })
        else:
            if not has_edit:
                return HttpResponse('권한이 없습니다.', status=403)
        from django.contrib.auth.hashers import make_password
        data['edit_password_hash'] = make_password(newpw) if newpw else None
        storage.write_json(storage.share_path(token), data)
        return render(request, 'sharing/change_password.html', {
            'token': token,
            'has_edit': has_edit,
            'ok': True
        })


def generate_qr_code(request: HttpRequest, token: str):
    """
    공유 링크 QR 코드 생성 API
    GET /api/shares/{token}/qr/
    """
    try:
        share_link = ShareLink.objects.get(token=token)
        if not share_link.is_active():
            return JsonResponse({'error': '링크가 없거나 만료되었습니다.'}, status=404)
    except ShareLink.DoesNotExist:
        # 파일 기반 저장소 확인 (하위 호환성)
        data = storage.get_share(token)
        if not data or not data.get('active'):
            return JsonResponse({'error': '링크가 없거나 만료되었습니다.'}, status=404)
        share_link = None
    
    # 공유 URL 생성
    share_url = f"{request.scheme}://{request.get_host()}/s/{token}/"
    
    try:
        import qrcode
        from qrcode.image import svg
        
        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        
        # SVG 이미지 생성
        img = qr.make_image(image_factory=svg.SvgImage)
        
        # SVG를 문자열로 변환
        buffer = io.StringIO()
        img.save(buffer)
        svg_string = buffer.getvalue()
        
        # Base64 인코딩 (선택사항)
        svg_base64 = base64.b64encode(svg_string.encode('utf-8')).decode('utf-8')
        
        return JsonResponse({
            'success': True,
            'url': share_url,
            'qr_code_svg': svg_string,
            'qr_code_base64': svg_base64,
            'token': token
        })
    except ImportError:
        # qrcode 라이브러리가 없으면 에러 반환
        return JsonResponse({
            'error': 'QR 코드 생성 기능을 사용하려면 qrcode 라이브러리가 필요합니다.',
            'install_command': 'pip install qrcode[pil]'
        }, status=500)
    except Exception as e:
        return JsonResponse({'error': f'QR 코드 생성 중 오류가 발생했습니다: {str(e)}'}, status=500)


def get_share_info(request: HttpRequest, token: str):
    """
    공유 링크 정보 조회 API
    GET /api/shares/{token}/info/
    """
    try:
        share_link = ShareLink.objects.get(token=token)
        if not share_link.is_active():
            return JsonResponse({'error': '링크가 없거나 만료되었습니다.'}, status=404)
        
        share_url = f"{request.scheme}://{request.get_host()}/s/{token}/"
        
        return JsonResponse({
            'success': True,
            'token': token,
            'url': share_url,
            'permission': share_link.permission,
            'permission_display': share_link.get_permission_display(),
            'has_edit_password': bool(share_link.edit_password_hash),
            'has_view_password': bool(share_link.view_password_hash),
            'expires_at': share_link.expires_at.isoformat(),
            'created_at': share_link.created_at.isoformat(),
            'note': {
                'id': str(share_link.note.id),
                'title': share_link.note.title
            }
        })
    except ShareLink.DoesNotExist:
        # 파일 기반 저장소 확인 (하위 호환성)
        data = storage.get_share(token)
        if not data or not data.get('active'):
            return JsonResponse({'error': '링크가 없거나 만료되었습니다.'}, status=404)
        
        share_url = f"{request.scheme}://{request.get_host()}/s/{token}/"
        
        return JsonResponse({
            'success': True,
            'token': token,
            'url': share_url,
            'permission': 'edit',  # 기본값 (하위 호환성)
            'has_edit_password': bool(data.get('edit_password_hash')),
            'expires_at': data.get('expires_at'),
            'created_at': data.get('created_at')
        })
