from datetime import datetime

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from core.services import storage
from core.services.diff import html_diff
import bleach
from bleach.css_sanitizer import CSSSanitizer
from PIL import Image, UnidentifiedImageError
from pathlib import Path


def editor(request: HttpRequest):
    return render(request, 'notes/editor.html', {"initial_html": None, "note_id": None})


def save_note(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    client_token = request.COOKIES.get('client_token')
    if not client_token:
        return JsonResponse({'error': 'no client token'}, status=400)

    # IP quota check
    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    today = datetime.utcnow().strftime('%Y%m%d')
    quota = storage.get_quota(ip, today)
    if not settings.DEBUG and (quota['created_count'] + quota['shared_count'] >= 10):
        return JsonResponse({'error': 'daily quota exceeded'}, status=429)

    title = request.POST.get('title', '제목 없음')
    # content_json from client (TipTap document JSON)
    try:
        import json
        content_json = json.loads(request.POST.get('content_json', '{}'))
    except Exception:
        content_json = {}

    # sanitize HTML if provided in our interim format
    if content_json.get('type') == 'html':
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

    # Support create or update
    existing_note_id = request.POST.get('note_id')
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
    note_id = storage.create_note(title, client_token, ip, content_json)
    storage.increment_quota(ip, today, 'created_count')
    return JsonResponse({'note_id': note_id})


def upload_image(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    client_token = request.COOKIES.get('client_token')
    if not client_token:
        return JsonResponse({'error': 'no client token'}, status=400)
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'no file'}, status=400)
    if file.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'max 10MB'}, status=413)
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
    return JsonResponse({'url': url})
from django.shortcuts import render

# Create your views here.

def get_note_content(request: HttpRequest, note_id: str):
    meta, content = storage.get_note(note_id)
    if not meta:
        return JsonResponse({'error': 'not found'}, status=404)
    return JsonResponse({'note_id': note_id, 'content': content or {} })
