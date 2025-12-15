from datetime import datetime, timedelta
from django.utils import timezone

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from core.services import storage
from core.services.diff import html_diff
from core.utils import can_create_note, can_edit_note
from .models import Note, NoteHistory, ShareLink, MediaFile
from .utils import validate_image, validate_audio, validate_video, get_file_type_from_mime
from core.models import Team
import bleach
from bleach.css_sanitizer import CSSSanitizer
from PIL import Image, UnidentifiedImageError
from pathlib import Path
from django.conf import settings


def editor(request: HttpRequest):
    # 원노트 스타일 에디터 사용
    return render(request, 'notes/editor_onenote.html', {"initial_html": None, "note_id": None})


def save_note(request: HttpRequest):
    """
    노트 저장 API
    회원/비회원 모두 지원
    - 회원: DB에 저장
    - 비회원: 기존 파일 기반 저장소 사용 (하위 호환성)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    client_token = request.COOKIES.get('client_token')
    if not client_token:
        return JsonResponse({'error': 'no client token'}, status=400)

    # IP quota check (비회원용)
    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    today = datetime.utcnow().strftime('%Y%m%d')
    quota = storage.get_quota(ip, today)
    if not settings.DEBUG and (quota['created_count'] + quota['shared_count'] >= 10):
        return JsonResponse({'error': 'daily quota exceeded'}, status=429)

    title = request.POST.get('title', '제목 없음')
    team_id = request.POST.get('team_id', '').strip()  # 팀 ID (선택사항)
    
    # content_json from client (TipTap document JSON 또는 원노트 캔버스)
    try:
        import json
        content_json = json.loads(request.POST.get('content_json', '{}'))
    except Exception:
        content_json = {}

    # 원노트 캔버스 형식인 경우 그대로 저장
    if content_json.get('type') == 'onenote_canvas':
        # 캔버스 데이터는 그대로 저장 (추가 검증 필요시 여기서 처리)
        pass
    # sanitize HTML if provided in our interim format
    elif content_json.get('type') == 'html':
        allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
            'p','br','b','i','u','strong','em','ul','ol','li','h1','h2','h3','h4','h5','h6','blockquote','code','pre','img','a','span','div','ins','del','hr'
        })
        allowed_attrs = {**bleach.sanitizer.ALLOWED_ATTRIBUTES,
                         'a': ['href','title','target','rel'],
                         'img': ['src','alt','title'],
                         'span': ['style'],
                         'p': ['style'], 'div': ['style'],
                         'h1': ['style'],'h2': ['style'],'h3': ['style'],'h4': ['style'],'h5': ['style'],'h6': ['style']}
        cleaner = bleach.Cleaner(
            tags=list(allowed_tags),
            attributes=allowed_attrs,
            css_sanitizer=CSSSanitizer(
                allowed_css_properties=[
                    'color','background-color','text-align','font-size','font-family',
                    'line-height','margin','padding','text-decoration'
                ]
            ),
            strip=True
        )
        html = cleaner.clean(content_json.get('html',''))
        content_json['html'] = html

    # 회원 여부 확인
    is_authenticated = request.user.is_authenticated
    
    # Support create or update
    existing_note_id = request.POST.get('note_id')
    
    if is_authenticated:
        # 회원: DB에 저장
        try:
            # 팀 확인 및 권한 검증
            team = None
            if team_id:
                try:
                    team = Team.objects.get(id=team_id)
                    if not can_create_note(request.user, team) and not existing_note_id:
                        return JsonResponse({'error': '팀 노트 생성 권한이 없습니다.'}, status=403)
                except Team.DoesNotExist:
                    return JsonResponse({'error': '팀을 찾을 수 없습니다.'}, status=404)
            
            if existing_note_id:
                # 기존 노트 업데이트
                try:
                    note = Note.objects.get(id=existing_note_id, owner=request.user)
                except Note.DoesNotExist:
                    return JsonResponse({'error': 'note not found or no permission'}, status=404)
                
                if note.status in ('expired', 'deleted'):
                    return JsonResponse({'error': 'note not active'}, status=403)
                
                # 히스토리 생성
                before_html = ''
                if note.content_json.get('type') == 'html':
                    before_html = note.content_json.get('html', '')
                after_html = content_json.get('html', '') if content_json.get('type') == 'html' else ''
                diff_html = html_diff(before_html, after_html)
                
                # 팀 변경 권한 확인
                if team_id:
                    try:
                        new_team = Team.objects.get(id=team_id)
                        if note.team != new_team:
                            if not can_create_note(request.user, new_team):
                                return JsonResponse({'error': '팀 노트 생성 권한이 없습니다.'}, status=403)
                            note.team = new_team
                    except Team.DoesNotExist:
                        return JsonResponse({'error': '팀을 찾을 수 없습니다.'}, status=404)
                elif note.team:
                    # 팀에서 개인 노트로 변경
                    note.team = None
                
                # 편집 권한 확인
                if not can_edit_note(request.user, note):
                    return JsonResponse({'error': '노트 편집 권한이 없습니다.'}, status=403)
                
                # 노트 업데이트
                note.title = title
                note.content_json = content_json
                note.save()
                
                # 히스토리 저장
                NoteHistory.objects.create(
                    note=note,
                    before_html=before_html,
                    after_html=after_html,
                    diff_html=diff_html,
                    editor_session_id=request.session.session_key or 'session'
                )
                
                return JsonResponse({'note_id': str(note.id), 'content': content_json})
            else:
                # 새 노트 생성
                note = Note.objects.create(
                    title=title,
                    content_json=content_json,
                    owner=request.user,
                    creator_ip=ip,
                    team=team
                )
                
                # 팀 노트 수 증가
                if team:
                    team.notes_count += 1
                    team.save(update_fields=['notes_count'])
                
                # 사용자 프로필 노트 수 증가
                if hasattr(request.user, 'profile'):
                    request.user.profile.notes_count += 1
                    request.user.profile.save()
                
                return JsonResponse({'note_id': str(note.id)})
        except Exception as e:
            return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
    else:
        # 비회원: 기존 파일 기반 저장소 사용 (하위 호환성)
        if not existing_note_id:
            note_id = storage.create_note(title, client_token, ip, content_json)
            if not settings.DEBUG:
                storage.increment_quota(ip, today, 'created_count')
            return JsonResponse({'note_id': note_id})
        else:
            meta, current = storage.get_note(existing_note_id)
            if meta and meta.get('status') in ('expired','deleted'):
                return JsonResponse({'error': 'note not active'}, status=403)
            before_html = ''
            if current and current.get('type') == 'html':
                before_html = current.get('html','')
            after_html = content_json.get('html','') if content_json.get('type')=='html' else ''
            diff_html = html_diff(before_html, after_html)
            storage.save_note_content(existing_note_id, content_json)
            storage.add_history(existing_note_id, before_html, after_html, diff_html, request.session.session_key or 'session')
            return JsonResponse({'note_id': existing_note_id, 'content': content_json})


def upload_image(request: HttpRequest):
    """
    이미지 파일 업로드 API
    POST /upload-image/
    기존 기능 유지 (하위 호환성)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    client_token = request.COOKIES.get('client_token')
    if not client_token:
        return JsonResponse({'error': 'no client token'}, status=400)
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'no file'}, status=400)
    
    # 파일 검증
    is_valid, mime_type, error = validate_image(file)
    if not is_valid:
        return JsonResponse({'error': error}, status=400)
    
    # Validate image
    try:
        img = Image.open(file)
        img = img.convert('RGB')  # strip alpha/exif implicitly handled below
    except UnidentifiedImageError:
        return JsonResponse({'error': 'invalid image'}, status=400)

    # Resize if too large
    max_side = 2000
    w, h = img.size
    if max(w, h) > max_side:
        if w >= h:
            new_w = max_side
            new_h = int(h * (max_side / w))
        else:
            new_h = max_side
            new_w = int(w * (max_side / h))
        img = img.resize((new_w, new_h))

    # Save to MEDIA/uploads/{client_token}/{uuid}.webp
    from uuid import uuid4
    rel_dir = Path('uploads') / client_token
    abs_dir = Path(settings.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.webp"
    abs_path = abs_dir / filename
    img.save(abs_path, format='WEBP', quality=85, method=6)
    url = f"{settings.MEDIA_URL}{rel_dir.as_posix()}/{filename}"
    
    # 회원인 경우 MediaFile에 저장
    if request.user.is_authenticated:
        try:
            MediaFile.objects.create(
                file=f"{rel_dir.as_posix()}/{filename}",
                file_type='image',
                mime_type='image/webp',
                file_size=abs_path.stat().st_size,
                uploader=request.user
            )
        except Exception:
            pass  # 저장 실패해도 URL은 반환
    
    return JsonResponse({'url': url})


def upload_audio(request: HttpRequest):
    """
    음성 파일 업로드 API
    POST /api/media/upload-audio/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    client_token = request.COOKIES.get('client_token')
    if not client_token:
        return JsonResponse({'error': 'no client token'}, status=400)
    
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'no file'}, status=400)
    
    # 파일 검증
    is_valid, mime_type, error = validate_audio(file)
    if not is_valid:
        return JsonResponse({'error': error}, status=400)
    
    # 파일 저장
    from uuid import uuid4
    file_type = get_file_type_from_mime(mime_type)
    ext = Path(file.name).suffix.lower()
    if not ext:
        # MIME 타입에서 확장자 추정
        if 'mp3' in mime_type or 'mpeg' in mime_type:
            ext = '.mp3'
        elif 'wav' in mime_type:
            ext = '.wav'
        elif 'ogg' in mime_type:
            ext = '.ogg'
        elif 'webm' in mime_type:
            ext = '.webm'
        elif 'm4a' in mime_type or 'mp4' in mime_type:
            ext = '.m4a'
        else:
            ext = '.mp3'  # 기본값
    
    # 저장 경로 결정
    if request.user.is_authenticated:
        rel_dir = Path('media') / 'audio' / str(request.user.id)
    else:
        rel_dir = Path('media') / 'audio' / client_token
    
    abs_dir = Path(settings.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{uuid4().hex}{ext}"
    abs_path = abs_dir / filename
    
    # 파일 저장
    with open(abs_path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)
    
    url = f"{settings.MEDIA_URL}{rel_dir.as_posix()}/{filename}"
    
    # MediaFile에 저장
    try:
        media_file = MediaFile.objects.create(
            file=f"{rel_dir.as_posix()}/{filename}",
            file_type=file_type,
            mime_type=mime_type,
            file_size=file.size,
            uploader=request.user if request.user.is_authenticated else None,
            uploader_client_token=client_token if not request.user.is_authenticated else None
        )
        return JsonResponse({
            'success': True,
            'url': url,
            'file_id': str(media_file.id),
            'file_type': file_type,
            'file_size': file.size
        })
    except Exception as e:
        return JsonResponse({'error': f'파일 저장 중 오류가 발생했습니다: {str(e)}'}, status=500)


def upload_video(request: HttpRequest):
    """
    영상 파일 업로드 API
    POST /api/media/upload-video/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    client_token = request.COOKIES.get('client_token')
    if not client_token:
        return JsonResponse({'error': 'no client token'}, status=400)
    
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'no file'}, status=400)
    
    # 파일 검증
    is_valid, mime_type, error = validate_video(file)
    if not is_valid:
        return JsonResponse({'error': error}, status=400)
    
    # 파일 저장
    from uuid import uuid4
    file_type = get_file_type_from_mime(mime_type)
    ext = Path(file.name).suffix.lower()
    if not ext:
        # MIME 타입에서 확장자 추정
        if 'mp4' in mime_type:
            ext = '.mp4'
        elif 'webm' in mime_type:
            ext = '.webm'
        elif 'ogg' in mime_type or 'ogv' in mime_type:
            ext = '.ogv'
        elif 'quicktime' in mime_type or 'mov' in mime_type:
            ext = '.mov'
        else:
            ext = '.mp4'  # 기본값
    
    # 저장 경로 결정
    if request.user.is_authenticated:
        rel_dir = Path('media') / 'video' / str(request.user.id)
    else:
        rel_dir = Path('media') / 'video' / client_token
    
    abs_dir = Path(settings.MEDIA_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{uuid4().hex}{ext}"
    abs_path = abs_dir / filename
    
    # 파일 저장
    with open(abs_path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)
    
    url = f"{settings.MEDIA_URL}{rel_dir.as_posix()}/{filename}"
    
    # MediaFile에 저장
    try:
        media_file = MediaFile.objects.create(
            file=f"{rel_dir.as_posix()}/{filename}",
            file_type=file_type,
            mime_type=mime_type,
            file_size=file.size,
            uploader=request.user if request.user.is_authenticated else None,
            uploader_client_token=client_token if not request.user.is_authenticated else None
        )
        return JsonResponse({
            'success': True,
            'url': url,
            'file_id': str(media_file.id),
            'file_type': file_type,
            'file_size': file.size
        })
    except Exception as e:
        return JsonResponse({'error': f'파일 저장 중 오류가 발생했습니다: {str(e)}'}, status=500)


def list_media_files(request: HttpRequest):
    """
    업로드한 미디어 파일 목록 조회 API
    GET /api/media/files/
    Query params: ?file_type=image|audio|video (선택)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    
    file_type = request.GET.get('file_type', '').strip()
    
    # 사용자가 업로드한 파일만 조회
    files = MediaFile.objects.filter(uploader=request.user)
    
    if file_type:
        files = files.filter(file_type=file_type)
    
    files = files.order_by('-created_at')[:100]  # 최근 100개만
    
    result = []
    for media_file in files:
        result.append({
            'id': str(media_file.id),
            'file_type': media_file.file_type,
            'mime_type': media_file.mime_type,
            'file_size': media_file.file_size,
            'url': f"{settings.MEDIA_URL}{media_file.file.name}",
            'created_at': media_file.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'files': result,
        'count': len(result)
    })


def get_media_file(request: HttpRequest, file_id: str):
    """
    미디어 파일 정보 조회 API
    GET /api/media/files/{file_id}/
    """
    try:
        media_file = MediaFile.objects.get(id=file_id)
        
        # 권한 확인 (업로더만 조회 가능)
        if request.user.is_authenticated:
            if media_file.uploader != request.user:
                return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        else:
            client_token = request.COOKIES.get('client_token')
            if media_file.uploader_client_token != client_token:
                return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
        return JsonResponse({
            'success': True,
            'file': {
                'id': str(media_file.id),
                'file_type': media_file.file_type,
                'mime_type': media_file.mime_type,
                'file_size': media_file.file_size,
                'url': f"{settings.MEDIA_URL}{media_file.file.name}",
                'created_at': media_file.created_at.isoformat()
            }
        })
        
    except MediaFile.DoesNotExist:
        return JsonResponse({'error': '파일을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'파일 조회 중 오류가 발생했습니다: {str(e)}'}, status=500)


def get_note_content(request: HttpRequest, note_id: str):
    """
    노트 내용 조회 API
    DB 우선, 없으면 파일 기반 저장소 확인
    """
    try:
        # DB에서 먼저 확인
        note = Note.objects.get(id=note_id, status='active')
        return JsonResponse({
            'note_id': str(note.id),
            'title': note.title,
            'content': note.content_json
        })
    except Note.DoesNotExist:
        # 파일 기반 저장소 확인 (하위 호환성)
        meta, content = storage.get_note(note_id)
        if not meta:
            return JsonResponse({'error': 'not found'}, status=404)
        return JsonResponse({
            'note_id': note_id,
            'title': meta.get('title', '제목 없음'),
            'content': content or {}
        })
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
