"""Minimal OSS FastAPI server for lg-pregel.

Surface:
  POST /runs                          → invoke outlook_triage graph synchronously
  POST /threads/search                → list pending gray-zone emails (HITL)
  GET  /threads/{thread_id}/state     → fetch interrupt envelope for one item
  POST /threads/{thread_id}/runs/stream → submit human verdict (SSE response)
  GET  /health /ok                    → liveness
  GET  /graphs                        → list graph IDs

Auth: optional `LG_PREGEL_API_KEY` env enforces `x-api-key` on /runs and HITL endpoints.
Cron path (x-cron=1) is allowed anonymously (tunnel-layer trust).
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.responses import StreamingResponse

from kotodama.agents.outlook_triage import outlook_triage_graph
from kotodama.pregel.graph import build_graph as _build_pregel
from kotodama.projector.graph import build_lifecycle_graph as _build_projector_lifecycle
from kotodama.projector.driver import build_driver_graph as _build_projector_driver
from kotodama.projector.ops import build_ops_graph as _build_projector_ops

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "outlook_triage": outlook_triage_graph,
    "pregel_triage": _build_pregel(),
    "projector_lifecycle": _build_projector_lifecycle(),
    "projector_driver": _build_projector_driver(),
    "projector_ops": _build_projector_ops(),
}

app = FastAPI(
    title="lg-pregel",
    description="LangGraph Server: Outlook email triage resident worker.",
    version="0.0.1",
)


def _enforce_auth(x_api_key: str | None, *, exempt: bool = False) -> None:
    if exempt:
        return
    expected = os.environ.get("LG_PREGEL_API_KEY")
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="x-api-key mismatch")


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {
        "ok": True,
        "app": "lg-pregel",
        "ts": int(time.time() * 1000),
        "graphs": list(GRAPHS.keys()),
    }


@app.get("/graphs")
def _list_graphs() -> dict[str, Any]:
    return {"graphs": list(GRAPHS.keys())}


@app.post("/runs")
async def _runs(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_cron: str | None = Header(default=None, alias="x-cron"),
) -> dict[str, Any]:
    _enforce_auth(x_api_key, exempt=(x_cron == "1"))
    graph_id = body.get("graph") or body.get("assistant_id", "outlook_triage")
    if graph_id not in GRAPHS:
        raise HTTPException(status_code=404, detail=f"unknown graph: {graph_id}")
    inp = body.get("input", {})
    config = body.get("config", {})
    t0 = time.time()
    try:
        result = await GRAPHS[graph_id].ainvoke(inp, config=config)
    except Exception as e:
        _log.exception("[lg-pregel][runs] graph=%s failed", graph_id)
        raise HTTPException(status_code=500, detail=str(e)[:300])
    return {
        "ok": True,
        "graph": graph_id,
        "duration_ms": int((time.time() - t0) * 1000),
        "result": result,
    }


# ── HITL endpoints (LangGraph-compatible shape) ───────────────────────────────


@app.get("/stats")
async def _stats(
    days: int = 30,
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    from kotodama.agents.outlook_stats import get_all_stats
    return get_all_stats(days=max(1, min(int(days), 365)))


@app.post("/threads/search")
async def _threads_search(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> list[dict[str, Any]]:
    _enforce_auth(x_api_key)
    status = str(body.get("status") or "interrupted")
    if status != "interrupted":
        return []
    limit = max(1, min(int(body.get("limit") or 50), 1000))
    from kotodama.agents.outlook_gray_review import list_pending_gray
    from kotodama.agents.outlook_reply_draft import list_pending_drafts
    gray = list_pending_gray(limit=limit)
    drafts = list_pending_drafts(limit=limit)
    combined = sorted(gray + drafts, key=lambda x: x.get("updated_at", ""), reverse=True)
    return combined[:limit]


@app.get("/threads/{thread_id}/state")
async def _thread_state(
    thread_id: str,
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> dict[str, Any]:
    _enforce_auth(x_api_key)

    if thread_id.startswith("draft-"):
        from kotodama.agents.outlook_reply_draft import get_draft_item
        item = get_draft_item(thread_id)
        if item is None:
            raise HTTPException(status_code=404, detail="thread not found")
        return {
            "thread_id": thread_id,
            "status": "interrupted",
            "interrupts": [
                {
                    "value": {
                        "tool_name": "request_draft_approval",
                        "question": f"返信下書き: {item.get('from_address', '')}",
                        "context": (
                            f"送信元: {item.get('from_address', '')}\n"
                            f"件名: {item.get('subject', '')}"
                        ),
                        "options": ["approve", "discard"],
                        "meta": {
                            "type": "reply_draft",
                            "draft_text": item.get("draft_text", ""),
                            "from_address": item.get("from_address", ""),
                            "subject": item.get("subject", ""),
                        },
                    }
                }
            ],
        }

    # Default: gray item
    from kotodama.agents.outlook_gray_review import get_gray_item
    item = get_gray_item(thread_id)
    if item is None:
        raise HTTPException(status_code=404, detail="thread not found")
    from_addr = str(item.get("from_address") or "")
    score = item.get("triage_score") or 0
    reasons = str(item.get("triage_reasons") or "")
    return {
        "thread_id": thread_id,
        "status": "interrupted",
        "interrupts": [
            {
                "value": {
                    "tool_name": "request_human_decision",
                    "question": f"メール仕分け: {from_addr}",
                    "context": (
                        f"送信元: {from_addr}\n"
                        f"スコア: {score}\n"
                        f"理由: {reasons}"
                    ),
                    "options": ["clean", "spam", "gray"],
                    "meta": {
                        "type": "email_triage",
                        "triage_score": item.get("triage_score") or 0,
                        "triage_reasons": [
                            r.strip()
                            for r in str(item.get("triage_reasons") or "").split(",")
                            if r.strip()
                        ],
                        "from_address": from_addr,
                    },
                }
            }
        ],
    }


@app.post("/threads/{thread_id}/runs/stream")
async def _thread_resume(
    thread_id: str,
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> Response:
    _enforce_auth(x_api_key)
    command = body.get("command") or {}

    if thread_id.startswith("draft-"):
        from kotodama.agents.outlook_reply_draft import apply_draft_verdict
        action = str(command.get("resume") or "discard").lower()
        final_text = str((body.get("command") or {}).get("final_text") or "")
        apply_draft_verdict(thread_id, action, final_text)
        verdict = action
    else:
        verdict = str(command.get("resume") or "gray").lower()
        if verdict not in {"clean", "spam", "gray"}:
            verdict = "gray"
        from kotodama.agents.outlook_gray_review import apply_verdict
        apply_verdict(thread_id, verdict)

    async def _event_stream():
        yield (
            "data: "
            + json.dumps({"event": "updates", "data": {"verdict": verdict, "thread_id": thread_id}})
            + "\n\n"
        )
        yield "data: " + json.dumps({"event": "end"}) + "\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")
