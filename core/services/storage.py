import json
import os
import uuid
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.conf import settings


class FileLock:
    _locks = {}
    _global = threading.Lock()

    def __init__(self, path: Path):
        self.path = path
        with FileLock._global:
            FileLock._locks.setdefault(str(path), threading.Lock())
        self._lock = FileLock._locks[str(path)]

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._lock.release()


def _ensure_dirs(*paths: Path):
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


BASE = Path(settings.DATA_ROOT)
_ensure_dirs(BASE, BASE / "notes", BASE / "history", BASE / "shares", BASE / "quota", BASE / "admin_logs", BASE / "index")


def generate_note_id() -> str:
    return uuid.uuid4().hex  # 32 hex; later can switch to base62


def generate_share_token() -> str:
    # 10-char Base62 like: using uuid and slicing; collision check must be external
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    n = uuid.uuid4().int
    token = ""
    for _ in range(10):
        token += alphabet[n % 62]
        n //= 62
    return token


def note_paths(note_id: str):
    note_dir = BASE / "notes" / note_id
    return {
        "dir": note_dir,
        "meta": note_dir / "meta.json",
        "content": note_dir / "content.json",
        "attachments": note_dir / "attachments",
    }


def share_path(token: str) -> Path:
    return BASE / "shares" / f"{token}.json"


def history_path(history_id: str) -> Path:
    return BASE / "history" / f"{history_id}.json"


def quota_path(date_str: str, ip: str) -> Path:
    d = BASE / "quota" / date_str
    _ensure_dirs(d)
    return d / f"{ip}.json"


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_note(title: str, creator_client_token: str, creator_ip: str, content_json: dict) -> str:
    note_id = generate_note_id()
    paths = note_paths(note_id)
    _ensure_dirs(paths["dir"], paths["attachments"])
    write_json(paths["content"], content_json)
    meta = {
        "note_id": note_id,
        "title": title,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "creator_client_token": creator_client_token,
        "creator_ip": creator_ip,
        "status": "active",
        "history_ids": [],
        "edit_password_hash": None,
    }
    write_json(paths["meta"], meta)
    return note_id


def save_note_content(note_id: str, content_json: dict):
    paths = note_paths(note_id)
    write_json(paths["content"], content_json)
    meta = read_json(paths["meta"]) or {}
    meta["updated_at"] = _now_iso()
    write_json(paths["meta"], meta)


def get_note(note_id: str) -> tuple[dict | None, dict | None]:
    paths = note_paths(note_id)
    return read_json(paths["meta"]), read_json(paths["content"])


def add_history(note_id: str, before_html: str, after_html: str, diff_html: str, editor_session_id: str) -> str:
    history_id = uuid.uuid4().hex
    write_json(history_path(history_id), {
        "note_id": note_id,
        "timestamp": _now_iso(),
        "before_html": before_html,
        "after_html": after_html,
        "diff_html": diff_html,
        "editor_session_id": editor_session_id,
    })
    paths = note_paths(note_id)
    meta = read_json(paths["meta"]) or {}
    meta.setdefault("history_ids", []).append(history_id)
    write_json(paths["meta"], meta)
    return history_id


def create_share(note_id: str, edit_password_hash: str | None) -> str:
    # Ensure unique token
    for _ in range(20):
        token = generate_share_token()
        if not share_path(token).exists():
            break
    else:
        raise RuntimeError("Failed to generate unique share token")
    created = datetime.now(timezone.utc)
    expires = created + timedelta(days=180)
    write_json(share_path(token), {
        "note_id": note_id,
        "token": token,
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "active": True,
        "edit_password_hash": edit_password_hash,
    })
    return token


def get_share(token: str) -> dict | None:
    data = read_json(share_path(token))
    if not data:
        return None
    # Auto-expire check
    try:
        exp = datetime.fromisoformat(data.get("expires_at"))
        if exp < datetime.now(timezone.utc):
            data["active"] = False
    except Exception:
        pass
    return data


def set_share_active(token: str, active: bool):
    data = read_json(share_path(token)) or {}
    data["active"] = active
    write_json(share_path(token), data)


def increment_quota(ip: str, date_str: str, key: str) -> dict:
    path = quota_path(date_str, ip)
    data = read_json(path) or {"created_count": 0, "shared_count": 0}
    if key not in data:
        data[key] = 0
    data[key] += 1
    write_json(path, data)
    return data


def get_quota(ip: str, date_str: str) -> dict:
    return read_json(quota_path(date_str, ip)) or {"created_count": 0, "shared_count": 0}


def write_admin_log(message: str):
    today = datetime.now(timezone.utc).date().isoformat()
    path = BASE / "admin_logs" / f"{today}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(path):
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{_now_iso()}] {message}\n")
