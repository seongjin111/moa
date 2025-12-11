from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from core.services import storage


def edit_page(request: HttpRequest, note_id: str):
    meta, content = storage.get_note(note_id)
    if not meta:
        return HttpResponse('없거나 삭제된 노트입니다.', status=404)
    if meta.get('status') in ('expired','deleted'):
        return HttpResponse('없거나 삭제된 노트입니다.', status=404)

    # Permission: owner via client_token, or share-edit session
    client_token = request.COOKIES.get('client_token')
    has_session = request.session.get(f'edit_session:{note_id}', False)
    if not (has_session or (client_token and client_token == meta.get('creator_client_token'))):
        return HttpResponse('편집 권한이 없습니다.', status=403)

    initial_html = ''
    if content and content.get('type') == 'html':
        initial_html = content.get('html', '')
    return render(request, 'notes/editor.html', {
        'initial_html': initial_html,
        'note_id': note_id,
        'title': meta.get('title',''),
    })
