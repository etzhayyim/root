"""Google Meet ingest Zeebe worker — Meet REST API conferenceRecords.list."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

MEET_TOKEN_TABLE = "vertex_gmeet_oauth_token"
MEET_CONFERENCE_TABLE = "vertex_gmeet_conference"
MEET_PARTICIPANT_TABLE = "vertex_gmeet_participant"
ACTOR_DID = "did:web:meet.etzhayyim.com"


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
    req = urllib.request.Request(url, method=method, data=body, headers={"accept": "application/json", "user-agent": "etzhayyim-meet-zeebe/1", **(headers or {})})
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


def _duration_seconds(start: str, end: str) -> int:
    if not start or not end:
        return 0
    try:
        import re
        def _ts(s: str) -> float:
            # Parse RFC3339 to epoch
            s = re.sub(r"(\d{2}:\d{2}:\d{2})Z$", r"\1+00:00", s)
            from datetime import datetime, timezone
            return datetime.fromisoformat(s).timestamp()
        return max(0, int(_ts(end) - _ts(start)))
    except Exception:
        return 0


def _conference_row(token: dict[str, Any], rec: dict[str, Any]) -> dict[str, Any]:
    conference_id = _str(rec.get("name")).split("/")[-1] or _str(rec.get("name"))
    actor = ACTOR_DID
    now = now_iso()
    space = rec.get("space") or {}
    start_time = _str((rec.get("startTime") or {}).get("value") or rec.get("startTime"))
    end_time = _str((rec.get("endTime") or {}).get("value") or rec.get("endTime"))
    return {
        "vertex_id": f"at://{actor}/com.etzhayyim.apps.meet.conference/{conference_id}",
        "_seq": int(time.time() * 1000),
        "created_date": now[:10],
        "sensitivity_ord": 100,
        "owner_did": actor,
        "rkey": conference_id,
        "repo": actor,
        "conference_id": conference_id,
        "conference_name": _str(rec.get("name")),
        "space_name": _str(space.get("name")),
        "meeting_code": _str(space.get("meetingCode")),
        "account_did": _str(token.get("account_did")),
        "organizer_email": _str(rec.get("organizerEmail")),
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": _duration_seconds(start_time, end_time),
        "calendar_event_id": _str((rec.get("calendarEvent") or {}).get("eventId")),
        "entry_points_json": json.dumps((space.get("config") or {}).get("entryPointAccess") or [], ensure_ascii=False),
        "meet_uri": _str(space.get("meetingUri")),
        "recording_file_id": "",
        "transcript_file_id": "",
        "created_at": now,
        "org_id": "anon",
        "user_id": _str(token.get("account_did")),
        "actor_id": "meet-mcp",
    }


def _participant_row(token: dict[str, Any], conference_id: str, p: dict[str, Any]) -> dict[str, Any]:
    participant_id = _str(p.get("name")).split("/")[-1] or _str(p.get("name"))
    actor = ACTOR_DID
    now = now_iso()
    user = p.get("signedinUser") or p.get("anonymousUser") or {}
    join_time = _str((p.get("earliestStartTime") or {}).get("value") or p.get("earliestStartTime"))
    leave_time = _str((p.get("latestEndTime") or {}).get("value") or p.get("latestEndTime"))
    return {
        "vertex_id": f"at://{actor}/com.etzhayyim.apps.meet.participant/{conference_id}_{participant_id}",
        "_seq": int(time.time() * 1000),
        "created_date": now[:10],
        "sensitivity_ord": 100,
        "owner_did": actor,
        "rkey": f"{conference_id}_{participant_id}",
        "repo": actor,
        "participant_id": participant_id,
        "conference_id": conference_id,
        "account_did": _str(token.get("account_did")),
        "email": _str(user.get("email")),
        "display_name": _str(user.get("displayName")),
        "role": "",
        "join_time": join_time,
        "leave_time": leave_time,
        "duration_seconds": _duration_seconds(join_time, leave_time),
        "device_type": "",
        "created_at": now,
        "org_id": "anon",
        "user_id": _str(token.get("account_did")),
        "actor_id": "meet-mcp",
    }


def _sync_token(token: dict[str, Any]) -> dict[str, Any]:
    access = _refresh_access_token(_str(token.get("encrypted_refresh_token")))
    if not access:
        return {"ok": False, "error": "access token refresh failed"}

    # cursor stores the last-seen conference name (RFC3339 filter via startTime)
    last_cursor = _str(token.get("cursor"))
    synced = 0
    new_cursor = last_cursor

    page_token = ""
    while True:
        params: dict[str, str] = {"pageSize": "100"}
        if last_cursor:
            # Filter to conferences that ended after last sync
            params["filter"] = f"start_time>={last_cursor}"
        if page_token:
            params["pageToken"] = page_token
        qs = urllib.parse.urlencode(params)
        try:
            data = _http_json(f"https://meet.googleapis.com/v2/conferenceRecords?{qs}", headers={"authorization": f"Bearer {access}"})
        except Exception as exc:
            # Meet REST API may not be enabled for this account — return gracefully
            return {"ok": False, "error": f"Meet API error: {exc}", "synced": synced}

        for rec in data.get("conferenceRecords") or []:
            conference_id = _str(rec.get("name")).split("/")[-1]
            if not conference_id:
                continue
            _insert(MEET_CONFERENCE_TABLE, _conference_row(token, rec))
            synced += 1
            new_cursor = max(new_cursor, _str(rec.get("startTime", {}).get("value") or rec.get("startTime") or ""))

            # Fetch participants for this conference record
            try:
                pdata = _http_json(f"https://meet.googleapis.com/v2/{rec['name']}/participants?pageSize=100", headers={"authorization": f"Bearer {access}"})
                for p in pdata.get("participants") or []:
                    _insert(MEET_PARTICIPANT_TABLE, _participant_row(token, conference_id, p))
            except Exception:
                pass  # participants list may be empty or restricted

        page_token = _str(data.get("nextPageToken"))
        if not page_token:
            break

    _execute(
        f"UPDATE {MEET_TOKEN_TABLE} SET last_sync_at = %s, cursor = %s, updated_at = %s WHERE vertex_id = %s",
        (now_iso(), new_cursor or now_iso(), now_iso(), _str(token.get("vertex_id"))),
    )
    return {"ok": True, "synced": synced, "cursor": new_cursor}


def sync_from_google(email: str = "", **_: Any) -> dict[str, Any]:
    if not email:
        return {"ok": False, "error": "email required"}
    token = _fetch_one(f"SELECT * FROM {MEET_TOKEN_TABLE} WHERE email = %s AND status = 'active' LIMIT 1", (email,))
    if not token:
        return {"ok": False, "error": "No active Meet account. connectAccount first."}
    return _sync_token(token)


def cron_tick(**_: Any) -> dict[str, Any]:
    rows = _fetch_all(f"SELECT * FROM {MEET_TOKEN_TABLE} WHERE status = 'active' ORDER BY COALESCE(last_sync_at, created_at) ASC LIMIT 10")
    synced = 0
    errors = 0
    for token in rows:
        result = _sync_token(token)
        synced += int(result.get("synced") or 0)
        errors += 0 if result.get("ok") else 1
    return {"ok": errors == 0, "accounts": len(rows), "synced": synced, "errors": errors}
