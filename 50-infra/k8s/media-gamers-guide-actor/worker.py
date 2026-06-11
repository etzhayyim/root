"""LangServer actor for media-gamers.etzhayyim.com guide generation.

The actor owns expensive/long-running work: LLM guide writing, translation,
quality scoring, and social-post drafting. Cloudflare app.ts only commits the
records and posts via com.etzhayyim.apps.media_gamers.guide.commitGuide.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
import uvicorn


LOG = logging.getLogger("media-gamers-guide-actor")
AGENTGATEWAY_MCP_URL = os.environ.get(
    "AGENTGATEWAY_MCP_URL",
    "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
)
PORT = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))
TOOLS = {
    "mediaGamers.guide.resolveTargets",
    "mediaGamers.guide.generate",
    "mediaGamers.knowledge.generateGuide",
    "mediaGamers.eval.models",
}

TARGET_LANGS = ["ja", "zh", "es", "ar", "hi", "ko"]
GUIDE_TYPES = {"boss-guide", "weapon-guide", "beginner-guide", "tier-list"}

SEED_GAMES = [
    {
        "slug": "elden-ring",
        "name": "Elden Ring",
        "synopsis": "Open-world action RPG set in the Lands Between, featuring challenging combat and deep lore.",
        "developer": "fromsoftware",
        "publisher": "bandai-namco",
        "platforms": ["PS5", "Xbox Series X", "PC"],
        "genre": "action-rpg",
        "releaseYear": 2022,
    },
    {
        "slug": "pokemon-legends-z-a",
        "name": "Pokémon Legends: Z-A",
        "synopsis": "Mainline Pokemon action RPG set in Lumiose City.",
        "developer": "game-freak",
        "publisher": "the-pokemon-company",
        "platforms": ["Switch", "Switch 2"],
        "genre": "creature-rpg",
        "releaseYear": 2025,
    },
    {
        "slug": "pokoa-world",
        "name": "Pokoa World",
        "synopsis": "etzhayyim original creature-collector RPG blending surreal meme aesthetics and community-driven evolution paths.",
        "developer": "etzhayyim-studio",
        "publisher": "etzhayyim",
        "platforms": ["PC", "Mobile"],
        "genre": "creature-rpg",
        "releaseYear": 2026,
    },
]


def configure_logging() -> None:
    if LOG.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def sanitize_rkey(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned[:128] or "unset"


def normalize_guide_type(value: Any) -> str:
    guide_type = str(value or "beginner-guide")
    return guide_type if guide_type in GUIDE_TYPES else "beginner-guide"


def game_by_slug(slug: str) -> dict[str, Any] | None:
    return next((game for game in SEED_GAMES if game["slug"] == slug), None)


def resolve_targets(slug: str = "", guide_type: str = "", offset: int = 0, limit: int = 1, **extra: Any) -> list[dict[str, Any]]:
    selected_type = normalize_guide_type(guide_type)
    if slug:
        game = game_by_slug(sanitize_rkey(slug))
        return [{**game, "guideType": selected_type, **extra}] if game else []
    start = max(0, int(offset or 0))
    count = max(1, min(int(limit or 1), 20))
    return [{**game, "guideType": selected_type, **extra} for game in SEED_GAMES[start : start + count]]


def build_prompt(game: dict[str, Any], guide_type: str) -> str:
    ip_prefix = ""
    if game["slug"] == "pokoa-world":
        ip_prefix = (
            f"Game description: {game['synopsis']}\n"
            "Use only this description for factual claims. Clearly label speculative mechanics.\n\n"
        )
    structures = {
        "boss-guide": "overview, preparation, phase-by-phase tactics, pro tips, common mistakes",
        "weapon-guide": "tier list, top weapon breakdowns, builds, matchups, upgrade priority",
        "beginner-guide": "first 30 minutes, core systems, common mistakes, early checklist, pacing advice",
        "tier-list": "S/A/B/C/D entries, role, strengths, weaknesses, team composition, recommended build",
    }
    return (
        f"{ip_prefix}Write a useful gaming guide for {game['name']} "
        f"({game['genre']}, {game['releaseYear']}).\n"
        f"Guide type: {guide_type}.\n"
        f"Required structure: {structures[guide_type]}.\n"
        "Use concrete headings, avoid filler, and make advice actionable for players.\n"
        "Return article body only. Target 900-1400 words."
    )


async def openai_chat(url: str, api_key: str, model: str, prompt: str, max_tokens: int = 2048) -> str:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["x-api-key"] = api_key
    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        res = await client.post(
            url,
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": max_tokens,
                "stream": False,
            },
        )
    res.raise_for_status()
    data = res.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return re.sub(r"<think>[\s\S]*?</think>", "", str(content)).strip()


async def llm(prompt: str, max_tokens: int = 2048) -> str:
    murakumo_url = os.environ.get("MURAKUMO_OPENAI_URL", "https://murakumo.etzhayyim.com/api/openai/v1/chat/completions")
    murakumo_key = os.environ.get("MURAKUMO_API_KEY", "")
    murakumo_model = os.environ.get("MURAKUMO_MODEL", "qwen3.5-4b")
    try:
        return await openai_chat(murakumo_url, murakumo_key, murakumo_model, prompt, max_tokens)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("murakumo call failed, trying fallback: %s", exc)
    runpod_url = os.environ.get("RUNPOD_OPENAI_URL", "")
    runpod_key = os.environ.get("RUNPOD_API_KEY", "")
    if runpod_url:
        return await openai_chat(runpod_url, runpod_key, os.environ.get("RUNPOD_MODEL", "gemma4:26b-a4b-it-q4_K_M"), prompt, max_tokens)
    raise RuntimeError("no LLM backend available")


def fallback_body(game: dict[str, Any], guide_type: str) -> str:
    return (
        f"# {game['name']} {guide_type}\n\n"
        f"{game['name']} is a {game['genre']} title. This fallback guide is generated without model access.\n\n"
        "## Start here\n"
        "Learn the core loop before optimizing. Spend the first session mapping controls, safe resources, and failure states.\n\n"
        "## Practical checklist\n"
        "- Identify one reliable defensive option.\n"
        "- Upgrade only tools that support your main route.\n"
        "- Revisit difficult encounters after each meaningful unlock.\n\n"
        "## Player value\n"
        "The goal is to reduce wasted time and help new players find a stable path into the game."
    )


def render_graph(graph: dict[str, Any]) -> str:
    return str(graph)[:8000]


def fallback_knowledge_guide(graph: dict[str, Any]) -> dict[str, str]:
    title = "ぽこあポケモン攻略: Pokemon Legends: Z-A を Knowledge Graph から読む完全ガイド"
    body = (
        "## 結論\n"
        "「pokoa pokemon」「ぽこあポケモン」は Pokemon Legends: Z-A に正規化して扱う。\n\n"
        "## Knowledge Graph の読み方\n"
        "作品、開発元、発売元、プラットフォーム、確認済みソースを分けて扱うことで、検索意図と攻略記事の根拠が混ざらない。\n\n"
        "## 攻略の軸\n"
        "Lumiose City、Mega Evolution、Z-A Royale を中核ノードとして読み、昼の準備と夜の連戦を分けて計画する。\n\n"
        "## 序盤チェックリスト\n"
        "- 主要施設を開放する\n"
        "- 戦闘距離と回避タイミングを確認する\n"
        "- Mega Evolution を切る勝ち筋を決める\n"
        "- Switch / Switch 2 の版差と購入導線を確認する\n\n"
        "## Graph snapshot\n"
        f"{render_graph(graph)[:1800]}"
    )
    return {"title": title, "body": body}


async def generate_body(game: dict[str, Any], guide_type: str) -> str:
    try:
        body = await llm(build_prompt(game, guide_type), 2200)
        if len(body) >= 400:
            return body
    except Exception as exc:  # noqa: BLE001
        LOG.warning("guide LLM failed slug=%s guideType=%s error=%s", game["slug"], guide_type, exc)
    return fallback_body(game, guide_type)


async def generate_knowledge_guide(graph: dict[str, Any]) -> dict[str, str]:
    title = "ぽこあポケモン攻略: Pokemon Legends: Z-A を Knowledge Graph から読む完全ガイド"
    prompt = (
        "Write a long-form Japanese strategy article for Pokemon Legends: Z-A.\n"
        "Use only confirmed facts in the graph for factual claims. Label strategy implications as inferred.\n"
        "Explain that the search intent 'pokoa pokemon' normalizes to Pokemon Legends: Z-A.\n"
        "Cover canonical identification, platforms, release status, Lumiose City, Mega Evolution, Z-A Royale, "
        "day/night preparation loop, first-session checklist, and practical progression route.\n"
        "Return article body only, with clear headings and no filler. Target 1800+ Japanese characters.\n\n"
        f"Knowledge graph:\n{render_graph(graph)}"
    )
    try:
        body = await llm(prompt, 4096)
        if len(body) >= 400:
            return {"title": title, "body": body}
    except Exception as exc:  # noqa: BLE001
        LOG.warning("knowledge guide generation failed: %s", exc)
    return fallback_knowledge_guide(graph)


async def evaluate_model() -> dict[str, Any]:
    test_prompt = (
        "Write a boss guide for Elden Ring's Malenia fight. Include recommended level, weapon builds, "
        "phase breakdown with attack patterns. 500 words."
    )
    article = await llm(test_prompt, 1024)
    eval_prompt = (
        "Rate this gaming guide on 5 axes (0-20 each, 100 total). Return JSON only:\n"
        '{"accuracy":N,"detail_depth":N,"structure":N,"actionability":N,"game_term_precision":N,"total":N,"notes":"..."}\n\n'
        f"Article:\n{article[:2000]}"
    )
    raw_eval = await llm(eval_prompt, 512)
    scores: dict[str, Any] = {}
    try:
        import json

        parsed = json.loads(raw_eval)
        if isinstance(parsed, dict):
            scores = parsed
    except Exception:  # noqa: BLE001
        scores = {"raw": raw_eval}
    return {
        "model": os.environ.get("MURAKUMO_MODEL", "qwen3.5-4b"),
        "scores": scores,
        "rawEval": raw_eval,
        "articlePreview": article[:500],
    }


async def translate_text(text: str, lang: str, game_name: str) -> str:
    prompt = (
        f"Translate this gaming guide content into {lang}. Preserve headings, concrete game terms, and URLs. "
        f"Context game: {game_name}. Return only the translation.\n\n{text}"
    )
    try:
        translated = await llm(prompt, 2200)
        return translated if len(translated) >= 20 else ""
    except Exception as exc:  # noqa: BLE001
        LOG.warning("translation failed lang=%s game=%s error=%s", lang, game_name, exc)
        return ""


def quality_score(body: str) -> float:
    length_score = min(1.0, len(body) / 4000)
    heading_score = 1.0 if re.search(r"(^|\n)#{1,3}\s+", body) else 0.4
    checklist_score = 1.0 if "-" in body or re.search(r"\n\d+\.", body) else 0.5
    return round((length_score * 0.45 + heading_score * 0.30 + checklist_score * 0.25) * 100, 1)


def title_for(game: dict[str, Any], guide_type: str) -> str:
    labels = {
        "boss-guide": "Boss Strategy Guide",
        "weapon-guide": "Weapon Tier & Build Guide",
        "beginner-guide": "Beginner's Complete Guide",
        "tier-list": "Character/Class Tier List",
    }
    return f"{game['name']} - {labels[guide_type]}"


def social_post(title: str, body: str, game: dict[str, Any], guide_type: str, lang: str = "en") -> str:
    url = f"https://media-gamers.etzhayyim.com/{lang}/game/{game['slug']}/{guide_type}"
    compact = re.sub(r"\s+", " ", body).strip()
    teaser = compact[:220]
    return f"{title}\n\n{teaser}\n\n#{game['genre']} #gaming #{guide_type}\n{url}"


async def commit_guide(payload: dict[str, Any]) -> dict[str, Any]:
    url = os.environ.get(
        "MEDIA_GAMERS_COMMIT_GUIDE_URL",
        "https://media-gamers.etzhayyim.com/xrpc/com.etzhayyim.apps.media_gamers.guide.commitGuide",
    )
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        res = await client.post(url, json=payload)
    if res.status_code >= 400:
        raise RuntimeError(f"commitGuide {res.status_code}: {res.text[:500]}")
    return res.json()


async def post_xrpc(env_name: str, default_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = os.environ.get(env_name, default_url)
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        res = await client.post(url, json=payload)
    if res.status_code >= 400:
        raise RuntimeError(f"{env_name} {res.status_code}: {res.text[:500]}")
    return res.json()


async def resolve_guide_targets(
    slug: str = "",
    guideType: str = "",
    offset: int = 0,
    limit: int = 1,
    userId: str = "",
    mood: str = "",
    **_: Any,
) -> dict[str, Any]:
    targets = resolve_targets(slug, guideType, offset, limit, userId=userId, mood=mood)
    return {"targets": targets, "total": len(targets)}


async def generate_guides(
    targets: list[dict[str, Any]] | None = None,
    translate: bool = True,
    publish: bool = True,
    **_: Any,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for target in targets or []:
        try:
            guide_type = normalize_guide_type(target.get("guideType"))
            body = await generate_body(target, guide_type)
            title = title_for(target, guide_type)
            translations: list[dict[str, Any]] = []
            if translate is not False:
                for lang in TARGET_LANGS:
                    tr_title = await translate_text(title, lang, target["name"])
                    tr_body = await translate_text(body, lang, target["name"])
                    if tr_title and tr_body:
                        translations.append(
                            {
                                "lang": lang,
                                "title": tr_title,
                                "body": tr_body,
                                "qualityScore": quality_score(tr_body),
                                "socialPost": social_post(tr_title, tr_body, target, guide_type, lang),
                            }
                        )
            commit = await commit_guide(
                {
                    "slug": sanitize_rkey(f"{target['slug']}-{guide_type}"),
                    "gameSlug": target["slug"],
                    "gameName": target["name"],
                    "guideType": guide_type,
                    "lang": "en",
                    "title": title,
                    "body": body,
                    "qualityScore": quality_score(body),
                    "generatedBy": "media-gamers-guide-actor",
                    "requestedBy": target.get("userId") or "",
                    "socialPost": social_post(title, body, target, guide_type),
                    "publish": publish,
                    "translations": translations,
                }
            )
            results.append({"slug": target["slug"], "guideType": guide_type, "ok": True, "commit": commit})
        except Exception as exc:  # noqa: BLE001
            LOG.exception("guide generation failed target=%s", target.get("slug"))
            results.append({"slug": target.get("slug", ""), "ok": False, "error": str(exc)})
    return {"results": results}


async def generate_knowledge(
    graph: dict[str, Any] | None = None,
    postAsGameDid: bool = True,
    publish: bool = True,
    sourceQuery: str = "pokoa pokemon",
    **_: Any,
) -> dict[str, Any]:
    guide = await generate_knowledge_guide(graph or {})
    commit = await post_xrpc(
        "MEDIA_GAMERS_COMMIT_KNOWLEDGE_GUIDE_URL",
        "https://media-gamers.etzhayyim.com/xrpc/com.etzhayyim.apps.media_gamers.knowledge.commitKnowledgeGuide",
        {
            "graph": graph or {},
            "title": guide["title"],
            "body": guide["body"],
            "postAsGameDid": postAsGameDid,
            "publish": publish,
            "sourceQuery": sourceQuery,
            "generatedBy": "media-gamers-guide-actor",
        },
    )
    return {"result": commit}


async def eval_models(**_: Any) -> dict[str, Any]:
    evaluation = await evaluate_model()
    commit = await post_xrpc(
        "MEDIA_GAMERS_COMMIT_MODEL_EVALUATION_URL",
        "https://media-gamers.etzhayyim.com/xrpc/com.etzhayyim.apps.media_gamers.commitModelEvaluation",
        {**evaluation, "generatedBy": "media-gamers-guide-actor"},
    )
    return {"result": commit}


app = FastAPI(title="media-gamers-guide-actor", version="1.0.0")


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "runtimeKind": "k8s-langserver",
        "agentGatewayMcpUrl": AGENTGATEWAY_MCP_URL,
        "tools": sorted(TOOLS),
    }


@app.get("/tools")
async def tools() -> dict[str, Any]:
    return {"tools": [{"name": name, "runtime": "langserver"} for name in sorted(TOOLS)]}


async def _invoke_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "mediaGamers.guide.resolveTargets":
        return await resolve_guide_targets(**arguments)
    if name == "mediaGamers.guide.generate":
        return await generate_guides(**arguments)
    if name == "mediaGamers.knowledge.generateGuide":
        return await generate_knowledge(**arguments)
    if name == "mediaGamers.eval.models":
        return await eval_models(**arguments)
    raise HTTPException(status_code=404, detail=f"unknown tool: {name}")


@app.post("/invoke")
async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or payload.get("tool") or "")
    arguments = payload.get("arguments") or payload.get("input") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="arguments must be an object")
    return {"ok": True, "name": name, "result": await _invoke_tool(name, arguments)}


@app.post("/runs")
async def runs(payload: dict[str, Any]) -> dict[str, Any]:
    assistant_id = str(payload.get("assistant_id") or "")
    arguments = payload.get("input") or payload.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="input must be an object")
    return {"status": "completed", "assistant_id": assistant_id, "output": await _invoke_tool(assistant_id, arguments)}


if __name__ == "__main__":
    configure_logging()
    LOG.info("media-gamers-guide-actor starting, runtime=k8s-langserver, agentgateway_mcp_url=%s", AGENTGATEWAY_MCP_URL)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
