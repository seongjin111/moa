from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
import bleach
from bleach.css_sanitizer import CSSSanitizer
from django.contrib.auth.decorators import login_required

from core.services import storage


def _can_view_note_history(request: HttpRequest, note_meta: dict) -> bool:
    if request.user.is_authenticated and request.user.is_staff:
        return True
    client_token = request.COOKIES.get('client_token')
    if client_token and client_token == note_meta.get('creator_client_token'):
        return True
    if request.session.get(f"edit_session:{note_meta['note_id']}", False):
        return True
    return False


def history_list(request: HttpRequest, note_id: str):
    meta, _ = storage.get_note(note_id)
    if not meta:
        return HttpResponse('없거나 삭제된 노트입니다.', status=404)
    if not _can_view_note_history(request, meta):
        return HttpResponse('권한이 없습니다.', status=403)

    items = []
    for hid in reversed(meta.get('history_ids', [])):
        h = storage.read_json(storage.history_path(hid)) or {}
        if h:
            h['id'] = hid
            items.append(h)
    return render(request, 'notes/history_list.html', {
        'note': meta,
        'items': items,
    })


def history_detail(request: HttpRequest, note_id: str, history_id: str):
    meta, _ = storage.get_note(note_id)
    if not meta:
        return HttpResponse('없거나 삭제된 노트입니다.', status=404)
    if not _can_view_note_history(request, meta):
        return HttpResponse('권한이 없습니다.', status=403)

    hist = storage.read_json(storage.history_path(history_id))
    if not hist or hist.get('note_id') != note_id:
        return HttpResponse('히스토리를 찾을 수 없습니다.', status=404)

    hist['id'] = history_id
    return render(request, 'notes/history_detail.html', {
        'note': meta,
        'hist': hist,
    })


def history_restore(request: HttpRequest, note_id: str, history_id: str):
    if request.method != 'POST':
        return HttpResponse('POST required', status=405)
    meta, _ = storage.get_note(note_id)
    if not meta:
        return HttpResponse('없거나 삭제된 노트입니다.', status=404)
    if not _can_view_note_history(request, meta):
        return HttpResponse('권한이 없습니다.', status=403)

    hist = storage.read_json(storage.history_path(history_id))
    if not hist or hist.get('note_id') != note_id:
        return HttpResponse('히스토리를 찾을 수 없습니다.', status=404)

    # Sanitize restored HTML (allow color/bg/text-align)
    allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
        'p','br','b','i','u','strong','em','ul','ol','li','h1','h2','h3','h4','h5','h6','blockquote','code','pre','img','a','span','div','ins','del','hr'
    })
    allowed_attrs = {**bleach.sanitizer.ALLOWED_ATTRIBUTES,
                     'a': ['href','title','target','rel'],
                     'img': ['src','alt','title'],
                     'span': ['style'],
                     'p': ['style'], 'div': ['style'],
                     'h1': ['style'],'h2': ['style'],'h3': ['style'],'h4': ['style'],'h5': ['style'],'h6': ['style']}
    cleaner = bleach.Cleaner(tags=list(allowed_tags), attributes=allowed_attrs,
                             css_sanitizer=CSSSanitizer(allowed_css_properties=['color','background-color','text-align']), strip=True)
    restored_html = cleaner.clean(hist.get('after_html',''))

    # Current content before overwrite
    _, current = storage.get_note(note_id)
    before_html = ''
    if current and current.get('type') == 'html':
        before_html = current.get('html','')

    # Write content and record new history
    storage.save_note_content(note_id, { 'type': 'html', 'html': restored_html })
    from core.services.diff import html_diff
    diff_html = html_diff(before_html, restored_html)
    storage.add_history(note_id, before_html, restored_html, diff_html, request.session.session_key or 'session')

    return redirect(f'/edit/{note_id}/')
