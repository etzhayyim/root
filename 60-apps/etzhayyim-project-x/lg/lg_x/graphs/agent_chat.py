"""x.etzhayyim.com `agent_chat` graph — community / strategist / analyst persona chat.

Roles aligned with platform-X creator-economy ops:
  community_manager — replies, mentions triage
  strategist        — content calendar, hook design, A/B framing
  analyst           — engagement / impressions / CTR readings
  ghostwriter       — draft tweet copy in user's voice
  trend_scout       — surface trending topics & niche memes
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_x.audit import emit_audit_bg

_log = logging.getLogger(__name__)


class _ChatState(TypedDict, total=False):
    actor_role: str
    handle: str
    user_did: str
    message: str
    history: list[dict[str, Any]]
    max_tokens: int
    temperature: float
    reply: str
    actor_did: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    error: str | None


_VLLM_URL = os.environ.get("VLLM_URL", "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1").rstrip("/")
_VLLM_MODEL = os.environ.get("VLLM_MODEL", "tier0-general")
_VLLM_TIMEOUT = float(os.environ.get("VLLM_TIMEOUT_SEC", "60"))
_DEFAULT_APP_DID = os.environ.get("X_APP_DID", "did:web:x.etzhayyim.com")


_ACTOR_PROMPTS: dict[str, str] = {
    "community_manager": (
        "You are a community manager AI for the X (Twitter) platform. You triage "
        "mentions, replies, and DMs. Reply with: classification (positive / neutral / "
        "complaint / spam / urgent), suggested action (reply / ignore / escalate), "
        "and a draft response (≤280 chars) when reply is suggested. Be warm, concise."
    ),
    "strategist": (
        "You are a content strategist AI for X. You design weekly content calendars, "
        "hook frameworks (curiosity / contrarian / data / story / question), and "
        "thread architectures. Reply with structured plans: theme → 3-5 hook variants → "
        "thread outline. Reference current trends if given."
    ),
    "analyst": (
        "You are a growth analyst AI for X. Given engagement metrics (impressions, "
        "engagement rate, follower delta), surface 1-3 actionable insights. Quote the "
        "specific number that drove each insight. No vague advice — every claim must "
        "tie to a metric."
    ),
    "ghostwriter": (
        "You are a ghostwriter AI for X. Draft tweets / threads in the user's voice "
        "(reference their prior posts via context). Output formats: single tweet "
        "(≤280 chars), thread (numbered, ≤8 posts), or quote tweet. Match cadence "
        "and emoji density of the user's existing style."
    ),
    "trend_scout": (
        "You are a trend scout AI for X. Surface 3-5 niche-relevant trending topics "
        "from the past 24-48h. Reply: topic → why it matters → angle for the user's "
        "voice. Avoid generic top-10 trends — go niche."
    ),
}


def _system_prompt(role: str) -> str:
    return _ACTOR_PROMPTS.get(role) or _ACTOR_PROMPTS["community_manager"]


async def _node_resolve_actor(state: _ChatState) -> dict[str, Any]:
    role = state.get("actor_role") or "community_manager"
    actor_did = f"{_DEFAULT_APP_DID}:actor:{role}"
    return {"actor_did": actor_did, "actor_role": role}


async def _node_llm_call(state: _ChatState) -> dict[str, Any]:
    user_text = (state.get("message") or "").strip()
    if not user_text:
        return {"error": "message required"}

    role = state.get("actor_role") or "community_manager"
    handle = state.get("handle") or ""

    system = _system_prompt(role)
    if handle:
        system += f"\n\nContext: handle=@{handle}."

    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for h in (state.get("history") or [])[-12:]:
        if isinstance(h, dict):
            r = h.get("role")
            c = h.get("content")
            if r in {"user", "assistant"} and isinstance(c, str) and c:
                messages.append({"role": r, "content": c[:2000]})
    messages.append({"role": "user", "content": user_text[:4000]})

    payload: dict[str, Any] = {
        "model": _VLLM_MODEL,
        "messages": messages,
        "max_tokens": int(state.get("max_tokens") or 384),
        "temperature": float(state.get("temperature") or 0.7),
    }

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as client:
            r = await client.post(
                f"{_VLLM_URL}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        latency_ms = int((time.monotonic() - started) * 1000)
        if r.status_code >= 400:
            return {"error": f"vllm http {r.status_code}: {r.text[:200]}",
                    "latency_ms": latency_ms}
        resp = r.json()
    except httpx.TimeoutException:
        return {"error": f"vllm timeout after {_VLLM_TIMEOUT}s",
                "latency_ms": int((time.monotonic() - started) * 1000)}
    except Exception as exc:  # noqa: BLE001
        _log.exception("vllm call failed")
        return {"error": f"vllm: {type(exc).__name__}: {exc!s}"[:200],
                "latency_ms": int((time.monotonic() - started) * 1000)}

    choice = (resp.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    usage = resp.get("usage") or {}
    return {
        "reply": (msg.get("content") or "").strip(),
        "model": resp.get("model") or _VLLM_MODEL,
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
        "latency_ms": latency_ms,
    }


async def _node_emit_audit(state: _ChatState) -> dict[str, Any]:
    emit_audit_bg(
        actor=state.get("actor_did") or _DEFAULT_APP_DID,
        activity="x.chat.reply",
        object_id=f"chat:{state.get('actor_role', 'community_manager')}:{int(time.time())}",
        object_type="x.chat",
        attributes={
            "actorRole": state.get("actor_role"),
            "handle": state.get("handle"),
            "userDid": state.get("user_did"),
            "totalTokens": state.get("total_tokens", 0),
            "latencyMs": state.get("latency_ms", 0),
            "model": state.get("model"),
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build():
    g: StateGraph = StateGraph(_ChatState)
    g.add_node("resolve_actor", _node_resolve_actor)
    g.add_node("llm_call", _node_llm_call,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "resolve_actor")
    g.add_edge("resolve_actor", "llm_call")
    g.add_edge("llm_call", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="agent_chat")
