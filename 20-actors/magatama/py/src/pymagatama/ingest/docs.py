"""Google Docs ingest Zeebe worker — Drive changes filter + documents.get."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

DOCS_TOKEN_TABLE = "vertex_gdocs_oauth_token"
DOCS_DOCUMENT_TABLE = "vertex_gdocs_document"
ACTOR_DID = "did:web:docs.etzhayyim.com"
GDOCS_MIME = "application/vnd.google-apps.document"


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
    req = urllib.request.Request(url, method=method, data=body, headers={"accept": "application/json", "user-agent": "etzhayyim-docs-zeebe/1", **(headers or {})})
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


def _extract_text(body: dict) -> tuple[str, int, int, int]:
    """Extract plain text preview and word/char/page counts from a document body."""
    content = body.get("content") or []
    text_parts: list[str] = []
    for elem in content:
        paragraph = elem.get("paragraph")
        if paragraph:
            for pe in paragraph.get("elements") or []:
                tr = pe.get("textRun")
                if tr:
                    text_parts.append(_str(tr.get("content")))
        section = elem.get("sectionBreak")
        if section:
            text_parts.append("\n")
    full_text = "".join(text_parts)
    preview = full_text[:2000]
    words = len(full_text.split())
    chars = len(full_text)
    pages = max(1, chars // 2000)
    return preview, words, chars, pages


def _doc_row(token: dict[str, Any], doc: dict[str, Any], file_id: str, modified_time: str) -> dict[str, Any]:
    document_id = _str(doc.get("documentId"))
    actor = ACTOR_DID
    now = now_iso()
    body = doc.get("body") or {}
    body_preview, word_count, char_count, page_count = _extract_text(body)
    return {
        "vertex_id": f"at://{actor}/com.etzhayyim.apps.docs.document/{document_id}",
        "_seq": int(time.time() * 1000),
        "created_date": now[:10],
        "sensitivity_ord": 100,
        "owner_did": actor,
        "rkey": document_id,
        "repo": actor,
        "document_id": document_id,
        "account_did": _str(token.get("account_did")),
        "file_id": file_id,
        "title": _str(doc.get("title")),
        "body_preview": body_preview,
        "body_content_json": json.dumps(body.get("content") or [], ensure_ascii=False)[:8000],
        "revision_id": _str(doc.get("revisionId")),
        "suggestions_view_mode": _str(doc.get("suggestionsViewMode")),
        "named_ranges_json": json.dumps(doc.get("namedRanges") or {}, ensure_ascii=False),
        "inline_objects_json": json.dumps(doc.get("inlineObjects") or {}, ensure_ascii=False)[:4000],
        "positioned_objects_json": json.dumps(doc.get("positionedObjects") or {}, ensure_ascii=False)[:4000],
        "lists_json": json.dumps(doc.get("lists") or {}, ensure_ascii=False),
        "headers_json": json.dumps(doc.get("headers") or {}, ensure_ascii=False),
        "footers_json": json.dumps(doc.get("footers") or {}, ensure_ascii=False),
        "footnotes_json": json.dumps(doc.get("footnotes") or {}, ensure_ascii=False),
        "doc_style_json": json.dumps(doc.get("documentStyle") or {}, ensure_ascii=False),
        "word_count": word_count,
        "char_count": char_count,
        "page_count": page_count,
        "updated_time": modified_time,
        "created_at": now,
        "org_id": "anon",
        "user_id": _str(token.get("account_did")),
        "actor_id": "docs-mcp",
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
            if f.get("mimeType") != GDOCS_MIME:
                continue
            if change.get("removed"):
                _execute(f"DELETE FROM {DOCS_DOCUMENT_TABLE} WHERE file_id = %s AND account_did = %s", (file_id, _str(token.get("account_did"))))
            else:
                try:
                    doc = _http_json(f"https://docs.googleapis.com/v1/documents/{file_id}", headers={"authorization": f"Bearer {access}"})
                    _insert(DOCS_DOCUMENT_TABLE, _doc_row(token, doc, file_id, _str(f.get("modifiedTime"))))
                    synced += 1
                except Exception:
                    pass  # permission denied or transient — skip

        new_cursor = _str(data.get("newStartPageToken") or data.get("nextPageToken") or page_token)
        page_token = _str(data.get("nextPageToken"))

    _execute(
        f"UPDATE {DOCS_TOKEN_TABLE} SET last_sync_at = %s, cursor = %s, updated_at = %s WHERE vertex_id = %s",
        (now_iso(), new_cursor, now_iso(), _str(token.get("vertex_id"))),
    )
    return {"ok": True, "synced": synced, "cursor": new_cursor}


def sync_from_google(email: str = "", **_: Any) -> dict[str, Any]:
    if not email:
        return {"ok": False, "error": "email required"}
    token = _fetch_one(f"SELECT * FROM {DOCS_TOKEN_TABLE} WHERE email = %s AND status = 'active' LIMIT 1", (email,))
    if not token:
        return {"ok": False, "error": "No active Docs account. connectAccount first."}
    return _sync_token(token)


def cron_tick(**_: Any) -> dict[str, Any]:
    rows = _fetch_all(f"SELECT * FROM {DOCS_TOKEN_TABLE} WHERE status = 'active' ORDER BY COALESCE(last_sync_at, created_at) ASC LIMIT 10")
    synced = 0
    errors = 0
    for token in rows:
        result = _sync_token(token)
        synced += int(result.get("synced") or 0)
        errors += 0 if result.get("ok") else 1
    return {"ok": errors == 0, "accounts": len(rows), "synced": synced, "errors": errors}
