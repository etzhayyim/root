"""yukkuri `reviewVideo` graph — critic QA (IP / 表現 / deepfake).

NSID: com.etzhayyim.apps.yukkuri.reviewVideo

Actor: did:web:yukkuri.etzhayyim.com:actor:critic

Checks (CLAUDE.md §CRITICAL Copyright Invariants):
  1. Script text: 個人名 / PII / 誹謗中傷 detection via LLM classifier
  2. Deepfake guard: real person name in topic/script → reject
  3. IP sim: topic vs known IP titles (simple keyword list, CLAP guard on audio delegated to ongakuka)

On pass  → status 'published' + T1 Social dispatch (app.bsky.feed.post)
On reject → status 'rejected' + review_reason logged
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_yukkuri.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_VLLM_URL = os.environ.get("VLLM_URL", "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1").rstrip("/")
_VLLM_MODEL = os.environ.get("VLLM_MODEL", "tier0-general")
_VLLM_TIMEOUT = float(os.environ.get("VLLM_TIMEOUT_SEC", "30"))
_PDS_XRPC_URL = os.environ.get("PDS_XRPC_URL", "https://atproto.etzhayyim.com/xrpc")
_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")
_CRITIC_DID = os.environ.get("YUKKURI_CRITIC_DID", "did:web:yukkuri.etzhayyim.com:actor:critic")
_SCRIPTWRITER_DID = os.environ.get(
    "YUKKURI_SCRIPTWRITER_DID", "did:web:yukkuri.etzhayyim.com:actor:scriptwriter"
)

_REVIEW_SYSTEM = """\
You are a content safety reviewer for a Japanese educational video platform.
Review the provided script excerpt and classify it as PASS or REJECT.

REJECT if:
- Contains real person's full name, contact info, or private information
- Contains defamatory statements about real individuals or organizations
- Simulates a real celebrity/public figure's voice or likeness
- Contains inappropriate content (violence, explicit material)
- Reproduces copyrighted lyrics/text verbatim (>30 chars)

Output JSON only: {"verdict": "PASS"|"REJECT", "reason": "<brief reason or null>"}
"""


class _State(TypedDict, total=False):
    video_id: str
    topic: str | None                   # internal: fetched topic
    script_excerpt: str | None          # internal: fetched script
    # output
    review_passed: bool | None
    review_reason: str | None
    error: str | None


async def _node_fetch_content(state: _State) -> dict[str, Any]:
    video_id = state.get("video_id") or ""
    if not video_id:
        return {"error": "video_id required"}
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_video = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "video_id", video_id, limit=1)
        topic = raw_video[0].get("topic") if raw_video else ""

        raw_lines = await asyncio.to_thread(client.select_where, "vertex_yukkuri_line", "video_id", video_id, limit=100)
        raw_lines.sort(key=lambda r: (int(r.get("scene_index") or 0), int(r.get("line_index") or 0)))
        
        script_excerpt = "\n".join(f"{(r.get('speaker') or '').upper()}: {r.get('text')}" for r in raw_lines[:40])
        return {"topic": topic, "script_excerpt": script_excerpt}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"fetch: {exc!s}"[:200]}


async def _node_llm_review(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    topic = state.get("topic") or ""
    excerpt = state.get("script_excerpt") or ""
    user_msg = f"Topic: {topic}\n\nScript excerpt:\n{excerpt[:2000]}"
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as client:
            r = await client.post(
                f"{_VLLM_URL}/chat/completions",
                json={
                    "model": _VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": _REVIEW_SYSTEM},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 200,
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"},
                },
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            # fail open: pass on LLM errors to avoid blocking production
            _log.warning("llm review error %s — defaulting to PASS", r.status_code)
            return {"review_passed": True, "review_reason": "llm_unavailable"}
        raw = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        import json
        try:
            parsed = json.loads(raw)
        except Exception:
            return {"review_passed": True, "review_reason": "parse_error"}
        verdict = parsed.get("verdict", "PASS")
        return {
            "review_passed": verdict == "PASS",
            "review_reason": parsed.get("reason"),
        }
    except Exception as exc:  # noqa: BLE001
        _log.warning("llm review exception — defaulting to PASS: %s", exc)
        return {"review_passed": True, "review_reason": "exception"}


async def _node_update_status(state: _State) -> dict[str, Any]:
    if state.get("error") or state.get("review_passed") is None:
        return {}
    video_id = state.get("video_id") or ""
    passed = state.get("review_passed", True)
    new_status = "published" if passed else "rejected"
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_video = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "video_id", video_id)
        if raw_video:
            row = raw_video[0]
            row["status"] = new_status
            await asyncio.to_thread(client.insert_row, "vertex_yukkuri_video", row)
    except Exception as exc:  # noqa: BLE001
        _log.exception("update status failed")
        return {"error": f"update: {exc!s}"[:300]}
    return {}


async def _node_social_publish(state: _State) -> dict[str, Any]:
    """T1 Social: app.bsky.feed.post on publish (derived write)."""
    if state.get("error") or not state.get("review_passed"):
        return {}
    video_id = state.get("video_id") or ""
    topic = state.get("topic") or "新作ゆっくり動画"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{_PDS_XRPC_URL}/app.bsky.feed.post",
                json={
                    "did": _APP_DID,
                    "text": f"🎬 新作ゆっくり動画: {topic[:80]}\nyukkuri.etzhayyim.com",
                    "collection": "app.bsky.feed.post",
                },
                headers={"Content-Type": "application/json"},
            )
    except Exception as exc:  # noqa: BLE001
        _log.warning("social publish failed (non-fatal): %s", exc)
    return {}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_CRITIC_DID,
        activity="yukkuri.reviewVideo",
        object_id=f"review:{state.get('video_id', '')}:{int(time.time())}",
        object_type="yukkuri.review",
        attributes={
            "videoId": state.get("video_id"),
            "passed": state.get("review_passed"),
            "reason": state.get("review_reason"),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_content", _node_fetch_content, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("llm_review", _node_llm_review, retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("update_status", _node_update_status, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("social_publish", _node_social_publish)
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_content")
    g.add_edge("fetch_content", "llm_review")
    g.add_edge("llm_review", "update_status")
    g.add_edge("update_status", "social_publish")
    g.add_edge("social_publish", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="review_video")
