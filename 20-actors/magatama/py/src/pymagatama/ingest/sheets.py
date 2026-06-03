"""Google Sheets ingest Zeebe worker — Drive changes filter + spreadsheets.get."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

SHEETS_TOKEN_TABLE = "vertex_gsheets_oauth_token"
SHEETS_SPREADSHEET_TABLE = "vertex_gsheets_spreadsheet"
SHEETS_SHEET_TABLE = "vertex_gsheets_sheet"
ACTOR_DID = "did:web:sheets.etzhayyim.com"
GSHEETS_MIME = "application/vnd.google-apps.spreadsheet"


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
    req = urllib.request.Request(url, method=method, data=body, headers={"accept": "application/json", "user-agent": "etzhayyim-sheets-zeebe/1", **(headers or {})})
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


def _spreadsheet_row(token: dict[str, Any], ss: dict[str, Any], file_id: str, modified_time: str) -> dict[str, Any]:
    spreadsheet_id = _str(ss.get("spreadsheetId"))
    actor = ACTOR_DID
    now = now_iso()
    props = ss.get("properties") or {}
    sheets = ss.get("sheets") or []
    named_ranges = ss.get("namedRanges") or []
    developer_metadata = ss.get("developerMetadata") or []
    return {
        "vertex_id": f"at://{actor}/com.etzhayyim.apps.sheets.spreadsheet/{spreadsheet_id}",
        "_seq": int(time.time() * 1000),
        "created_date": now[:10],
        "sensitivity_ord": 100,
        "owner_did": actor,
        "rkey": spreadsheet_id,
        "repo": actor,
        "spreadsheet_id": spreadsheet_id,
        "account_did": _str(token.get("account_did")),
        "file_id": file_id,
        "title": _str(props.get("title")),
        "locale": _str(props.get("locale")),
        "time_zone": _str(props.get("timeZone")),
        "auto_recalc": _str(props.get("autoRecalc")),
        "sheet_count": len(sheets),
        "named_ranges_json": json.dumps(named_ranges, ensure_ascii=False),
        "developer_metadata_json": json.dumps(developer_metadata, ensure_ascii=False),
        "spreadsheet_url": _str(ss.get("spreadsheetUrl")),
        "updated_time": modified_time,
        "created_at": now,
        "org_id": "anon",
        "user_id": _str(token.get("account_did")),
        "actor_id": "sheets-mcp",
    }


def _sheet_row(token: dict[str, Any], spreadsheet_id: str, sheet: dict[str, Any]) -> dict[str, Any]:
    props = sheet.get("properties") or {}
    grid_props = props.get("gridProperties") or {}
    sheet_id = _str(props.get("sheetId"))
    actor = ACTOR_DID
    now = now_iso()

    # Extract grid data preview (values from first sheet data range)
    data_list = sheet.get("data") or []
    grid_values: list[list[Any]] = []
    for d in data_list[:1]:
        for row_data in (d.get("rowData") or [])[:20]:
            row_vals = [_str((c.get("formattedValue") or "")) for c in (row_data.get("values") or [])]
            grid_values.append(row_vals)
    grid_preview = json.dumps(grid_values[:5], ensure_ascii=False)[:2000]

    charts = sheet.get("charts") or []
    protected = sheet.get("protectedRanges") or []

    # Estimate cell count and data bytes from row/col counts
    row_count = int(grid_props.get("rowCount") or 0)
    col_count = int(grid_props.get("columnCount") or 0)
    cell_count = row_count * col_count if row_count and col_count else 0
    data_bytes = len(json.dumps(grid_values, ensure_ascii=False).encode())

    return {
        "vertex_id": f"at://{actor}/com.etzhayyim.apps.sheets.sheet/{spreadsheet_id}_{sheet_id}",
        "_seq": int(time.time() * 1000),
        "created_date": now[:10],
        "sensitivity_ord": 100,
        "owner_did": actor,
        "rkey": f"{spreadsheet_id}_{sheet_id}",
        "repo": actor,
        "sheet_id": sheet_id,
        "spreadsheet_id": spreadsheet_id,
        "account_did": _str(token.get("account_did")),
        "title": _str(props.get("title")),
        "sheet_type": _str(props.get("sheetType")),
        "sheet_index": int(props.get("index") or 0),
        "row_count": row_count,
        "column_count": col_count,
        "frozen_row_count": int(grid_props.get("frozenRowCount") or 0),
        "frozen_column_count": int(grid_props.get("frozenColumnCount") or 0),
        "hidden": _str(props.get("hidden") or "false"),
        "tab_color": json.dumps((props.get("tabColorStyle") or props.get("tabColor") or {}), ensure_ascii=False),
        "grid_values_json": json.dumps(grid_values, ensure_ascii=False)[:8000],
        "grid_values_preview": grid_preview,
        "cell_count": cell_count,
        "data_bytes": data_bytes,
        "charts_json": json.dumps(charts, ensure_ascii=False)[:4000],
        "protected_ranges_json": json.dumps(protected, ensure_ascii=False),
        "updated_time": now,
        "created_at": now,
        "org_id": "anon",
        "user_id": _str(token.get("account_did")),
        "actor_id": "sheets-mcp",
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
            if f.get("mimeType") != GSHEETS_MIME:
                continue
            if change.get("removed"):
                _execute(f"DELETE FROM {SHEETS_SPREADSHEET_TABLE} WHERE file_id = %s AND account_did = %s", (file_id, _str(token.get("account_did"))))
            else:
                try:
                    # includeGridData=true fetches sheet values (first 20 rows per sheet)
                    ss = _http_json(
                        f"https://sheets.googleapis.com/v4/spreadsheets/{file_id}?includeGridData=true&ranges=A1:T20",
                        headers={"authorization": f"Bearer {access}"},
                    )
                    _insert(SHEETS_SPREADSHEET_TABLE, _spreadsheet_row(token, ss, file_id, _str(f.get("modifiedTime"))))
                    for sheet in ss.get("sheets") or []:
                        _insert(SHEETS_SHEET_TABLE, _sheet_row(token, _str(ss.get("spreadsheetId")), sheet))
                    synced += 1
                except Exception:
                    pass  # permission denied or transient — skip

        new_cursor = _str(data.get("newStartPageToken") or data.get("nextPageToken") or page_token)
        page_token = _str(data.get("nextPageToken"))

    _execute(
        f"UPDATE {SHEETS_TOKEN_TABLE} SET last_sync_at = %s, cursor = %s, updated_at = %s WHERE vertex_id = %s",
        (now_iso(), new_cursor, now_iso(), _str(token.get("vertex_id"))),
    )
    return {"ok": True, "synced": synced, "cursor": new_cursor}


def sync_from_google(email: str = "", **_: Any) -> dict[str, Any]:
    if not email:
        return {"ok": False, "error": "email required"}
    token = _fetch_one(f"SELECT * FROM {SHEETS_TOKEN_TABLE} WHERE email = %s AND status = 'active' LIMIT 1", (email,))
    if not token:
        return {"ok": False, "error": "No active Sheets account. connectAccount first."}
    return _sync_token(token)


def cron_tick(**_: Any) -> dict[str, Any]:
    rows = _fetch_all(f"SELECT * FROM {SHEETS_TOKEN_TABLE} WHERE status = 'active' ORDER BY COALESCE(last_sync_at, created_at) ASC LIMIT 10")
    synced = 0
    errors = 0
    for token in rows:
        result = _sync_token(token)
        synced += int(result.get("synced") or 0)
        errors += 0 if result.get("ok") else 1
    return {"ok": errors == 0, "accounts": len(rows), "synced": synced, "errors": errors}
