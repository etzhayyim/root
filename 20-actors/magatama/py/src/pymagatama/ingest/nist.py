"""NIST CSF fallback app handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import time
from typing import Any
from uuid import uuid4

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:nist.etzhayyim.com"
NANOID = "n1st0csf"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _s(value: Any, default: str = "") -> str:
    return str(value if value is not None else default)


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _event(kind: str, payload: dict[str, Any]) -> str:
    event_id = _id(kind)
    created_at = now_iso()
    rec = {**payload, "eventId": event_id, "createdAt": created_at}
    _execute(
        """INSERT INTO vertex_nist_event
        (vertex_id, _seq, owner_did, event_id, event_kind, event_json, created_at)
        VALUES (%s, _next_seq('vertex_nist_event'), %s, %s, %s, %s, %s)""",
        (
            f"nist:event:{event_id}",
            OWNER_DID,
            event_id,
            kind,
            json.dumps(rec, ensure_ascii=False, sort_keys=True),
            created_at,
        ),
    )
    return event_id


def health(**_: Any) -> dict[str, Any]:
    return {"status": "healthy", "app": "NIST CSF", "nanoid": NANOID, "did": OWNER_DID, "now": now_iso()}


def describe(**_: Any) -> dict[str, Any]:
    return {
        "name": "NIST CSF Intelligence",
        "did": OWNER_DID,
        "nanoid": NANOID,
        "capabilities": ["health", "describe", "wave", "csf-assessment", "cross-framework-mapping"],
        "protocols": ["xrpc", "w-protocol", "mcp", "bpmn"],
    }


def wave(message: Any = None, **_: Any) -> dict[str, Any]:
    text = _s(message, "hello")
    event_id = _event("wave", {"message": text, "postText": f"NIST CSF: {text}"})
    return {"ok": True, "nanoid": NANOID, "eventId": event_id}
