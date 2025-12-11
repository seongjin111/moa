import json
from datetime import datetime

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from core.services import storage
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings


def view_share(request: HttpRequest, token: str):
    data = storage.get_share(token)
    if not data or not data.get('active'):
        return HttpResponse('링크가 없거나 만료되었습니다.', status=404)
    meta, content = storage.get_note(data['note_id'])
    if not meta or meta.get('status') in ('expired','deleted'):
        return HttpResponse('노트가 만료되었거나 삭제되었습니다.', status=404)
    has_edit = request.session.get(f'edit_session:{data["note_id"]}', False)
    return render(request, 'sharing/view.html', {'meta': meta, 'content': content, 'token': token, 'has_edit': has_edit})


def create_share(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    today = datetime.utcnow().strftime('%Y%m%d')
    quota = storage.get_quota(ip, today)
    if not settings.DEBUG and (quota['created_count'] + quota['shared_count'] >= 10):
        return JsonResponse({'error': 'daily quota exceeded'}, status=429)

    note_id = request.POST.get('note_id')
    edit_password = request.POST.get('edit_password')
    edit_password_hash = make_password(edit_password) if edit_password else None
    token = storage.create_share(note_id, edit_password_hash)
    if not settings.DEBUG:
        storage.increment_quota(ip, today, 'shared_count')
    return JsonResponse({'token': token})


def edit_share(request: HttpRequest, token: str):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
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
    data = storage.get_share(token)
    if not data or not data.get('active'):
        return HttpResponse('링크가 없거나 만료되었습니다.', status=404)
    note_id = data['note_id']
    has_edit = request.session.get(f'edit_session:{note_id}', False)
    if request.method == 'GET':
        return render(request, 'sharing/change_password.html', { 'token': token, 'has_edit': has_edit })
    # POST
    current = request.POST.get('current_password')
    newpw = request.POST.get('new_password')
    if data.get('edit_password_hash'):
        if not current or not check_password(current, data['edit_password_hash']):
            return render(request, 'sharing/change_password.html', { 'token': token, 'has_edit': has_edit, 'error': '현재 비밀번호가 올바르지 않습니다.' })
    else:
        # no password set, require edit session
        if not has_edit:
            return HttpResponse('권한이 없습니다.', status=403)
    from django.contrib.auth.hashers import make_password
    data['edit_password_hash'] = make_password(newpw) if newpw else None
    storage.write_json(storage.share_path(token), data)
    return render(request, 'sharing/change_password.html', { 'token': token, 'has_edit': has_edit, 'ok': True })
    return JsonResponse({'ok': True})
from django.shortcuts import render

# Create your views here.
