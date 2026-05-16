"""Generic-primitive worker for ai.gftd.tools.audit.* (ADR-2605082000 §2.5 follow-up).

Replaces per-actor `emit_audit` node functions across bulk-51 (shosha,
isbn, animeka, …) with a single data-resolved MCP tool. Each invocation
writes one row to ``vertex_repo_commit`` (OCEL trail).

Wired into mcp_dispatch via ``register_overrides`` (the namespace is
``ai.gftd.tools.audit``, outside the per-actor convention).
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any


async def task_audit_emit(
    *,
    repo: str = "",
    collection: str = "",
    rkey: str = "",
    action: str = "",
    recordJson: Any | None = None,
    **_ignored: Any,
) -> dict[str, Any]:
    """Insert one OCEL audit row into vertex_repo_commit.

    Best-effort: swallows DB errors and returns ``{"error": str(exc)}`` so
    audit emission never blocks an actor cycle. Same semantics as the
    per-actor ``emit_audit`` nodes it replaces.
    """
    if not repo or not collection or not action:
        return {"error": "repo / collection / action required"}

    rk = rkey or str(uuid.uuid4())
    ts_ms = int(time.time() * 1000)
    payload = recordJson if isinstance(recordJson, dict) else {}
    record_json = json.dumps(payload, separators=(",", ":"))
    vertex_id = f"{repo}:{collection}:{rk}:{action}"

    try:
        # Defer import so unit tests can stub the cursor.
        from pymagatama.db_sync import sync_cursor
    except Exception as exc:
        return {"error": f"db_sync unavailable: {exc}"}

    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_repo_commit
                  (vertex_id, repo, collection, rkey, action, ts_ms, record_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (vertex_id, repo, collection, rk, action, ts_ms, record_json),
            )
    except Exception as exc:  # pragma: no cover — defensive
        return {"vertexId": vertex_id, "rkey": rk, "error": str(exc)}

    return {"vertexId": vertex_id, "rkey": rk}
