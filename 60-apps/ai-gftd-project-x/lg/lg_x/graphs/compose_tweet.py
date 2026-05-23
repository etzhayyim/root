"""x.etzhayyim.com `compose_tweet` graph — draft tweet/thread copy (no posting).

Pure LLM compose path. Does NOT call X API — that's a future `post`
graph that requires OAuth setup. This graph is the safest first
ship: drafts can be reviewed by a human before any actual API call.

Output shape:
  format       single | thread | quote_tweet | reply
  tweets       list[str], each ≤280 chars (X's hard limit)
  rationale    1-line "why this hook"
  hashtags     list[str], up to 4
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_x.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_VLLM_URL = os.environ.get("VLLM_URL", "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1").rstrip("/")
_VLLM_MODEL = os.environ.get("VLLM_MODEL", "tier0-general")
_VLLM_TIMEOUT = float(os.environ.get("VLLM_TIMEOUT_SEC", "60"))
_DEFAULT_APP_DID = os.environ.get("X_APP_DID", "did:web:x.etzhayyim.com")


class _ComposeState(TypedDict, total=False):
    handle: str
    voice_sample: str       # paste recent posts to match cadence
    topic: str
    angle: str              # hook framework: curiosity / contrarian / story / data / question
    format: str             # single | thread | quote_tweet | reply
    quote_url: str          # for quote_tweet
    reply_to: str           # for reply
    max_tweets: int

    # Output
    tweets: list[str]
    rationale: str
    hashtags: list[str]
    model: str
    latency_ms: int
    error: str | None


_HOOK_HINTS: dict[str, str] = {
    "curiosity": "Open with a surprising claim or counterintuitive observation that the reader needs to keep reading to resolve.",
    "contrarian": "Open by stating the popular view, then immediately disagreeing with a specific reason.",
    "story": "Open mid-action with a tight scene (≤2 lines), then zoom out to the lesson.",
    "data": "Open with a single number that reframes the topic, then explain its meaning.",
    "question": "Open with a high-stakes question the reader genuinely doesn't know the answer to.",
}


def _build_system_prompt(state: _ComposeState) -> str:
    fmt = state.get("format") or "single"
    angle = state.get("angle") or "curiosity"
    hook = _HOOK_HINTS.get(angle, _HOOK_HINTS["curiosity"])
    handle = state.get("handle") or "the user"
    max_t = max(1, min(12, int(state.get("max_tweets") or (8 if fmt == "thread" else 1))))

    return (
        f"You are a tweet ghostwriter for @{handle}. Draft X content in their voice.\n"
        f"Format: {fmt}. Max {max_t} tweet(s). Each ≤280 characters (HARD LIMIT).\n"
        f"Angle: {angle} — {hook}\n"
        "Output ONLY a JSON object with exact keys: "
        "{ \"tweets\": [string, ...], \"rationale\": string, \"hashtags\": [string, ...] }. "
        "No prose, no code-fence, no commentary."
    )


def _enforce_280(text: str) -> str:
    # X counts URLs as 23 chars + emoji as 2-4. Conservatively cap to 270 for safety.
    if len(text) <= 270:
        return text
    cut = text[:267].rsplit(" ", 1)[0]
    return cut + "…"


def _parse_llm_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    # Strip code fences if the model wrapped JSON despite the prompt.
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n", "", raw)
        raw = re.sub(r"\n```$", "", raw)
    # Try direct parse
    try:
        return json.loads(raw)
    except Exception:
        pass
    # Try to find the first { ... } block
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}


async def _node_compose(state: _ComposeState) -> dict[str, Any]:
    topic = (state.get("topic") or "").strip()
    if not topic:
        return {"error": "topic required"}

    sys_prompt = _build_system_prompt(state)
    user_prompt_parts: list[str] = [f"Topic: {topic}"]
    voice = (state.get("voice_sample") or "").strip()
    if voice:
        user_prompt_parts.append(f"Voice sample (match cadence + emoji density):\n{voice[:1500]}")
    if state.get("format") == "quote_tweet" and state.get("quote_url"):
        user_prompt_parts.append(f"Quote-tweeting: {state['quote_url']}")
    if state.get("format") == "reply" and state.get("reply_to"):
        user_prompt_parts.append(f"Reply context: {state['reply_to'][:1500]}")

    payload: dict[str, Any] = {
        "model": _VLLM_MODEL,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": "\n\n".join(user_prompt_parts)},
        ],
        "max_tokens": 768,
        "temperature": 0.85,
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
    except Exception as exc:  # noqa: BLE001
        _log.exception("vllm call failed")
        return {"error": f"vllm: {type(exc).__name__}: {exc!s}"[:200],
                "latency_ms": int((time.monotonic() - started) * 1000)}

    raw = (((resp.get("choices") or [{}])[0]).get("message") or {}).get("content") or ""
    parsed = _parse_llm_json(raw)

    tweets = [_enforce_280(t) for t in (parsed.get("tweets") or []) if isinstance(t, str)]
    if not tweets:
        # If parse failed, fall back to treating the whole reply as one tweet.
        tweets = [_enforce_280(raw)]
    return {
        "tweets": tweets,
        "rationale": (parsed.get("rationale") or "")[:300],
        "hashtags": [h for h in (parsed.get("hashtags") or []) if isinstance(h, str)][:4],
        "model": resp.get("model") or _VLLM_MODEL,
        "latency_ms": latency_ms,
    }


async def _node_emit_audit(state: _ComposeState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="x.tweet.composed",
        object_id=f"compose:{state.get('handle','-')}:{int(time.time())}",
        object_type="x.tweet",
        attributes={
            "handle": state.get("handle"),
            "topic": (state.get("topic") or "")[:120],
            "format": state.get("format"),
            "angle": state.get("angle"),
            "tweetCount": len(state.get("tweets") or []),
            "latencyMs": state.get("latency_ms", 0),
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build():
    g: StateGraph = StateGraph(_ComposeState)
    g.add_node("compose", _node_compose,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "compose")
    g.add_edge("compose", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="compose_tweet")
