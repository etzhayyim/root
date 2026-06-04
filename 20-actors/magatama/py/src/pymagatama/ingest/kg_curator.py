"""KG Curator handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:media-gamers.etzhayyim.com"
SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def now_date() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> Any:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _ollama_json(system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
    base = os.environ.get("OLLAMA_URL", "").rstrip("/")
    if not base:
        raise RuntimeError("kg-curator: OLLAMA_URL not configured")
    out = _post_json(
        f"{base}/v1/chat/completions",
        {
            "model": os.environ.get("OLLAMA_MODEL_EXTRACTION", "gemma4:e4b"),
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "out", "schema": schema}},
            "temperature": 0.6,
            "max_tokens": 3000,
        },
    )
    return json.loads(out["choices"][0]["message"]["content"])


CHAR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "name": {"type": "string"},
                    "name_ja": {"type": "string"},
                    "role": {"type": "string"},
                    "character_class": {"type": "string"},
                    "description": {"type": "string", "maxLength": 280},
                },
                "required": ["slug", "name", "role", "description"],
            },
        }
    },
    "required": ["characters"],
}


def analyze_coverage(targetCount: Any = 12, limit: Any = 40, **_: Any) -> dict[str, Any]:
    target = _int(targetCount, 12)
    rows = _fetch_all(
        """SELECT t.vertex_id AS scope_did, t.title_en, COALESCE(c.cnt, 0) AS current_count
        FROM vertex_game_title t
        LEFT JOIN (
          SELECT title_did, COUNT(*) AS cnt FROM vertex_game_character GROUP BY title_did
        ) c ON c.title_did=t.vertex_id
        WHERE t.release_year >= 1990 AND COALESCE(c.cnt, 0) < %s
        ORDER BY COALESCE(c.cnt, 0) ASC, t.release_year DESC
        LIMIT %s""",
        (target, max(1, min(_int(limit, 40), 200))),
    )
    tasks = [
        {
            "kind": "expand-characters",
            "scope_did": row["scope_did"],
            "title_en": row.get("title_en"),
            "current_count": row.get("current_count"),
            "target_count": target,
        }
        for row in rows
    ]
    return {"tasks_emitted": len(tasks), "target_per_title": target, "tasks": tasks}


def expand_title(scope_did: str = "", target_count: Any = 12, **_: Any) -> dict[str, Any]:
    if not scope_did:
        return {"error": "scope_did required"}
    existing_rows = _fetch_all("SELECT name, character_role, class FROM vertex_game_character WHERE title_did=%s", (scope_did,))
    title_rows = _fetch_all("SELECT title_en, release_year FROM vertex_game_title WHERE vertex_id=%s", (scope_did,))
    if not title_rows:
        return {"skipped": "title not found"}
    need = _int(target_count, 12) - len(existing_rows)
    if need <= 0:
        return {"skipped": "already covered"}
    title = title_rows[0].get("title_en")
    year = title_rows[0].get("release_year")
    existing = ", ".join(f"{r.get('name')} ({r.get('character_role')})" for r in existing_rows)
    out = _ollama_json(
        "You are a knowledge graph generator for media-gamers.etzhayyim.com. Output strict JSON only. Slugs MUST match ^[a-z0-9-]+$.",
        f"Game: \"{title}\" ({year}). Existing characters: {existing or '(none)'}. Generate {need} more canonical characters from this game's universe NOT in the existing list. Include name in English + Japanese (name_ja), role, character_class, and one-sentence description. Output JSON: {{\"characters\":[...]}}.",
        CHAR_SCHEMA,
    )
    inserted = 0
    skipped: list[str] = []
    for raw in out.get("characters", []):
        slug_text = _str(raw.get("slug"))
        if not SLUG_RE.match(slug_text):
            skipped.append(f"bad-slug:{slug_text}")
            continue
        slug = f"did:etzhayyim:gamechar:{slug_text}"
        if _fetch_all("SELECT 1 FROM vertex_game_character WHERE vertex_id=%s LIMIT 1", (slug,)):
            skipped.append(f"dup:{slug_text}")
            continue
        name = _str(raw.get("name"))
        desc = _str(raw.get("description"))
        _execute(
            """INSERT INTO vertex_game_character
            (vertex_id, sensitivity_ord, owner_did, title_did, name, name_ja, character_role, class, first_appearance_title_did, voice_actor_did)
            VALUES (%s,0,%s,%s,%s,%s,%s,%s,%s,NULL)
            ON CONFLICT (vertex_id) DO NOTHING""",
            (slug, OWNER_DID, scope_did, name, _str(raw.get("name_ja")), _str(raw.get("role")), _str(raw.get("character_class")), scope_did),
        )
        handle = f"{slug_text}.media-gamers.etzhayyim.com"
        _execute(
            """INSERT INTO vertex_actor
            (vertex_id, sensitivity_ord, owner_did, did, handle, display_name, name, execution_tier, performer_type, status, category, classification, operator, agent_type, runtime_type, ui_type, country, created_at)
            VALUES (%s,0,%s,%s,%s,%s,%s,'T0','game-character','active','character',%s,'etzhayyim.com','logical','db-only','metadata-only','jp',%s)
            ON CONFLICT (vertex_id) DO NOTHING""",
            (slug, OWNER_DID, slug, handle, name, name, os.environ.get("KG_LLM_TIER", "T0"), now_date()),
        )
        profile = {
            "displayName": name,
            "displayNameJa": _str(raw.get("name_ja")),
            "description": desc,
            "role": _str(raw.get("role")),
            "class": _str(raw.get("character_class")),
            "isBot": True,
            "tier": "T0-llm-generated",
            "category": "game-character",
            "llm_generated": True,
            "llm_model": os.environ.get("OLLAMA_MODEL_EXTRACTION", "gemma4:e4b"),
            "generated_at": now_iso(),
        }
        _execute(
            """INSERT INTO vertex_actor_manifest
            (vertex_id, sensitivity_ord, owner_did, did, name, display_name, description, execution_tier, performer_type, profile_json, status, created_date)
            VALUES (%s,0,%s,%s,%s,%s,%s,'T0','game-character',%s,'active',%s::date)
            ON CONFLICT (vertex_id) DO NOTHING""",
            (slug, OWNER_DID, slug, name, name, desc, json.dumps(profile, ensure_ascii=False), now_date()),
        )
        inserted += 1
    return {"inserted": inserted, "skipped": skipped}


def status(**_: Any) -> dict[str, Any]:
    rows = _fetch_all(
        """SELECT
        (SELECT count(*) FROM vertex_actor_manifest WHERE execution_tier='T0') AS t0_actors,
        (SELECT count(*) FROM vertex_actor_manifest WHERE execution_tier='T0' AND profile_json LIKE '%llm_generated%true%') AS llm_generated,
        (SELECT count(*) FROM vertex_game_character WHERE owner_did=%s) AS game_chars""",
        (OWNER_DID,),
    )
    row = rows[0] if rows else {}
    return {"status": "alive", "linode_gpu": os.environ.get("OLLAMA_URL", ""), **row}
