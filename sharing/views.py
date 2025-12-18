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
    # Ensure iframe attributes needed by browsers / YouTube are present
    if content and isinstance(content, dict) and content.get('type') == 'html':
        try:
            import re
            html = content.get('html','') or ''
            def _fix_iframe(m):
                tag = m.group(0)
                # ensure allow attribute
                if 'allow=' not in tag:
                    tag = tag.replace('<iframe', '<iframe allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"')
                # ensure loading attribute
                if 'loading=' not in tag:
                    tag = tag.replace('<iframe', '<iframe loading="lazy"')
                # ensure referrerpolicy
                if 'referrerpolicy=' not in tag:
                    tag = tag.replace('<iframe', '<iframe referrerpolicy="no-referrer-when-downgrade"')
                # ensure allowfullscreen
                if 'allowfullscreen' not in tag:
                    tag = tag.replace('<iframe', '<iframe allowfullscreen')
                return tag
            html = re.sub(r'<iframe[^>]*>', _fix_iframe, html, flags=re.I)
            # Ensure youtube.com/embed -> youtube-nocookie.com/embed and add rel=0
            try:
                def _normalize_src(m):
                    src = m.group(1) or ''
                    if 'youtube.com/embed' in src and 'youtube-nocookie.com' not in src:
                        src = src.replace('youtube.com/embed', 'youtube-nocookie.com/embed')
                    # add rel=0 unless already present
                    if '?' in src:
                        if 'rel=' not in src:
                            src = src + '&rel=0'
                    else:
                        src = src + '?rel=0'
                    # add origin parameter for YouTube to validate origin
                    try:
                        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                        p = urlparse(src)
                        qs = parse_qs(p.query)
                        if 'origin' not in qs:
                            origin = request.scheme + '://' + request.get_host()
                            # append origin to query params
                            if p.query:
                                src = src + '&origin=' + origin
                            else:
                                src = src + ('&' if '?' in src else '?') + 'origin=' + origin
                    except Exception:
                        pass
                    return f'src="{src}"'
                html = re.sub(r'src=["\']([^"\']+)["\']', _normalize_src, html, flags=re.I)
            except Exception:
                pass
            # Replace iframe tags with deferred placeholders to create iframes
            try:
                import html as _html
                def _replace_iframe_with_placeholder(m):
                    tag = m.group(0)
                    # extract src/width/height
                    src_m = re.search(r'src=["\']([^"\']+)["\']', tag, flags=re.I)
                    w_m = re.search(r'width=["\']([^"\']+)["\']', tag, flags=re.I)
                    h_m = re.search(r'height=["\']([^"\']+)["\']', tag, flags=re.I)
                    src = src_m.group(1) if src_m else ''
                    w = w_m.group(1) if w_m else '640'
                    h = h_m.group(1) if h_m else '480'
                    # escape attributes
                    esc_src = _html.escape(src, quote=True)
                    esc_w = _html.escape(w, quote=True)
                    esc_h = _html.escape(h, quote=True)
                    return f'<div class="deferred-iframe" data-src="{esc_src}" data-width="{esc_w}" data-height="{esc_h}"></div>'
                html = re.sub(r'<iframe[^>]*>.*?</iframe>', _replace_iframe_with_placeholder, html, flags=re.I|re.S)
            except Exception:
                pass
            content = dict(content)
            content['html'] = html
        except Exception:
            pass
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
