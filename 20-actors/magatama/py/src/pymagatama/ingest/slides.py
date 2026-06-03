"""Google Slides ingest Zeebe worker — Drive changes filter + presentations.get."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

SLIDES_TOKEN_TABLE = "vertex_gslides_oauth_token"
SLIDES_PRESENTATION_TABLE = "vertex_gslides_presentation"
SLIDES_SLIDE_TABLE = "vertex_gslides_slide"
ACTOR_DID = "did:web:slides.etzhayyim.com"
GSLIDES_MIME = "application/vnd.google-apps.presentation"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _str(v: Any) -> str:
    return "" if v is None else str(v)


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _fetch_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _http_json(url: str, *, method: str = "GET", body: bytes | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(url, method=method, data=body, headers={"accept": "application/json", "user-agent": "etzhayyim-slides-zeebe/1", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _insert(table: str, row: dict[str, Any]) -> None:
    cols = list(row.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    _execute(
        f"INSERT INTO {table} ({', '.join(cols)}) SELECT {placeholders} WHERE NOT EXISTS (SELECT 1 FROM {table} WHERE vertex_id = %s)",
        tuple(row[c] for c in cols) + (_str(row["vertex_id"]),),
    )


def _refresh_access_token(refresh_token: str) -> str:
    client_id = os.environ.get("SS_GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("SS_GOOGLE_OAUTH_CLIENT_SECRET", "")
    body = urllib.parse.urlencode({"refresh_token": refresh_token, "client_id": client_id, "client_secret": client_secret, "grant_type": "refresh_token"}).encode()
    data = _http_json("https://oauth2.googleapis.com/token", method="POST", headers={"content-type": "application/x-www-form-urlencoded"}, body=body)
    return _str(data.get("access_token"))


def _get_start_page_token(access: str) -> str:
    data = _http_json("https://www.googleapis.com/drive/v3/changes/startPageToken", headers={"authorization": f"Bearer {access}"})
    return _str(data.get("startPageToken"))


def _extract_slide_text(elements: list[dict[str, Any]]) -> str:
    """Extract plain text from page elements for notes/preview."""
    parts: list[str] = []
    for el in elements:
        shape = el.get("shape") or {}
        text_content = shape.get("text") or {}
        for te in text_content.get("textElements") or []:
            tr = te.get("textRun") or {}
            if tr.get("content"):
                parts.append(_str(tr["content"]))
    return "".join(parts)[:1000]


def _presentation_row(token: dict[str, Any], pres: dict[str, Any], file_id: str, modified_time: str) -> dict[str, Any]:
    presentation_id = _str(pres.get("presentationId"))
    actor = ACTOR_DID
    now = now_iso()
    slides = pres.get("slides") or []
    masters = pres.get("masters") or []
    layouts = pres.get("layouts") or []
    page_size = pres.get("pageSize") or {}
    width_emu = int((page_size.get("width") or {}).get("magnitude") or 0)
    height_emu = int((page_size.get("height") or {}).get("magnitude") or 0)
    return {
        "vertex_id": f"at://{actor}/com.etzhayyim.apps.slides.presentation/{presentation_id}",
        "_seq": int(time.time() * 1000),
        "created_date": now[:10],
        "sensitivity_ord": 100,
        "owner_did": actor,
        "rkey": presentation_id,
        "repo": actor,
        "presentation_id": presentation_id,
        "account_did": _str(token.get("account_did")),
        "file_id": file_id,
        "title": _str(pres.get("title")),
        "locale": _str(pres.get("locale")),
        "revision_id": _str(pres.get("revisionId")),
        "slide_count": len(slides),
        "master_count": len(masters),
        "layout_count": len(layouts),
        "page_width_emu": width_emu,
        "page_height_emu": height_emu,
        "notes_master_json": json.dumps(pres.get("notesMaster") or {}, ensure_ascii=False)[:2000],
        "updated_time": modified_time,
        "created_at": now,
        "org_id": "anon",
        "user_id": _str(token.get("account_did")),
        "actor_id": "slides-mcp",
    }


def _slide_row(token: dict[str, Any], presentation_id: str, slide: dict[str, Any], slide_index: int) -> dict[str, Any]:
    slide_object_id = _str(slide.get("objectId"))
    actor = ACTOR_DID
    now = now_iso()
    elements = slide.get("pageElements") or []
    notes_page = slide.get("slideProperties", {}).get("notesPage") or {}
    notes_elements = notes_page.get("pageElements") or []
    notes_text = _extract_slide_text(notes_elements)
    elements_preview = _extract_slide_text(elements)
    page_properties = slide.get("pageProperties") or {}
    return {
        "vertex_id": f"at://{actor}/com.etzhayyim.apps.slides.slide/{presentation_id}_{slide_object_id}",
        "_seq": int(time.time() * 1000),
        "created_date": now[:10],
        "sensitivity_ord": 100,
        "owner_did": actor,
        "rkey": f"{presentation_id}_{slide_object_id}",
        "repo": actor,
        "slide_object_id": slide_object_id,
        "presentation_id": presentation_id,
        "account_did": _str(token.get("account_did")),
        "slide_index": slide_index,
        "layout_object_id": _str((slide.get("slideProperties") or {}).get("layoutObjectId")),
        "master_object_id": _str((slide.get("slideProperties") or {}).get("masterObjectId")),
        "notes_text": notes_text,
        "page_elements_json": json.dumps(elements, ensure_ascii=False)[:8000],
        "page_elements_preview": elements_preview,
        "element_count": len(elements),
        "page_properties_json": json.dumps(page_properties, ensure_ascii=False),
        "updated_time": now,
        "created_at": now,
        "org_id": "anon",
        "user_id": _str(token.get("account_did")),
        "actor_id": "slides-mcp",
    }


def _sync_token(token: dict[str, Any]) -> dict[str, Any]:
    access = _refresh_access_token(_str(token.get("encrypted_refresh_token")))
    if not access:
        return {"ok": False, "error": "access token refresh failed"}

    page_token = _str(token.get("cursor"))
    if not page_token:
        page_token = _get_start_page_token(access)

    synced = 0
    new_cursor = page_token

    while page_token:
        fields = "newStartPageToken,nextPageToken,changes(type,removed,fileId,file(id,mimeType,name,modifiedTime))"
        qs = urllib.parse.urlencode({"pageToken": page_token, "fields": fields, "pageSize": "1000", "includeItemsFromAllDrives": "true", "supportsAllDrives": "true"})
        data = _http_json(f"https://www.googleapis.com/drive/v3/changes?{qs}", headers={"authorization": f"Bearer {access}"})

        for change in data.get("changes") or []:
            if change.get("type") != "file":
                continue
            f = change.get("file") or {}
            file_id = _str(f.get("id") or change.get("fileId"))
            if not file_id:
                continue
            if f.get("mimeType") != GSLIDES_MIME:
                continue
            if change.get("removed"):
                _execute(f"DELETE FROM {SLIDES_PRESENTATION_TABLE} WHERE file_id = %s AND account_did = %s", (file_id, _str(token.get("account_did"))))
            else:
                try:
                    pres = _http_json(
                        f"https://slides.googleapis.com/v1/presentations/{file_id}",
                        headers={"authorization": f"Bearer {access}"},
                    )
                    _insert(SLIDES_PRESENTATION_TABLE, _presentation_row(token, pres, file_id, _str(f.get("modifiedTime"))))
                    for idx, slide in enumerate(pres.get("slides") or []):
                        _insert(SLIDES_SLIDE_TABLE, _slide_row(token, _str(pres.get("presentationId")), slide, idx))
                    synced += 1
                except Exception:
                    pass  # permission denied or transient — skip

        new_cursor = _str(data.get("newStartPageToken") or data.get("nextPageToken") or page_token)
        page_token = _str(data.get("nextPageToken"))

    _execute(
        f"UPDATE {SLIDES_TOKEN_TABLE} SET last_sync_at = %s, cursor = %s, updated_at = %s WHERE vertex_id = %s",
        (now_iso(), new_cursor, now_iso(), _str(token.get("vertex_id"))),
    )
    return {"ok": True, "synced": synced, "cursor": new_cursor}


def sync_from_google(email: str = "", **_: Any) -> dict[str, Any]:
    if not email:
        return {"ok": False, "error": "email required"}
    token = _fetch_one(f"SELECT * FROM {SLIDES_TOKEN_TABLE} WHERE email = %s AND status = 'active' LIMIT 1", (email,))
    if not token:
        return {"ok": False, "error": "No active Slides account. connectAccount first."}
    return _sync_token(token)


def cron_tick(**_: Any) -> dict[str, Any]:
    rows = _fetch_all(f"SELECT * FROM {SLIDES_TOKEN_TABLE} WHERE status = 'active' ORDER BY COALESCE(last_sync_at, created_at) ASC LIMIT 10")
    synced = 0
    errors = 0
    for token in rows:
        result = _sync_token(token)
        synced += int(result.get("synced") or 0)
        errors += 0 if result.get("ok") else 1
    return {"ok": errors == 0, "accounts": len(rows), "synced": synced, "errors": errors}
