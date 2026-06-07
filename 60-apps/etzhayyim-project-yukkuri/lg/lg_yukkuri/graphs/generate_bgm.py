"""yukkuri `generateBgm` graph — ongakuka.compose cross-project invoke.

NSID: com.etzhayyim.apps.yukkuri.generateBgm

Actor: did:web:yukkuri.etzhayyim.com:actor:composer

Calls com.etzhayyim.ongakuka.compose XRPC to generate BGM for the video.
Stores returned blob_key in vertex_yukkuri_asset (kind='bgm').

CLAP cosine guard: ongakuka rejects similarity > 0.92 to existing works
(copyright invariant, CLAUDE.md §CRITICAL).
"""

from __future__ import annotations

import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_yukkuri.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_ONGAKUKA_URL = os.environ.get(
    "ONGAKUKA_XRPC_URL", "https://atproto.etzhayyim.com/xrpc/com.etzhayyim.ongakuka.compose"
)
_ONGAKUKA_TIMEOUT = float(os.environ.get("ONGAKUKA_TIMEOUT_SEC", "120"))
_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")
_COMPOSER_DID = os.environ.get(
    "YUKKURI_COMPOSER_DID", "did:web:yukkuri.etzhayyim.com:actor:composer"
)
_REPO = os.environ.get("YUKKURI_REPO_DID", "did:web:y5kk5r1x.etzhayyim.com")


class _State(TypedDict, total=False):
    video_id: str
    topic: str | None       # used for mood hint to ongakuka
    bgm_genre: str | None   # e.g. "calm_educational", "upbeat_quiz"
    # output
    bgm_blob_key: str | None
    bgm_asset_id: str | None
    error: str | None


async def _node_fetch_topic(state: _State) -> dict[str, Any]:
    if state.get("topic"):
        return {}
    video_id = state.get("video_id") or ""
    if not video_id:
        return {}
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "video_id", video_id, limit=1)
        if raw_rows:
            return {"topic": raw_rows[0].get("topic") or ""}
    except Exception as exc:
        _log.warning("fetch_topic failed: %s", exc)
    return {}


async def _node_compose_bgm(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    topic = (state.get("topic") or "yukkuri educational video").strip()
    genre = state.get("bgm_genre") or "calm_educational"
    video_id = state.get("video_id") or ""
    try:
        async with httpx.AsyncClient(timeout=_ONGAKUKA_TIMEOUT) as client:
            r = await client.post(
                _ONGAKUKA_URL,
                json={
                    "prompt": f"BGM for a Japanese educational video about: {topic}",
                    "genre": genre,
                    "durationSec": 180,
                    "loopable": True,
                    "projectId": video_id,
                },
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            return {"error": f"ongakuka {r.status_code}: {r.text[:200]}"}
        data = r.json()
        blob_key = data.get("blobKey") or data.get("blob_key") or ""
        if not blob_key:
            return {"error": "ongakuka returned no blobKey"}
        return {"bgm_blob_key": blob_key}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"ongakuka: {exc!s}"[:200]}


async def _node_insert_asset(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("bgm_blob_key"):
        return {}
    video_id = state.get("video_id") or ""
    asset_id = f"asset-bgm-{video_id}-{secrets.token_hex(3)}"
    created_at = datetime.now(tz=timezone.utc).isoformat()
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        await asyncio.to_thread(client.insert_row, "vertex_yukkuri_asset", {
            "vertex_id": asset_id,
            "video_id": video_id,
            "kind": "bgm",
            "actor_did": _COMPOSER_DID,
            "blob_key": state["bgm_blob_key"],
            "meta_json": "{}",
            "created_at": created_at
        })
    except Exception as exc:  # noqa: BLE001
        _log.exception("insert bgm asset failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"bgm_asset_id": asset_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_COMPOSER_DID,
        activity="yukkuri.generateBgm",
        object_id=f"bgm:{state.get('video_id', '')}:{int(time.time())}",
        object_type="yukkuri.asset",
        attributes={"videoId": state.get("video_id"), "ok": not bool(state.get("error"))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_topic", _node_fetch_topic, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("compose_bgm", _node_compose_bgm, retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert_asset", _node_insert_asset, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_topic")
    g.add_edge("fetch_topic", "compose_bgm")
    g.add_edge("compose_bgm", "insert_asset")
    g.add_edge("insert_asset", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_bgm")
