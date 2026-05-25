"""Goriketsu Dash handlers for BPMN + Zeebe."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:k3t5g0r1.etzhayyim.com"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _num(value: Any, default: float = 0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if out >= 0 else default


def _int(value: Any, default: int = 0) -> int:
    return int(_num(value, default))


def _caller(kwargs: dict[str, Any]) -> str:
    for key in ("playerDid", "callerDid", "did", "actorDid"):
        value = kwargs.get(key)
        if isinstance(value, str) and value:
            return value
    caller = kwargs.get("caller")
    if isinstance(caller, dict) and isinstance(caller.get("did"), str):
        return caller["did"]
    return "anon"


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def submit_score(**kwargs: Any) -> dict[str, Any]:
    score_id = f"score-{uuid4().hex[:12]}"
    score = _int(kwargs.get("score"))
    slaps = _int(kwargs.get("slaps"))
    bananas = _int(kwargs.get("bananas"))
    run_sec = _num(kwargs.get("runSec"))
    player = _caller(kwargs)
    created_at = now_iso()
    _execute(
        """INSERT INTO vertex_atrecord_kami_ketsu_gorilla_score
        (vertex_id, _seq, owner_did, player_did, score, slaps, bananas, run_sec, created_at)
        VALUES (%s, _next_seq('vertex_atrecord_kami_ketsu_gorilla_score'), %s, %s, %s, %s, %s, %s, %s)""",
        (f"at://{OWNER_DID}/app.etzhayyim.apps.kami.ketsu_gorilla.score/{score_id}", OWNER_DID, player, score, slaps, bananas, run_sec, created_at),
    )
    return {"ok": True, "scoreId": score_id}


def get_leaderboard(limit: Any = 20, offset: Any = 0, **_: Any) -> dict[str, Any]:
    lim = max(1, min(_int(limit, 20), 100))
    off = max(0, _int(offset, 0))
    rows = _fetch_all(
        """SELECT vertex_id AS scoreId, player_did AS playerDid, score, slaps, bananas, run_sec AS runSec, created_at AS createdAt
        FROM vertex_atrecord_kami_ketsu_gorilla_score
        ORDER BY score DESC, bananas DESC, run_sec ASC, created_at ASC
        LIMIT %s OFFSET %s""",
        (lim, off),
    )
    return {"entries": rows, "limit": lim, "offset": off}
