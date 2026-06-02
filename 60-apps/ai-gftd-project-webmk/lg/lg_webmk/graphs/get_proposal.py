"""webmk `get_proposal` graph — fetch proposal by ID.

NSID: com.etzhayyim.apps.webmk.getProposal
"""

from __future__ import annotations

import logging
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

_log = logging.getLogger(__name__)
_RW_URL = os.environ.get("RW_URL", "")


class _State(TypedDict, total=False):
    proposal_id: str
    proposal: dict
    ok: bool
    error: str | None


async def _fetch(state: _State) -> dict[str, Any]:
    proposal_id = state.get("proposal_id", "")
    if not proposal_id:
        return {"ok": False, "error": "proposal_id required"}
    if not _RW_URL:
        return {"ok": False, "error": "RW_URL not configured"}
    try:
        import psycopg
        async with await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True) as conn:
            cur = await conn.execute(
                "SELECT proposal_id, client_name, website_url, industry, target_audience, "
                "budget_jpy, quality_score, status, created_at "
                "FROM vertex_webmk_proposal WHERE proposal_id = %s LIMIT 1",
                (proposal_id,),
            )
            row = await cur.fetchone()
            if not row:
                return {"ok": False, "error": "notFound", "proposal": {}}
            return {
                "ok": True,
                "proposal": {
                    "proposalId": row[0], "clientName": row[1], "websiteUrl": row[2],
                    "industry": row[3], "targetAudience": row[4], "budgetJpy": row[5],
                    "qualityScore": float(row[6] or 0), "status": row[7],
                    "createdAt": str(row[8]),
                },
            }
    except Exception as exc:  # noqa: BLE001
        _log.error("get_proposal failed: %s", exc)
        return {"ok": False, "error": str(exc)[:200]}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch", _fetch)
    g.add_edge(START, "fetch")
    g.add_edge("fetch", END)
    return g


GRAPH = _build().compile(name="get_proposal")
