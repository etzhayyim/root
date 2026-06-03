"""Google Drive ingest Zeebe worker — changes.list cursor-based sync."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

DRIVE_TOKEN_TABLE = "vertex_gdrive_oauth_token"
DRIVE_FILE_TABLE = "vertex_gdrive_file"
ACTOR_DID = "did:web:drive.etzhayyim.com"


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
    req = urllib.request.Request(url, method=method, data=body, headers={"accept": "application/json", "user-agent": "etzhayyim-drive-zeebe/1", **(headers or {})})
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


def _file_row(token: dict[str, Any], f: dict[str, Any]) -> dict[str, Any]:
    file_id = _str(f.get("id"))
    actor = ACTOR_DID
    now = now_iso()
    return {
        "vertex_id": f"at://{actor}/com.etzhayyim.apps.drive.file/{file_id}",
        "_seq": int(time.time() * 1000),
        "created_date": now[:10],
        "sensitivity_ord": 100,
        "owner_did": actor,
        "rkey": file_id,
        "repo": actor,
        "file_id": file_id,
        "account_did": _str(token.get("account_did")),
        "name": _str(f.get("name")),
        "mime_type": _str(f.get("mimeType")),
        "kind": _str(f.get("kind")),
        "size_bytes": int(f.get("size") or 0),
        "md5_checksum": _str(f.get("md5Checksum")),
        "sha256_checksum": _str(f.get("sha256Checksum")),
        "description": _str(f.get("description")),
        "starred": "true" if f.get("starred") else "false",
        "trashed": "true" if f.get("trashed") else "false",
        "explicitly_trashed": "true" if f.get("explicitlyTrashed") else "false",
        "shared": "true" if f.get("shared") else "false",
        "owners_json": json.dumps(f.get("owners") or [], ensure_ascii=False),
        "parents_json": json.dumps(f.get("parents") or [], ensure_ascii=False),
        "spaces_json": json.dumps(f.get("spaces") or [], ensure_ascii=False),
        "web_view_link": _str(f.get("webViewLink")),
        "web_content_link": _str(f.get("webContentLink")),
        "icon_link": _str(f.get("iconLink")),
        "thumbnail_link": _str(f.get("thumbnailLink")),
        "original_filename": _str(f.get("originalFilename")),
        "file_extension": _str(f.get("fileExtension")),
        "full_file_extension": _str(f.get("fullFileExtension")),
        "head_revision_id": _str(f.get("headRevisionId")),
        "version_num": int(f.get("version") or 0),
        "view_count": int((f.get("fileViewerAccess") or {}).get("viewCount") or 0),
        "capabilities_json": json.dumps(f.get("capabilities") or {}, ensure_ascii=False),
        "export_links_json": json.dumps(f.get("exportLinks") or {}, ensure_ascii=False),
        "drive_id": _str(f.get("driveId")),
        "team_drive_id": _str(f.get("teamDriveId")),
        "created_time": _str(f.get("createdTime")),
        "modified_time": _str(f.get("modifiedTime")),
        "viewed_by_me_time": _str(f.get("viewedByMeTime")),
        "shared_with_me_time": _str(f.get("sharedWithMeTime")),
        "created_at": now,
        "org_id": "anon",
        "user_id": _str(token.get("account_did")),
        "actor_id": "drive-mcp",
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
        fields = "newStartPageToken,nextPageToken,changes(type,removed,fileId,file(id,name,mimeType,kind,size,md5Checksum,sha256Checksum,description,starred,trashed,explicitlyTrashed,shared,owners,parents,spaces,webViewLink,webContentLink,iconLink,thumbnailLink,originalFilename,fileExtension,fullFileExtension,headRevisionId,version,capabilities,exportLinks,driveId,teamDriveId,createdTime,modifiedTime,viewedByMeTime,sharedWithMeTime))"
        qs = urllib.parse.urlencode({"pageToken": page_token, "fields": fields, "pageSize": "1000", "includeItemsFromAllDrives": "true", "supportsAllDrives": "true"})
        data = _http_json(f"https://www.googleapis.com/drive/v3/changes?{qs}", headers={"authorization": f"Bearer {access}"})

        for change in data.get("changes", []):
            if change.get("type") != "file":
                continue
            f = change.get("file")
            if not f or not f.get("id"):
                continue
            if change.get("removed"):
                _execute(f"DELETE FROM {DRIVE_FILE_TABLE} WHERE file_id = %s AND account_did = %s", (f.get("id"), _str(token.get("account_did"))))
            else:
                _insert(DRIVE_FILE_TABLE, _file_row(token, f))
            synced += 1

        new_cursor = _str(data.get("newStartPageToken") or data.get("nextPageToken") or page_token)
        page_token = _str(data.get("nextPageToken"))

    _execute(
        f"UPDATE {DRIVE_TOKEN_TABLE} SET last_sync_at = %s, cursor = %s, updated_at = %s WHERE vertex_id = %s",
        (now_iso(), new_cursor, now_iso(), _str(token.get("vertex_id"))),
    )
    return {"ok": True, "synced": synced, "cursor": new_cursor}


def sync_from_google(email: str = "", **_: Any) -> dict[str, Any]:
    if not email:
        return {"ok": False, "error": "email required"}
    token = _fetch_one(f"SELECT * FROM {DRIVE_TOKEN_TABLE} WHERE email = %s AND status = 'active' LIMIT 1", (email,))
    if not token:
        return {"ok": False, "error": "No active Drive account. connectAccount first."}
    return _sync_token(token)


def cron_tick(**_: Any) -> dict[str, Any]:
    rows = _fetch_all(f"SELECT * FROM {DRIVE_TOKEN_TABLE} WHERE status = 'active' ORDER BY COALESCE(last_sync_at, created_at) ASC LIMIT 10")
    synced = 0
    errors = 0
    for token in rows:
        result = _sync_token(token)
        synced += int(result.get("synced") or 0)
        errors += 0 if result.get("ok") else 1
    return {"ok": errors == 0, "accounts": len(rows), "synced": synced, "errors": errors}
