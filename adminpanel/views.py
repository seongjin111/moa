from pathlib import Path
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.services import storage
from django.conf import settings
import json


@login_required
def dashboard(request: HttpRequest):
    return render(request, 'adminpanel/dashboard.html', {})


@login_required
def notes_list(request: HttpRequest):
    base = Path(settings.DATA_ROOT) / 'notes'
    rows = []
    if base.exists():
        for note_dir in base.iterdir():
            meta = storage.read_json(note_dir / 'meta.json') or {}
            rows.append(meta)
    rows.sort(key=lambda x: x.get('created_at',''), reverse=True)
    return render(request, 'adminpanel/notes_list.html', { 'rows': rows })


@login_required
def note_expire(request: HttpRequest, note_id: str):
    meta, _ = storage.get_note(note_id)
    if not meta:
        return HttpResponse('not found', status=404)
    meta['status'] = 'expired'
    paths = storage.note_paths(note_id)
    storage.write_json(paths['meta'], meta)
    storage.write_admin_log(f"expire note {note_id} by {request.user.username}")
    return redirect('admin_notes_list')


@login_required
def note_delete(request: HttpRequest, note_id: str):
    meta, _ = storage.get_note(note_id)
    if not meta:
        return HttpResponse('not found', status=404)
    # physical delete
    paths = storage.note_paths(note_id)
    try:
        import shutil
        shutil.rmtree(paths['dir'], ignore_errors=True)
        storage.write_admin_log(f"physically deleted note {note_id} by {request.user.username}")
    except Exception as e:
        storage.write_admin_log(f"delete note failed {note_id}: {e}")
    return redirect('admin_notes_list')

@login_required
def note_history_list(request: HttpRequest, note_id: str):
    meta, _ = storage.get_note(note_id)
    if not meta:
        return HttpResponse('not found', status=404)
    ids = (meta.get('history_ids') or [])
    histories = []
    for hid in reversed(ids):  # newest first
        h = storage.read_json(storage.history_path(hid)) or {}
        if h:
            h['history_id'] = hid
            histories.append(h)
    return render(request, 'adminpanel/note_history_list.html', {
        'note': meta,
        'histories': histories,
    })
