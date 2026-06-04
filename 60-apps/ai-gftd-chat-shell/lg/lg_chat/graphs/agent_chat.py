"""lg-chat `agent_chat` graph — general-purpose assistant.

ReAct tool-calling loop using direct httpx against keiei-litellm
(Gemma 4 E4B-it, OpenAI-compatible).

State machine:
  START
   → prepare        (message + history → messages list)
   → llm            (POST /v1/chat/completions with tool schemas)
   → route          (tool calls present? → execute → llm loop; else → END)
   → execute_tools  (sync dispatch in thread executor)
   → llm            (append tool results, continue)
   → END

Input (from ChatPanel.svelte /lg/runs/stream body.input):
  {
    "message": "<user text>",
    "history": [{"role": "user"|"assistant", "content": "..."}],
    "conv_id": "<optional>",
    "owner_did": "<optional>"
  }

Config.configurable:
  tier: "fast" | "balanced" | "reasoning"   (ignored for now, single model)
  ephemeral: true                            (server.py strips checkpointer)

Output state fields:
  reply: str        — final assistant text
  tool_results: list  — tool call results (for UI display)
  error: str | None
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_chat.tools import TOOL_SCHEMAS, dispatch_tool

_log = logging.getLogger(__name__)

_VLLM_URL = os.environ.get("VLLM_URL",
    "http://keiei-litellm.keiei-llm.svc.cluster.local:4000/v1").rstrip("/")
_VLLM_MODEL = os.environ.get("MURAKUMO_DEFAULT_MODEL", "gemma-4-E4B-it")
_VLLM_API_KEY = os.environ.get("LLM_API_KEY", "dummy")
_VLLM_TIMEOUT = float(os.environ.get("VLLM_TIMEOUT_SEC", "60"))
_MAX_ITERATIONS = int(os.environ.get("CHAT_MAX_ITERATIONS", "8"))
_MAX_HISTORY = int(os.environ.get("CHAT_MAX_HISTORY", "20"))

_SYSTEM_PROMPT = (
    "You are Gftd Chat, a helpful AI assistant on gftd.ai. "
    "You have access to tools for code execution, web search, file saving, "
    "image generation, conversation search, and report scheduling. "
    "Use tools when they would genuinely help the user. "
    "Reply in the user's language. Be concise and accurate."
)


class _ChatState(TypedDict, total=False):
    # Input
    message: str
    history: list[dict[str, Any]]
    conv_id: str
    owner_did: str
    # Working
    messages: list[dict[str, Any]]
    iteration: int
    # Output
    reply: str
    tool_results: list[dict[str, Any]]
    error: str | None


# ── nodes ──────────────────────────────────────────────────────────────


async def _node_prepare(state: _ChatState) -> dict[str, Any]:
    msgs: list[dict[str, Any]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for h in (state.get("history") or [])[-_MAX_HISTORY:]:
        if isinstance(h, dict) and h.get("role") in {"user", "assistant", "tool"}:
            msgs.append({"role": h["role"], "content": str(h.get("content") or "")[:4000]})
    user_text = str(state.get("message") or "").strip()
    if user_text:
        msgs.append({"role": "user", "content": user_text})
    return {"messages": msgs, "iteration": 0, "tool_results": []}


async def _node_llm(state: _ChatState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    msgs = state.get("messages") or []
    payload: dict[str, Any] = {
        "model": _VLLM_MODEL,
        "messages": msgs,
        "tools": TOOL_SCHEMAS,
        "tool_choice": "auto",
        "max_tokens": 2048,
        "temperature": 0.4,
    }
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as client:
            r = await client.post(
                f"{_VLLM_URL}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {_VLLM_API_KEY}",
                         "Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            return {"error": f"vllm http {r.status_code}: {r.text[:300]}"}
        resp = r.json()
    except httpx.TimeoutException:
        return {"error": f"vllm timeout after {_VLLM_TIMEOUT}s"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"vllm: {type(exc).__name__}: {exc!s}"[:200]}

    choice = (resp.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    tool_calls = msg.get("tool_calls") or []

    updated_msgs = list(msgs)
    updated_msgs.append(msg)

    if not tool_calls:
        content = str(msg.get("content") or "").strip()
        # Strip <think>…</think> reasoning blocks before returning to user
        import re
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        return {"messages": updated_msgs, "reply": content}

    return {"messages": updated_msgs, "iteration": (state.get("iteration") or 0) + 1}


async def _node_execute_tools(state: _ChatState) -> dict[str, Any]:
    msgs = list(state.get("messages") or [])
    last_msg = msgs[-1] if msgs else {}
    tool_calls = last_msg.get("tool_calls") or []
    if not tool_calls:
        return {}

    conv_id = state.get("conv_id") or ""
    owner_did = state.get("owner_did") or ""
    msg_id = f"tc-{int(time.time() * 1000)}"

    tool_results: list[dict[str, Any]] = list(state.get("tool_results") or [])
    tool_result_msgs: list[dict[str, Any]] = []

    loop = asyncio.get_event_loop()
    for tc in tool_calls:
        fn = tc.get("function") or {}
        name = str(fn.get("name") or "")
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except (json.JSONDecodeError, TypeError):
            args = {}
        _log.info("tool call: %s %s", name, list(args.keys()))

        result = await loop.run_in_executor(
            None,
            lambda n=name, a=args: dispatch_tool(n, a, conv_id=conv_id, msg_id=msg_id, owner_did=owner_did),
        )
        tool_results.append({"name": name, "args": args, "result": result})
        tool_result_msgs.append({
            "role": "tool",
            "tool_call_id": tc.get("id") or f"tc-{name}",
            "content": json.dumps(result, ensure_ascii=False)[:4000],
        })

    return {"messages": msgs + tool_result_msgs, "tool_results": tool_results}


def _route_after_llm(state: _ChatState) -> str:
    if state.get("error"):
        return END
    if state.get("reply") is not None:
        return END
    if (state.get("iteration") or 0) >= _MAX_ITERATIONS:
        return END
    msgs = state.get("messages") or []
    last = msgs[-1] if msgs else {}
    if last.get("tool_calls"):
        return "execute_tools"
    return END


# ── graph ──────────────────────────────────────────────────────────────


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_ChatState)
    g.add_node("prepare", _node_prepare)
    g.add_node("llm", _node_llm, retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("execute_tools", _node_execute_tools)

    g.add_edge(START, "prepare")
    g.add_edge("prepare", "llm")
    g.add_conditional_edges("llm", _route_after_llm, {"execute_tools": "execute_tools", END: END})
    g.add_edge("execute_tools", "llm")

    return g


GRAPH = _build().compile(name="agent_chat")
