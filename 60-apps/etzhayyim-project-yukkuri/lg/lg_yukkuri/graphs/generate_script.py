"""yukkuri `generateScript` graph — LLM で台本生成 (L/R 掛け合い + scene 分割).

NSID: com.etzhayyim.apps.yukkuri.generateScript

Actor: did:web:yukkuri.etzhayyim.com:actor:scriptwriter

Input: video_id (既存 queued video)
Output: scenes[] + lines[] を vertex_yukkuri_scene / vertex_yukkuri_line に INSERT。
        vertex_yukkuri_video.status を 'script' に更新。
"""

from __future__ import annotations

import json
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

_VLLM_URL = os.environ.get("VLLM_URL", "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1").rstrip("/")
_VLLM_MODEL = os.environ.get("VLLM_MODEL", "tier0-general")
_VLLM_TIMEOUT = float(os.environ.get("VLLM_TIMEOUT_SEC", "90"))
_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")
_SCRIPTWRITER_DID = os.environ.get(
    "YUKKURI_SCRIPTWRITER_DID", "did:web:yukkuri.etzhayyim.com:actor:scriptwriter"
)
_REPO = os.environ.get("YUKKURI_REPO_DID", "did:web:y5kk5r1x.etzhayyim.com")

_SYSTEM_PROMPT = """\
You are a Japanese "yukkuri" video scriptwriter. Given a topic, write a two-character
commentary script in the style of Japanese educational YouTube videos.
Characters:
  LEFT  = "ゆきり" (Reimu-like, knowledgeable, calm)
  RIGHT = "まりり" (Marisa-like, energetic, curious)

Output valid JSON only:
{
  "scenes": [
    {
      "location": "<scene location / background hint in Japanese>",
      "action": "<1-2 sentence scene description in Japanese>",
      "lines": [
        {"speaker": "left"|"right", "text": "<dialogue in Japanese>", "emotion": "normal"|"happy"|"surprised"|"sad"|"angry"},
        ...
      ]
    },
    ...
  ]
}

Rules:
- 5–8 scenes for a 3–5 minute video
- Each scene has 3–6 lines
- Start with RIGHT asking a question, LEFT answering
- End with both summarising the key takeaway
- Keep vocabulary accessible (N3 level)
- Include 1 surprising fact mid-video
- No real person names, no PII
"""


class _State(TypedDict, total=False):
    video_id: str
    topic: str | None       # override; if absent, read from DB
    outline: str | None
    scene_count_target: int | None
    # output
    scenes: list[dict] | None
    scene_count: int | None
    script_error: str | None
    error: str | None


async def _node_fetch_video(state: _State) -> dict[str, Any]:
    video_id = state.get("video_id") or ""
    if not video_id:
        return {"error": "video_id required"}
    if state.get("topic"):
        return {}
    try:
        import asyncio
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "video_id", video_id, limit=1)
        if raw_rows:
            row = raw_rows[0]
            return {"topic": row.get("topic") or "", "outline": row.get("outline")}
    except Exception as exc:
        _log.warning("fetch_video failed: %s", exc)
    return {}


async def _node_llm_script(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    topic = (state.get("topic") or "").strip()
    if not topic:
        return {"error": "topic is empty"}
    outline_hint = f"\nOutline provided by user:\n{state['outline']}" if state.get("outline") else ""
    user_msg = f"Topic: {topic}{outline_hint}"

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as client:
            r = await client.post(
                f"{_VLLM_URL}/chat/completions",
                json={
                    "model": _VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 3000,
                    "temperature": 0.8,
                    "response_format": {"type": "json_object"},
                },
                headers={"Content-Type": "application/json"},
            )
    except Exception as exc:
        return {"error": f"vllm: {exc!s}"[:200]}

    if r.status_code >= 400:
        return {"error": f"vllm {r.status_code}: {r.text[:200]}"}

    raw = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    try:
        parsed = json.loads(raw)
        scenes = parsed.get("scenes") or []
    except Exception:
        # fallback: try to extract JSON block
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            scenes = json.loads(raw[start:end]).get("scenes") or []
        except Exception:
            return {"error": f"json_parse: {raw[:200]}"}

    if not scenes:
        return {"error": "llm returned empty scenes"}

    return {"scenes": scenes, "scene_count": len(scenes)}


async def _node_insert_scenes_lines(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("scenes"):
        return {}
    video_id = state.get("video_id") or ""
    scenes = state["scenes"]
    created_at = datetime.now(tz=timezone.utc).isoformat()
    try:
        import asyncio
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        for i, scene in enumerate(scenes):
            scene_id = f"scene-{video_id}-{i}"
            scene_vertex_id = f"at://{_REPO}/com.etzhayyim.apps.yukkuri.scene/{scene_id}"
            await asyncio.to_thread(client.insert_row, "vertex_yukkuri_scene", {
                "vertex_id": scene_vertex_id,
                "scene_id": scene_id,
                "video_id": video_id,
                "scene_index": i,
                "location": scene.get("location", ""),
                "action": scene.get("action", ""),
                "created_at": created_at
            })
            for j, line in enumerate(scene.get("lines") or []):
                line_id = f"line-{video_id}-{i}-{j}"
                line_vertex_id = f"at://{_REPO}/com.etzhayyim.apps.yukkuri.line/{line_id}"
                await asyncio.to_thread(client.insert_row, "vertex_yukkuri_line", {
                    "vertex_id": line_vertex_id,
                    "line_id": line_id,
                    "video_id": video_id,
                    "scene_index": i,
                    "line_index": j,
                    "speaker": line.get("speaker", "left"),
                    "text": line.get("text", ""),
                    "emotion": line.get("emotion", "normal"),
                    "created_at": created_at
                })
        # advance video status
        video_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "video_id", video_id)
        if video_rows:
            video_row = video_rows[0]
            video_row["status"] = "script"
            await asyncio.to_thread(client.insert_row, "vertex_yukkuri_video", video_row)
    except Exception as exc:  # noqa: BLE001
        _log.exception("insert scenes/lines failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_SCRIPTWRITER_DID,
        activity="yukkuri.generateScript",
        object_id=f"script:{state.get('video_id', '')}:{int(time.time())}",
        object_type="yukkuri.script",
        attributes={
            "videoId": state.get("video_id"),
            "sceneCount": state.get("scene_count"),
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_video", _node_fetch_video, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("llm_script", _node_llm_script, retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0))
    g.add_node("insert", _node_insert_scenes_lines, retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_video")
    g.add_edge("fetch_video", "llm_script")
    g.add_edge("llm_script", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_script")
