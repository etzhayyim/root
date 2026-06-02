"""
shosha.agentLoop — LangGraph StateGraph port (ADR-2605080600 Phase 4).

Replaces the LangServer task `task_shosha_agent_chat` + BPMN `agentLoop.bpmn`.
Registered under assistant_id="shosha_agent_loop" in LangGraph Server.

Graph:
  START → fetch_context → call_llm → emit_audit → END

State:
  prompt          str       user question (required input)
  tier            str       LLM tier (default: "fast" -> Murakumo organism gateway)
  maxTokens       int       max LLM output tokens (default: 1500)
  commodityFocus  str|None  optional commodity filter
  _context        str       assembled RW context (internal)
  content         str       LLM response (output)
  model           str       LLM model used (output)
  latencyMs       int       LLM call latency (output)
  ok              bool      success flag (output)
  error           str|None  error message if ok=False

Activation (once routing_target='langgraph' set on the binding row):
  POST /xrpc/com.etzhayyim.apps.shosha.agentLoop → bpmn-dispatcher
    → POST http://langgraph-server.mitama-udf.svc:8000/runs
        {assistant_id: "shosha_agent_loop", input: {prompt, tier?, ...}}
"""

from __future__ import annotations

import re
import time
from typing import Any, TypedDict

from pymagatama.db_sync import sync_cursor
from pymagatama import llm


# ── State ──────────────────────────────────────────────────────────────

class ShoshaAgentState(TypedDict, total=False):
    prompt: str
    tier: str
    maxTokens: int
    commodityFocus: str | None
    _context: str
    content: str
    model: str
    latencyMs: int
    intelRowsUsed: int
    marketViewRowsUsed: int
    exposureRowsUsed: int
    ok: bool
    error: str | None


# ── System prompt ──────────────────────────────────────────────────────

_AGENT_SYSTEM = (
    "You are 商社 (shosha.etzhayyim.com), an autonomous AI sogo-shosha agent. "
    "You have read access to recent market intel, market views, and open "
    "exposure. Be concise, factual, and acknowledge uncertainty. Default "
    "to Japanese unless the user writes English. Keep replies under 600 "
    "tokens."
)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
# Also strip unclosed <think> blocks (truncated at max_tokens boundary).
_THINK_OPEN_RE = re.compile(r"<think>.*$", re.DOTALL)


def _strip_think(text: str) -> str:
    text = _THINK_RE.sub("", text)
    text = _THINK_OPEN_RE.sub("", text)
    return text.strip()


# ── RW helpers ────────────────────────────────────────────────────────

def _rw_query(sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
    try:
        with sync_cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() or []
    except Exception:
        return []


# ── Nodes ─────────────────────────────────────────────────────────────

def fetch_context(state: ShoshaAgentState) -> dict:
    """Read recent intel, market views, and exposure from RisingWave."""
    focus = (state.get("commodityFocus") or "").strip() or None
    params: tuple[Any, ...] = (focus,) if focus else ()

    intel = _rw_query(
        "SELECT symbol, value, unit, ts_ms FROM vertex_shosha_intel "
        "WHERE value IS NOT NULL "
        + ("AND symbol = %s " if focus else "")
        + "ORDER BY ts_ms DESC LIMIT 30",
        params,
    )
    views = _rw_query(
        "SELECT commodity, direction, confidence, price_target, rationale "
        "FROM vertex_shosha_market_view "
        + ("WHERE commodity = %s " if focus else "")
        + "ORDER BY as_of_date DESC LIMIT 20",
        params,
    )
    exposure = _rw_query(
        "SELECT commodity, net_usd FROM mv_shosha_exposure_by_commodity "
        + ("WHERE commodity = %s " if focus else "")
        + "ORDER BY net_usd DESC LIMIT 20",
        params,
    )

    lines: list[str] = []
    if intel:
        lines.append("Recent intel ticks (symbol, value, unit, ts_ms):")
        for s, v, u, t in intel[:15]:
            lines.append(f"  - {s} | {v} | {u} | {t}")
    if views:
        lines.append("Market views (commodity, direction, conf, target, rationale):")
        for c, d, cf, pt, r in views[:10]:
            lines.append(f"  - {c} | {d} | {cf} | {pt} | {r}")
    if exposure:
        lines.append("Open exposure (commodity, net USD):")
        for c, n in exposure[:10]:
            lines.append(f"  - {c} | {n}")

    # Phase E1 (ADR-2605082000): pre-render `_userMessage` so the downstream
    # mcp_tool com.etzhayyim.tools.llm.chat node can consume `user` directly via
    # input_paths={"user":"_userMessage"}, retiring the call_llm py_primitive.
    ctx_text = "\n".join(lines) if lines else "(no context rows yet)"
    prompt_text = (state.get("prompt") or "").strip()
    return {
        "_context": ctx_text,
        "_userMessage": f"{ctx_text}\n\nUser asks:\n{prompt_text}",
        "intelRowsUsed": len(intel),
        "marketViewRowsUsed": len(views),
        "exposureRowsUsed": len(exposure),
    }


def call_llm(state: ShoshaAgentState) -> dict:
    """Call LLM with assembled context."""
    prompt = (state.get("prompt") or "").strip()
    if not prompt:
        return {"ok": False, "error": "prompt is required"}

    tier = state.get("tier") or "fast"
    max_tokens = int(state.get("maxTokens") or 1500)
    context = state.get("_context") or "(no context)"
    user_msg = f"{context}\n\nUser asks:\n{prompt}"

    try:
        resp = llm.call_tier(
            tier, _AGENT_SYSTEM, user_msg,
            max_tokens=max_tokens, temperature=0.3,
        )
        return {
            "ok": True,
            "content": _strip_think(resp.get("content") or ""),
            "model": resp.get("model") or "unknown",
            "latencyMs": int(resp.get("latencyMs") or 0),
        }
    except llm.LlmError as e:
        return {"ok": False, "error": str(e), "content": "", "model": "", "latencyMs": 0}


def emit_audit(state: ShoshaAgentState) -> dict:
    """Write OCEL audit row to RisingWave (non-fatal if it fails)."""
    import uuid
    import time as _time

    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_repo_commit
                  (vertex_id, repo, collection, rkey, action, ts_ms, record_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    "did:web:shosha.etzhayyim.com",
                    "com.etzhayyim.apps.shosha.agentLoop",
                    f"lg-{int(_time.time() * 1000)}",
                    "create",
                    int(_time.time() * 1000),
                    f'{{"ok":{str(state.get("ok", False)).lower()},'
                    f'"latencyMs":{state.get("latencyMs", 0)}}}',
                ),
            )
    except Exception:
        pass
    return {}


# ── Graph factory ──────────────────────────────────────────────────────

def build_graph():
    """Build and compile the shosha agentLoop StateGraph."""
    from langgraph.graph import END, StateGraph

    builder = StateGraph(ShoshaAgentState)
    builder.add_node("fetch_context", fetch_context)
    builder.add_node("call_llm", call_llm)
    builder.add_node("emit_audit", emit_audit)

    builder.set_entry_point("fetch_context")
    builder.add_edge("fetch_context", "call_llm")
    builder.add_edge("call_llm", "emit_audit")
    builder.add_edge("emit_audit", END)

    return builder.compile()
