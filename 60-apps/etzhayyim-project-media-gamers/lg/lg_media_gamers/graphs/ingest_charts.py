"""media-gamers `ingest_charts` graph — SteamSpy chart ingest + LLM analysis.

NSID: com.etzhayyim.apps.media_gamers.ingestCharts

Nodes:
  fetch   → SteamSpy top2w via API. Parse top 20 by players_2weeks.
  persist → INSERT into vertex_game_chart_snapshot (delete-then-insert; no ON CONFLICT).
  analyze → LLM analysis of the chart data.
  audit   → fire-and-forget OCEL.

Cron: every Monday 09:00 UTC (0 9 * * 1).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from lg_media_gamers.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_APP_DID = os.environ.get("MEDIA_GAMERS_APP_DID", "did:web:media-gamers.etzhayyim.com")
_MURAKUMO_URL = os.environ.get("MURAKUMO_OPENAI_URL", "").rstrip("/")
_MURAKUMO_KEY = os.environ.get("MURAKUMO_API_KEY", "")
_RUNPOD_URL = os.environ.get("RUNPOD_OPENAI_URL", "").rstrip("/")
_RUNPOD_KEY = os.environ.get("RUNPOD_API_KEY", "")
_LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3.5-4b")
_LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT_SEC", "60"))

_STEAMSPY_TOP2W_URL = "https://steamspy.com/api.php?request=top100in2weeks"
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class _State(TypedDict, total=False):
    source: str
    week_start: str
    entries: list[dict[str, Any]]
    snapshot_count: int
    analysis_ja: str
    analysis_en: str
    insight_tags: list[str]
    ok: bool
    error: str | None


# ── LLM helper ─────────────────────────────────────────────────────────────

async def _chat(system: str, user: str, max_tokens: int = 500, temp: float = 0.7) -> str:
    """Try Murakumo first, fall back to RunPod."""
    endpoints = []
    if _MURAKUMO_URL and _MURAKUMO_KEY:
        endpoints.append((_MURAKUMO_URL, _MURAKUMO_KEY))
    if _RUNPOD_URL and _RUNPOD_KEY:
        endpoints.append((_RUNPOD_URL, _RUNPOD_KEY))
    if not endpoints:
        return ""

    for url, key in endpoints:
        try:
            async with httpx.AsyncClient(timeout=_LLM_TIMEOUT) as c:
                r = await c.post(
                    f"{url}/chat/completions",
                    json={
                        "model": _LLM_MODEL,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temp,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {key}",
                    },
                )
            if r.status_code >= 400:
                continue
            text = (
                ((r.json().get("choices") or [{}])[0].get("message") or {})
                .get("content") or ""
            ).strip()
            return _THINK_RE.sub("", text).strip()
        except Exception as exc:  # noqa: BLE001
            _log.warning("LLM endpoint %s failed: %s", url, exc)
            continue
    return ""


# ── nodes ─────────────────────────────────────────────────────────────────

async def _node_fetch(state: _State) -> dict[str, Any]:
    week_start = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(_STEAMSPY_TOP2W_URL)
        if r.status_code >= 400:
            return {"ok": False, "error": f"steamspy http {r.status_code}", "week_start": week_start}
        data = r.json()
        # data is a dict of appid → game info. Sort by players_2weeks desc, take top 20.
        entries = sorted(
            [
                {
                    "appid": str(appid),
                    "name": info.get("name", ""),
                    "players_2weeks": int(info.get("players_2weeks") or 0),
                    "positive": int(info.get("positive") or 0),
                    "negative": int(info.get("negative") or 0),
                    "genre": str(info.get("genre") or ""),
                    "developer": str(info.get("developer") or ""),
                    "publisher": str(info.get("publisher") or ""),
                }
                for appid, info in data.items()
                if isinstance(info, dict)
            ],
            key=lambda x: x["players_2weeks"],
            reverse=True,
        )[:20]
        return {"entries": entries, "week_start": week_start, "ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200], "week_start": week_start}


async def _node_persist(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("entries"):
        return {"snapshot_count": 0}
    if not _RW_URL:
        _log.info("RW_URL not set — skipping chart snapshot persist")
        return {"snapshot_count": 0, "ok": True}

    entries = state["entries"]
    week_start = state.get("week_start", "")
    count = 0
    try:
        import psycopg  # type: ignore
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            for entry in entries:
                pk_appid = entry["appid"]
                # Delete-then-insert: RisingWave does not support ON CONFLICT DO UPDATE
                await conn.execute(
                    "DELETE FROM vertex_game_chart_snapshot WHERE appid = %s AND week_start = %s",
                    [pk_appid, week_start],
                )
                await conn.execute(
                    """INSERT INTO vertex_game_chart_snapshot
                       (appid, week_start, name, players_2weeks, positive, negative,
                        genre, developer, publisher, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    [
                        pk_appid, week_start, entry["name"],
                        entry["players_2weeks"], entry["positive"], entry["negative"],
                        entry["genre"], entry["developer"], entry["publisher"],
                        datetime.now(tz=timezone.utc).isoformat(),
                    ],
                )
                count += 1
        finally:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        _log.warning("chart persist failed: %s", exc)
        return {"snapshot_count": count, "error": str(exc)[:200]}
    return {"snapshot_count": count}


async def _node_analyze(state: _State) -> dict[str, Any]:
    entries = state.get("entries") or []
    if not entries:
        return {"analysis_ja": "", "analysis_en": "", "insight_tags": []}

    top5 = entries[:5]
    context = "\n".join(
        f"{i+1}. {e['name']} (players_2weeks={e['players_2weeks']}, genre={e['genre']})"
        for i, e in enumerate(top5)
    )

    raw = await _chat(
        "You are a gaming industry analyst. Analyze the Steam chart data and return JSON: "
        '{"analysis_ja": "...", "analysis_en": "...", "insight_tags": [...]}. '
        "analysis_ja: 2-3 sentences in Japanese. analysis_en: 2-3 sentences in English. "
        "insight_tags: 3-5 short English tags (e.g. 'action-rpg-dominant', 'indie-surge').",
        f"Steam Top 2-week chart (week of {state.get('week_start', 'unknown')}):\n{context}",
        max_tokens=500,
        temp=0.4,
    )

    analysis_ja = ""
    analysis_en = ""
    insight_tags: list[str] = []

    try:
        parsed = json.loads(raw)
        analysis_ja = str(parsed.get("analysis_ja") or "")
        analysis_en = str(parsed.get("analysis_en") or "")
        insight_tags = [str(t) for t in (parsed.get("insight_tags") or [])]
    except Exception:
        # Fallback: use raw as English analysis
        analysis_en = raw[:500] if raw else ""

    # Persist analysis record
    if _RW_URL and analysis_en:
        try:
            import psycopg  # type: ignore
            week_start = state.get("week_start", "")
            conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
            try:
                await conn.execute(
                    "DELETE FROM vertex_game_chart_analysis WHERE week_start = %s",
                    [week_start],
                )
                await conn.execute(
                    """INSERT INTO vertex_game_chart_analysis
                       (week_start, analysis_ja, analysis_en, insight_tags, created_at)
                       VALUES (%s, %s, %s, %s, %s)""",
                    [
                        week_start, analysis_ja, analysis_en,
                        json.dumps(insight_tags),
                        datetime.now(tz=timezone.utc).isoformat(),
                    ],
                )
            finally:
                await conn.close()
        except Exception as exc:  # noqa: BLE001
            _log.warning("chart analysis persist failed: %s", exc)

    return {
        "analysis_ja": analysis_ja,
        "analysis_en": analysis_en,
        "insight_tags": insight_tags,
    }


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="media_gamers.charts.ingest",
        object_id=f"charts:{state.get('week_start', '')}:{int(time.time())}",
        object_type="media_gamers.chartSnapshot",
        attributes={
            "weekStart": state.get("week_start"),
            "snapshotCount": state.get("snapshot_count", 0),
            "insightTags": state.get("insight_tags", []),
            "ok": state.get("ok", True),
            "error": state.get("error"),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch", _node_fetch)
    g.add_node("persist", _node_persist)
    g.add_node("analyze", _node_analyze)
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch")
    g.add_edge("fetch", "persist")
    g.add_edge("persist", "analyze")
    g.add_edge("analyze", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="ingest_charts")
