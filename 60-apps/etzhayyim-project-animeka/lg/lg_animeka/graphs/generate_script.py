"""animeka `generateScript` graph — LLM screenplay generation for an episode.

NSID: com.etzhayyim.animeka.generateScript

Given an episode_id, reads the episode title/synopsis from RW and
generates a structured screenplay (scene descriptions + dialogue
placeholders) using vLLM. Inserts the result into vertex_animeka
collection=com.etzhayyim.animeka.script.
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

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_VLLM_URL = os.environ.get("VLLM_URL", "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1").rstrip("/")
_VLLM_MODEL = os.environ.get("VLLM_MODEL", "tier0-general")
_VLLM_TIMEOUT = float(os.environ.get("VLLM_TIMEOUT_SEC", "60"))
_DEFAULT_APP_DID = os.environ.get("ANIMEKA_APP_DID", "did:web:animeka.etzhayyim.com")
_REPO = os.environ.get("ANIMEKA_REPO_DID", "did:web:an1m3k4x.etzhayyim.com")
_CKPT = "animagine-xl-4.0.safetensors"


class _State(TypedDict, total=False):
    episode_id: str
    synopsis: str | None       # override; if absent, read from DB
    scene_count: int | None    # default 5
    # output
    script_id: str | None
    script_uri: str | None
    body: str | None
    scene_count_actual: int | None
    error: str | None


async def _node_fetch_episode(state: _State) -> dict[str, Any]:
    episode_id = state.get("episode_id") or ""
    if not episode_id:
        return {"error": "episode_id required"}
    if state.get("synopsis"):
        return {}
    if not _RW_URL:
        return {}
    try:
        import psycopg
        rkey = episode_id.rsplit("/", 1)[-1] if "/" in episode_id else episode_id
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                "SELECT title, synopsis FROM vertex_animeka WHERE collection='com.etzhayyim.animeka.episode' AND rkey=%s LIMIT 1",
                [rkey],
            )
            row = await cur.fetchone()
        finally:
            await conn.close()
        if row:
            title = row[0] or ""
            synopsis = row[1] or f"Episode: {title}"
            return {"synopsis": synopsis}
    except Exception as exc:
        _log.warning("fetch_episode failed: %s", exc)
    return {}


async def _node_llm_script(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    synopsis = state.get("synopsis") or "An original anime episode."
    scene_count = int(state.get("scene_count") or 5)

    system = (
        "You are an anime screenwriter. Given a synopsis, write a compact "
        f"screenplay with exactly {scene_count} scenes. For each scene output:\n"
        "SCENE N: [location, time]\n"
        "ACTION: [1-2 sentences of action/visuals]\n"
        "DIALOGUE: [key line(s) or '(no dialogue)']\n\n"
        "Keep each scene under 80 words. Output only the screenplay, no preamble."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Synopsis: {synopsis}"},
    ]
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as client:
            r = await client.post(
                f"{_VLLM_URL}/chat/completions",
                json={"model": _VLLM_MODEL, "messages": messages, "max_tokens": 1200, "temperature": 0.7},
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            return {"error": f"vllm {r.status_code}: {r.text[:200]}"}
        resp = r.json()
    except Exception as exc:
        return {"error": f"vllm: {exc!s}"[:200]}

    body = ((resp.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    actual = body.count("SCENE ")
    return {"body": body.strip(), "scene_count_actual": actual or scene_count}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("body"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    episode_id = state.get("episode_id") or ""
    import secrets
    from datetime import datetime, timezone
    rkey = f"script-{secrets.token_hex(4)}"
    vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.script/{rkey}"
    created_at = datetime.now(tz=timezone.utc).isoformat()
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """INSERT INTO vertex_animeka
                   (vertex_id, repo, rkey, collection, kind, owner_did,
                    episode_id, scene_count, body, status, created_at)
                   VALUES (%s, %s, %s, 'com.etzhayyim.animeka.script', 'script',
                           %s, %s, %s, %s, 'draft', %s)""",
                [vertex_id, _REPO, rkey, _DEFAULT_APP_DID,
                 episode_id, state.get("scene_count_actual"),
                 state.get("body"), created_at],
            )
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert script failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"script_id": rkey, "script_uri": vertex_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.generateScript",
        object_id=f"script:{state.get('script_id', '')}:{int(time.time())}",
        object_type="animeka.script",
        attributes={"episodeId": state.get("episode_id"), "ok": not bool(state.get("error"))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_episode", _node_fetch_episode,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=1.5))
    g.add_node("llm_script", _node_llm_script,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0))
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_episode")
    g.add_edge("fetch_episode", "llm_script")
    g.add_edge("llm_script", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_script")
