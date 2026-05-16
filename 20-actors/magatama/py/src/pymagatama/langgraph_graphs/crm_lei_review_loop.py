"""crm_lei_review_loop — LangGraph loop for CRM ↔ GLEIF LEI review.

Graph:
  load_review_queue -> maybe_interrupt -> mark_waiting -> END

The MCP server owns writes that verify/reject LEI matches. This graph is the
checkpointed orchestration layer: it loads queue rows, interrupts when human
evidence is needed, and marks queue rows as waiting for review.
"""

from __future__ import annotations

import json
from typing import Any, TypedDict


class CrmLeiReviewState(TypedDict, total=False):
    crmSystem: str
    entityType: str
    country: str
    limit: int
    queueItems: list[dict[str, Any]]
    queueCount: int
    needsHumanReview: bool
    interruptPayload: dict[str, Any]
    markedCount: int
    ok: bool
    error: str | None


def _rw_query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    try:
        from pymagatama.db_sync import sync_cursor

        with sync_cursor() as cur:
            cur.execute(sql, params)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row, strict=False)) for row in (cur.fetchall() or [])]
    except Exception:
        return []


def _rw_exec(sql: str, params: tuple[Any, ...] = ()) -> int:
    try:
        from pymagatama.db_sync import sync_cursor

        with sync_cursor() as cur:
            cur.execute(sql, params)
            return int(cur.rowcount or 0)
    except Exception:
        return 0


def load_review_queue(state: CrmLeiReviewState) -> dict[str, Any]:
    limit = int(state.get("limit") or 20)
    limit = max(1, min(limit, 100))
    filters = ["review_status IN ('open', 'needs_human_review')"]
    values: list[Any] = []
    if state.get("crmSystem"):
        filters.append("crm_system = %s")
        values.append(state["crmSystem"])
    if state.get("entityType"):
        filters.append("crm_entity_type = %s")
        values.append(state["entityType"])
    if state.get("country"):
        filters.append("crm_country = %s")
        values.append(str(state["country"]).upper())
    rows = _rw_query(
        f"""
        SELECT vertex_id, review_id, crm_system, crm_entity_type,
               crm_source_id, crm_legal_name, crm_country, review_status,
               review_reason, candidate_count, candidates_json, priority,
               evidence_note
          FROM view_crm_lei_review_queue
         WHERE {' AND '.join(filters)}
         ORDER BY priority DESC, updated_at DESC
         LIMIT {limit}
        """,
        tuple(values),
    )
    for row in rows:
        raw = row.get("candidates_json")
        if isinstance(raw, str) and raw:
            try:
                row["candidates"] = json.loads(raw)
            except Exception:
                row["candidates"] = []
    return {
        "queueItems": rows,
        "queueCount": len(rows),
        "needsHumanReview": bool(rows),
        "ok": True,
        "error": None,
    }


def maybe_interrupt(state: CrmLeiReviewState) -> dict[str, Any]:
    items = state.get("queueItems") or []
    if not items:
        return {"needsHumanReview": False, "interruptPayload": {}}
    payload = {
        "kind": "crm_lei_review",
        "message": "Review unresolved CRM legal entities and verify/reject LEI candidates through openLei.crm.bridge.review.",
        "items": items,
    }
    try:
        from langgraph.types import interrupt

        decision = interrupt(payload)
        return {"interruptPayload": payload, "reviewDecision": decision, "needsHumanReview": True}
    except Exception:
        return {"interruptPayload": payload, "needsHumanReview": True}


def mark_waiting(state: CrmLeiReviewState) -> dict[str, Any]:
    items = state.get("queueItems") or []
    count = 0
    for item in items:
        count += _rw_exec(
            """
            UPDATE vertex_crm_lei_review_item
               SET review_status = 'needs_human_review',
                   updated_at = %s,
                   evidence_note = %s
             WHERE vertex_id = %s
               AND review_status = 'open'
            """,
            (
                _now_iso(),
                "crm_lei_review_loop interrupted for human LEI evidence review",
                item.get("vertex_id"),
            ),
        )
    return {"markedCount": count}


def _now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _route_after_load(state: CrmLeiReviewState) -> str:
    return "interrupt" if state.get("queueCount", 0) else "done"


def build_graph():
    from langgraph.graph import END, StateGraph

    builder = StateGraph(CrmLeiReviewState)
    builder.add_node("load_review_queue", load_review_queue)
    builder.add_node("maybe_interrupt", maybe_interrupt)
    builder.add_node("mark_waiting", mark_waiting)
    builder.set_entry_point("load_review_queue")
    builder.add_conditional_edges(
        "load_review_queue",
        _route_after_load,
        {"interrupt": "maybe_interrupt", "done": END},
    )
    builder.add_edge("maybe_interrupt", "mark_waiting")
    builder.add_edge("mark_waiting", END)
    return builder.compile()
