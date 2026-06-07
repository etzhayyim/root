"""media-gamers `autopilot` graph — fully autonomous guide generation + social post.

NSID: com.etzhayyim.apps.media_gamers.autopilot
Cron: */30 * * * * (every 30 minutes)

Each cron fire:
  1. resolve_mood  → pick mood based on epoch rotation
  2. select_game   → map mood to game + pick guide_type
  3. generate      → LLM guide generation
  4. evaluate      → quality_score computation
  5. translate     → (conditional) translate if score >= 70
  6. commit        → POST to commitGuide XRPC
  7. post          → social post via PDS com.atproto.repo.createRecord
  8. audit         → OCEL

Conditional edge after evaluate:
  quality_score >= 70 → translate → commit → post → audit
  quality_score < 70  → commit → post → audit
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from lg_media_gamers.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("MEDIA_GAMERS_APP_DID", "did:web:media-gamers.etzhayyim.com")
_REPO_DID = os.environ.get("MEDIA_GAMERS_REPO_DID", "did:web:a7m8oocs.etzhayyim.com")
_PDS_BASE = os.environ.get("PDS_URL", "https://atproto.etzhayyim.com")
_MURAKUMO_URL = os.environ.get("MURAKUMO_OPENAI_URL", "").rstrip("/")
_MURAKUMO_KEY = os.environ.get("MURAKUMO_API_KEY", "")
_RUNPOD_URL = os.environ.get("RUNPOD_OPENAI_URL", "").rstrip("/")
_RUNPOD_KEY = os.environ.get("RUNPOD_API_KEY", "")
_LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3.5-4b")
_LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT_SEC", "60"))
_COMMIT_GUIDE_XRPC = os.environ.get(
    "COMMIT_GUIDE_XRPC_URL",
    "https://media-gamers.etzhayyim.com/xrpc/com.etzhayyim.apps.media_gamers.guide.commitGuide",
)
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

SEED_GAMES = [
    {"slug": "elden-ring", "name": "Elden Ring", "genre": "action-rpg", "releaseYear": 2022, "developer": "fromsoftware", "publisher": "bandai-namco", "platforms": ["PS5", "Xbox Series X", "PC"]},
    {"slug": "zelda-totk", "name": "The Legend of Zelda: Tears of the Kingdom", "genre": "action-adventure", "releaseYear": 2023, "developer": "nintendo", "publisher": "nintendo", "platforms": ["Switch"]},
    {"slug": "monster-hunter-wilds", "name": "Monster Hunter Wilds", "genre": "action-rpg", "releaseYear": 2025, "developer": "capcom", "publisher": "capcom", "platforms": ["PS5", "Xbox Series X", "PC"]},
    {"slug": "black-myth-wukong", "name": "Black Myth: Wukong", "genre": "action-rpg", "releaseYear": 2024, "developer": "game-science", "publisher": "game-science", "platforms": ["PS5", "PC"]},
    {"slug": "pokoa-world", "name": "Pokoa World", "genre": "creature-rpg", "releaseYear": 2026, "developer": "etzhayyim-studio", "publisher": "etzhayyim", "platforms": ["PC", "Mobile"]},
    {"slug": "metaphor-refantazio", "name": "Metaphor: ReFantazio", "genre": "jrpg", "releaseYear": 2024, "developer": "atlus", "publisher": "atlus", "platforms": ["PS5", "PS4", "PC"]},
    {"slug": "ff7-rebirth", "name": "Final Fantasy VII Rebirth", "genre": "jrpg", "releaseYear": 2024, "developer": "square-enix", "publisher": "square-enix", "platforms": ["PS5", "PC"]},
    {"slug": "stellar-blade", "name": "Stellar Blade", "genre": "action-rpg", "releaseYear": 2024, "developer": "shift-up", "publisher": "sony", "platforms": ["PS5", "PC"]},
    {"slug": "dq3-hd2d", "name": "Dragon Quest III HD-2D Remake", "genre": "jrpg", "releaseYear": 2024, "developer": "square-enix", "publisher": "square-enix", "platforms": ["Switch", "PS5", "Xbox", "PC"]},
    {"slug": "gta-vi", "name": "Grand Theft Auto VI", "genre": "open-world", "releaseYear": 2025, "developer": "rockstar", "publisher": "take-two", "platforms": ["PS5", "Xbox Series X"]},
    {"slug": "pokemon-legends-z-a", "name": "Pokémon Legends: Z-A", "genre": "creature-rpg", "releaseYear": 2025, "developer": "game-freak", "publisher": "the-pokemon-company", "platforms": ["Switch", "Switch 2"]},
]

_SEED_GAMES_BY_SLUG = {g["slug"]: g for g in SEED_GAMES}

GUIDE_TYPES = ["boss-guide", "weapon-guide", "beginner-guide", "tier-list"]
TARGET_LANGS = ["ja", "zh", "es", "ar", "hi", "ko"]
QUALITY_THRESHOLD = 70

# Joucho mood → game slugs mapping
_MOOD_TO_GAMES: dict[str, list[str]] = {
    "focused":    ["elden-ring", "black-myth-wukong"],
    "calm":       ["elden-ring", "black-myth-wukong"],
    "joyful":     ["zelda-totk", "pokoa-world", "dq3-hd2d"],
    "grateful":   ["zelda-totk", "pokoa-world", "dq3-hd2d"],
    "reflective": ["monster-hunter-wilds", "metaphor-refantazio"],
}
_MOODS = ["focused", "calm", "joyful", "grateful", "reflective"]


class _State(TypedDict, total=False):
    mood: str
    game_slug: str
    guide_type: str
    game_name: str
    game_genre: str
    game_year: int
    body: str
    title: str
    quality_score: float
    translations: list[dict[str, Any]]
    post_status: str
    ok: bool
    error: str | None


# ── LLM helper ─────────────────────────────────────────────────────────────

async def _chat(system: str, user: str, max_tokens: int = 1000, temp: float = 0.7) -> str:
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


def _compute_quality(body: str) -> float:
    length_score = min(1.0, len(body) / 4000)
    heading_score = 1.0 if re.search(r"(^|\n)#{1,3}\s+", body) else 0.4
    checklist_score = 1.0 if "-" in body or re.search(r"\n\d+\.", body) else 0.5
    return round((length_score * 0.45 + heading_score * 0.30 + checklist_score * 0.25) * 100, 1)


# ── nodes ─────────────────────────────────────────────────────────────────

async def _node_resolve_mood(state: _State) -> dict[str, Any]:
    # Rotate through 5 moods every 30 minutes using epoch
    idx = (int(time.time()) // 1800) % 5
    mood = _MOODS[idx]
    return {"mood": mood}


async def _node_select_game(state: _State) -> dict[str, Any]:
    mood = state.get("mood", "reflective")
    game_slugs = _MOOD_TO_GAMES.get(mood, ["monster-hunter-wilds", "metaphor-refantazio"])

    # Pick game deterministically but with variation
    game_idx = (int(time.time()) // 1800) % len(game_slugs)
    game_slug = game_slugs[game_idx]

    # Pick guide_type deterministically
    guide_idx = (int(time.time()) // 900) % len(GUIDE_TYPES)
    guide_type = GUIDE_TYPES[guide_idx]

    return {"game_slug": game_slug, "guide_type": guide_type}


async def _node_generate(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}

    game_slug = state.get("game_slug", "")
    game = _SEED_GAMES_BY_SLUG.get(game_slug)
    if not game:
        return {"error": f"unknown game slug: {game_slug!r}"}

    game_name = game["name"]
    game_genre = game["genre"]
    game_year = game["releaseYear"]
    guide_type = state.get("guide_type", "beginner-guide")
    guide_label = guide_type.replace("-", " ").title()

    system = (
        "You are an expert gaming guide writer. "
        "Write detailed, well-structured guides with headings (##), bullet points, and numbered lists. "
        "Target length: 800-1200 words. Language: English."
    )
    user = (
        f"Write a comprehensive {guide_label} for {game_name} ({game_genre}, {game_year}). "
        f"Include: introduction, key strategies, tips and tricks, common mistakes to avoid. "
        f"Format with markdown headings and bullet points. Start with a title on the first line."
    )

    raw = await _chat(system, user, max_tokens=1500, temp=0.7)
    if not raw:
        return {"error": "LLM returned empty response", "body": "", "title": ""}

    lines = raw.strip().splitlines()
    title = lines[0].lstrip("#").strip() if lines else f"{game_name} {guide_type}"
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else raw

    return {
        "game_name": game_name,
        "game_genre": game_genre,
        "game_year": game_year,
        "title": title,
        "body": body,
    }


async def _node_evaluate(state: _State) -> dict[str, Any]:
    body = state.get("body", "")
    score = _compute_quality(body)
    return {"quality_score": score}


async def _node_translate(state: _State) -> dict[str, Any]:
    body = state.get("body", "")
    title = state.get("title", "")
    translations = []

    for lang in TARGET_LANGS:
        try:
            raw = await _chat(
                f"You are a professional translator. Translate the following gaming guide to {lang}. "
                "Keep markdown formatting. Return JSON: "
                '{"title": "...", "body": "...", "social_post": "..."}. '
                "social_post: 1-2 sentences with relevant hashtags.",
                f"Title: {title}\n\nBody:\n{body}",
                max_tokens=1800,
                temp=0.3,
            )
            parsed: dict[str, Any] = {}
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {"title": title, "body": raw, "social_post": ""}

            translated_body = str(parsed.get("body") or "")
            translations.append({
                "lang": lang,
                "title": str(parsed.get("title") or title),
                "body": translated_body,
                "quality_score": _compute_quality(translated_body),
                "social_post": str(parsed.get("social_post") or ""),
            })
        except Exception as exc:  # noqa: BLE001
            _log.warning("translate to %s failed: %s", lang, exc)

    return {"translations": translations}


async def _node_commit(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}

    payload = {
        "gameSlug": state.get("game_slug", ""),
        "guideType": state.get("guide_type", ""),
        "gameName": state.get("game_name", ""),
        "gameGenre": state.get("game_genre", ""),
        "gameYear": state.get("game_year"),
        "title": state.get("title", ""),
        "body": state.get("body", ""),
        "qualityScore": state.get("quality_score", 0),
        "translations": state.get("translations", []),
    }
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                _COMMIT_GUIDE_XRPC,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            _log.warning("commit guide http %d: %s", r.status_code, r.text[:200])
    except Exception as exc:  # noqa: BLE001
        _log.warning("commit guide failed: %s", exc)
    return {}


async def _node_post(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {"post_status": "skipped"}

    title = state.get("title", "")
    body = state.get("body", "")
    game_genre = state.get("game_genre", "gaming")
    guide_type = state.get("guide_type", "guide")
    slug = state.get("game_slug", "")

    hashtag_genre = game_genre.replace("-", "").replace(" ", "")
    hashtag_guide = guide_type.replace("-", "").replace(" ", "")
    guide_url = f"https://media-gamers.etzhayyim.com/en/game/{slug}/{guide_type}"

    text = (
        f"{title}\n\n"
        f"{body[:200]}...\n\n"
        f"#{hashtag_genre} #gaming #{hashtag_guide}\n"
        f"{guide_url}"
    )

    from datetime import datetime, timezone
    record = {
        "$type": "app.bsky.feed.post",
        "text": text[:300],
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"{_PDS_BASE}/xrpc/com.atproto.repo.createRecord",
                json={
                    "repo": _REPO_DID,
                    "collection": "app.bsky.feed.post",
                    "record": record,
                },
                headers={
                    "Content-Type": "application/json",
                    "x-kotodama-verified": "true",
                    "x-etzhayyim-org-id": "anon",
                },
            )
        if r.status_code < 400:
            return {"post_status": "posted", "ok": True}
        _log.warning("pds post http %d: %s", r.status_code, r.text[:200])
        return {"post_status": "error", "ok": bool(state.get("body"))}
    except Exception as exc:  # noqa: BLE001
        _log.warning("post to pds failed: %s", exc)
        return {"post_status": "error", "ok": bool(state.get("body"))}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="media_gamers.autopilot",
        object_id=f"autopilot:{state.get('game_slug','')}:{state.get('guide_type','')}:{int(time.time())}",
        object_type="media_gamers.guide",
        attributes={
            "mood": state.get("mood"),
            "gameSlug": state.get("game_slug"),
            "guideType": state.get("guide_type"),
            "qualityScore": state.get("quality_score"),
            "translationCount": len(state.get("translations") or []),
            "postStatus": state.get("post_status"),
            "ok": state.get("ok", True),
            "error": state.get("error"),
        },
    )
    return {}


def _route_after_evaluate(state: _State) -> str:
    score = state.get("quality_score", 0)
    return "translate" if (score or 0) >= QUALITY_THRESHOLD else "commit"


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("resolve_mood", _node_resolve_mood)
    g.add_node("select_game", _node_select_game)
    g.add_node("generate", _node_generate)
    g.add_node("evaluate", _node_evaluate)
    g.add_node("translate", _node_translate)
    g.add_node("commit", _node_commit)
    g.add_node("post", _node_post)
    g.add_node("audit", _node_audit)

    g.add_edge(START, "resolve_mood")
    g.add_edge("resolve_mood", "select_game")
    g.add_edge("select_game", "generate")
    g.add_edge("generate", "evaluate")
    g.add_conditional_edges(
        "evaluate",
        _route_after_evaluate,
        {"translate": "translate", "commit": "commit"},
    )
    g.add_edge("translate", "commit")
    g.add_edge("commit", "post")
    g.add_edge("post", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="autopilot")
