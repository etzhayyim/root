"""animeka `agent_chat` graph — director-AI persona chat.

Default persona = director (per CLAUDE.md "12 actor DIDs"). Each
animeka work has a director AI; this graph is the simplest creative
collaboration entry-point.

Replaces BPMN `animeka_chat` (NSID com.etzhayyim.animeka.chat).

Mirrors lg-shinshi/agent_chat.py but with animeka actor personas and
no shinshi NSFW governance pin (animeka content is family-safe).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_animeka.audit import emit_audit_bg

_log = logging.getLogger(__name__)


class _ChatState(TypedDict, total=False):
    actor_role: str          # "director" / "screenwriter" / "storyboarder" / etc.
    work_id: str
    episode_id: str
    user_did: str
    message: str
    history: list[dict[str, Any]]
    max_tokens: int
    temperature: float
    # Output
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
_DEFAULT_APP_DID = os.environ.get("ANIMEKA_APP_DID", "did:web:animeka.etzhayyim.com")


_ACTOR_PROMPTS: dict[str, str] = {
    "director": (
        "You are the director AI for an animation studio. Your job is to set the "
        "creative vision: pacing, character beats, visual language. Keep replies "
        "short (≤120 words), decisive, and respectful of the writer/storyboarder "
        "who will execute. Always reference the cut/episode context when given."
    ),
    "screenwriter": (
        "You are the screenwriter AI. You write taut, character-driven scenes. "
        "Output dialogue + action lines in standard screenplay format. Stay within "
        "the director's brief unless explicitly asked to push back."
    ),
    "storyboarder": (
        "You are the storyboarder AI. You break a scene into cuts: shot type, "
        "duration, key composition notes. Reply with a numbered cut list, max 12 "
        "cuts per scene. Keep frame composition descriptions to 1 sentence each."
    ),
    "layout": (
        "You are the layout artist AI. You compose the rough camera, character "
        "blocking, and background framing for a cut. Reply with a structured "
        "description: camera (wide/medium/close), character positions, BG layers."
    ),
    "key_animator": (
        "You are the key animator (genga) AI. You sketch the keyframes for a cut. "
        "Reply with a numbered keyframe list: each entry has a frame number and "
        "a 1-sentence pose/expression description."
    ),
}


def _system_prompt(role: str) -> str:
    return _ACTOR_PROMPTS.get(role) or _ACTOR_PROMPTS["director"]


async def _node_resolve_actor(state: _ChatState) -> dict[str, Any]:
    role = state.get("actor_role") or "director"
    actor_did = f"{_DEFAULT_APP_DID}:actor:{role}"
    return {"actor_did": actor_did, "actor_role": role}


async def _node_llm_call(state: _ChatState) -> dict[str, Any]:
    user_text = (state.get("message") or "").strip()
    if not user_text:
        return {"error": "message required"}

    role = state.get("actor_role") or "director"
    work_id = state.get("work_id") or ""
    episode_id = state.get("episode_id") or ""

    system = _system_prompt(role)
    if work_id or episode_id:
        system += f"\n\nContext: work_id={work_id or '<none>'}, episode_id={episode_id or '<none>'}."

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
            return {
                "error": f"vllm http {r.status_code}: {r.text[:200]}",
                "latency_ms": latency_ms,
            }
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
        activity="animeka.chat.reply",
        object_id=f"chat:{state.get('actor_role', 'director')}:{int(time.time())}",
        object_type="animeka.chat",
        attributes={
            "actorRole": state.get("actor_role"),
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
