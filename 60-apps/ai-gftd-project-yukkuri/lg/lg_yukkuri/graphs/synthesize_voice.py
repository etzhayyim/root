"""yukkuri `synthesizeVoice` graph — kokoro-ts TTS (L + R 並列).

NSID: com.etzhayyim.apps.yukkuri.synthesizeVoice

Actors:
  LEFT  → did:web:yukkuri.etzhayyim.com:actor:voiceLeft  (voice preset: af_heart)
  RIGHT → did:web:yukkuri.etzhayyim.com:actor:voiceRight (voice preset: am_puck)

Calls murakumo:inference/audio TTS endpoint (kokoro provider) for each
line, uploads wav to B2 via PDS uploadBlob, stores blob_key in
vertex_yukkuri_line.voice_blob_key. Advances video status → 'assembled'
when all parallel stages (voice + visual + bgm + sfx) are done
(checked by reviewing asset count; CF Worker drives ordering).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_yukkuri.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_MURAKUMO_TTS_URL = os.environ.get(
    "MURAKUMO_TTS_URL",
    "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1/audio/speech",
).rstrip("/")
_TTS_TIMEOUT = float(os.environ.get("TTS_TIMEOUT_SEC", "30"))
_PDS_BLOB_URL = os.environ.get("PDS_BLOB_URL", "https://atproto.etzhayyim.com/xrpc/com.atproto.repo.uploadBlob")
_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")

_VOICE_PRESET: dict[str, str] = {
    "left": os.environ.get("YUKKURI_VOICE_LEFT", "af_heart"),
    "right": os.environ.get("YUKKURI_VOICE_RIGHT", "am_puck"),
}


class _State(TypedDict, total=False):
    video_id: str
    lines: list[dict] | None            # internal: fetched lines
    # output
    voice_assets: list[dict] | None     # [{line_id, speaker, blob_key}]
    synthesized_count: int
    error: str | None


async def _fetch_lines(video_id: str) -> list[dict]:
    import psycopg
    conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
    try:
        cur = conn.cursor()
        await cur.execute(
            """SELECT line_id, scene_index, line_index, speaker, text
               FROM vertex_yukkuri_line
               WHERE video_id = %s AND voice_blob_key IS NULL
               ORDER BY scene_index, line_index
               LIMIT 500""",
            [video_id],
        )
        rows = await cur.fetchall()
    finally:
        await conn.close()
    return [{"line_id": r[0], "scene_index": r[1], "line_index": r[2],
             "speaker": r[3], "text": r[4]} for r in rows]


async def _tts_one(line: dict) -> dict[str, Any]:
    speaker = line["speaker"]
    voice = _VOICE_PRESET.get(speaker, "af_heart")
    text = line["text"]
    try:
        async with httpx.AsyncClient(timeout=_TTS_TIMEOUT) as client:
            r = await client.post(
                _MURAKUMO_TTS_URL,
                json={"model": "kokoro", "input": text, "voice": voice, "response_format": "wav"},
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            return {"line_id": line["line_id"], "error": f"tts {r.status_code}"}
        wav_bytes = r.content
        # upload blob to PDS
        async with httpx.AsyncClient(timeout=30) as client:
            ub = await client.post(
                _PDS_BLOB_URL,
                content=wav_bytes,
                headers={"Content-Type": "audio/wav"},
            )
        if ub.status_code >= 400:
            return {"line_id": line["line_id"], "error": f"uploadBlob {ub.status_code}"}
        blob_key = ub.json().get("blob", {}).get("ref", {}).get("$link", "")
        return {"line_id": line["line_id"], "speaker": speaker, "blob_key": blob_key}
    except Exception as exc:  # noqa: BLE001
        return {"line_id": line["line_id"], "error": str(exc)[:200]}


async def _node_fetch_lines(state: _State) -> dict[str, Any]:
    video_id = state.get("video_id") or ""
    if not video_id:
        return {"error": "video_id required"}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    try:
        fetched = await _fetch_lines(video_id)
        return {"lines": fetched}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"fetch_lines: {exc!s}"[:200]}


async def _node_synthesize(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    lines = state.get("lines") or []
    if not lines:
        return {"voice_assets": [], "synthesized_count": 0}

    results = await asyncio.gather(*[_tts_one(line) for line in lines], return_exceptions=False)
    ok = [r for r in results if not r.get("error")]
    failed = [r for r in results if r.get("error")]
    if failed:
        _log.warning("tts partial failure: %d/%d lines failed", len(failed), len(lines))
    return {"voice_assets": ok, "synthesized_count": len(ok)}


async def _node_update_lines(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("voice_assets"):
        return {}
    if not _RW_URL:
        return {}
    assets = state["voice_assets"]
    video_id = state.get("video_id") or ""
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            for asset in assets:
                await conn.execute(
                    "UPDATE vertex_yukkuri_line SET voice_blob_key = %s WHERE line_id = %s",
                    [asset["blob_key"], asset["line_id"]],
                )
            await conn.execute("FLUSH")
        finally:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        _log.exception("update lines voice_blob_key failed")
        return {"error": f"update: {exc!s}"[:300]}
    return {}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="yukkuri.synthesizeVoice",
        object_id=f"voice:{state.get('video_id', '')}:{int(time.time())}",
        object_type="yukkuri.voice",
        attributes={
            "videoId": state.get("video_id"),
            "synthesizedCount": state.get("synthesized_count", 0),
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_lines", _node_fetch_lines, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("synthesize", _node_synthesize, retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("update_lines", _node_update_lines, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_lines")
    g.add_edge("fetch_lines", "synthesize")
    g.add_edge("synthesize", "update_lines")
    g.add_edge("update_lines", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="synthesize_voice")
