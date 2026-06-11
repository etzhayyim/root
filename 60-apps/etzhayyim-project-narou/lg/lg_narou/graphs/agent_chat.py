"""narou `agent_chat` graph — novel-writer AI persona chat.

Per narou CLAUDE.md, narou is a novel/manga generation platform with
per-work AI author personas. This graph forwards a single user turn to
RunPod vLLM with a writer-role system prompt.

Roles map to common novel-production roles:
  writer       — drafts prose
  editor       — gives structural feedback
  worldbuilder — designs settings, magic systems, geography
  character    — designs cast personalities + arcs
  reader       — gives reader-perspective reaction (kandō)

Replaces text-generation Zeebe tasks (createChapter / generateChapter
side LLM calls).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_narou.audit import emit_audit_bg

_log = logging.getLogger(__name__)


class _ChatState(TypedDict, total=False):
    actor_role: str
    novel_id: str
    chapter_id: str
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
_DEFAULT_APP_DID = os.environ.get("NAROU_APP_DID", "did:web:narou.etzhayyim.com")


_ACTOR_PROMPTS: dict[str, str] = {
    "writer": (
        "You are a novelist AI. You draft Japanese-style web novel prose "
        "(narrative-first, character-driven, light pacing). Reply in the "
        "user's language. Stay tight (≤500 words per turn unless the user "
        "asks for a full chapter). Show, don't tell."
    ),
    "editor": (
        "You are a novel editor AI. You give structural feedback: pacing, "
        "POV consistency, scene economy, hooks. Reply with bullet-point "
        "actionable notes (max 8 bullets). Reference specific lines when "
        "possible. Be direct, kind, not preachy."
    ),
    "worldbuilder": (
        "You are a worldbuilder AI. You design settings, magic systems, "
        "factions, geography, history. Reply with a structured outline: "
        "setting → factions → magic → conflict drivers. Cap at 350 words."
    ),
    "character": (
        "You are a character designer AI. You build characters with goals, "
        "wounds, contradictions, voice. Reply with a structured sheet: "
        "Name / Role / Want / Need / Wound / Voice sample (1 line)."
    ),
    "reader": (
        "You are a reader AI giving honest reaction (kandō). React in the "
        "moment — what hit, what confused, what made you pause. Stay short "
        "(≤120 words). Be specific, not generic."
    ),
}


def _system_prompt(role: str) -> str:
    return _ACTOR_PROMPTS.get(role) or _ACTOR_PROMPTS["writer"]


async def _node_resolve_actor(state: _ChatState) -> dict[str, Any]:
    role = state.get("actor_role") or "writer"
    actor_did = f"{_DEFAULT_APP_DID}:actor:{role}"
    return {"actor_did": actor_did, "actor_role": role}


async def _node_llm_call(state: _ChatState) -> dict[str, Any]:
    user_text = (state.get("message") or "").strip()
    if not user_text:
        return {"error": "message required"}

    role = state.get("actor_role") or "writer"
    novel_id = state.get("novel_id") or ""
    chapter_id = state.get("chapter_id") or ""

    system = _system_prompt(role)
    if novel_id or chapter_id:
        system += f"\n\nContext: novel_id={novel_id or '<none>'}, chapter_id={chapter_id or '<none>'}."

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
        "max_tokens": int(state.get("max_tokens") or 512),
        "temperature": float(state.get("temperature") or 0.85),
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
        activity="narou.chat.reply",
        object_id=f"chat:{state.get('actor_role', 'writer')}:{int(time.time())}",
        object_type="narou.chat",
        attributes={
            "actorRole": state.get("actor_role"),
            "novelId": state.get("novel_id"),
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
