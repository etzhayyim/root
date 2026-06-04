"""
common-crawl entity extraction — Zeebe primitive.

Runs URL-regex fast-path (no LLM) and OpenRouter LLM fallback
to extract structured entities from vertex_page rows, then writes
results to domain state tables.

Env vars:
  SS_OPENROUTER_API_KEY   OpenRouter API key
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request as _req
from typing import Any

from pymagatama.db_sync import sync_cursor

_OPENROUTER_KEY = os.environ.get("SS_OPENROUTER_API_KEY", "").strip()
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_OPENROUTER_MODEL = "anthropic/claude-3-haiku"

# ---------------------------------------------------------------------------
# Domain config
# ---------------------------------------------------------------------------

_DOMAINS: dict[str, dict[str, Any]] = {
    "kuruma": {
        "domains": [
            "wheelsage.org", "www.edmunds.com", "www.kbb.com",
            "www.caranddriver.com", "www.motortrend.com", "www.autoblog.com",
            "www.toyota.com", "www.honda.com", "www.bmw.com", "www.ford.com",
            "www.nissan.com", "www.audi.com", "www.mercedes-benz.com",
            "www.tesla.com", "www.hyundai.com", "www.mazdausa.com",
            "www.subaru.com", "www.porsche.com",
        ],
        "collection": "com.etzhayyim.apps.kuruma.model",
        "repo": "did:web:kuruma.etzhayyim.com",
        "entity_key": "model_name",
    },
    "media_anime": {
        "domains": [
            "myanimelist.net", "anilist.co", "anidb.net",
            "kitsu.io", "anime-planet.com", "livechart.me", "notify.moe",
        ],
        "collection": "com.etzhayyim.apps.media_anime.title",
        "repo": "did:web:media-anime.etzhayyim.com",
        "entity_key": "title",
    },
    "media_gamers": {
        "domains": [
            "store.steampowered.com", "www.mobygames.com", "www.igdb.com",
            "www.metacritic.com", "www.gamespot.com", "www.ign.com",
            "www.nintendo.com", "www.playstation.com", "www.xbox.com",
            "store.epicgames.com", "www.gog.com",
        ],
        "collection": "com.etzhayyim.apps.media_gamers.title",
        "repo": "did:web:media-gamers.etzhayyim.com",
        "entity_key": "title",
    },
    "handotai": {
        "domains": [
            "en.wikichip.org", "www.anandtech.com", "ark.intel.com",
            "www.amd.com", "www.nvidia.com", "developer.arm.com",
            "www.tomshardware.com", "semiwiki.com",
        ],
        "collection": "com.etzhayyim.apps.handotai.chip",
        "repo": "did:web:handotai.etzhayyim.com",
        "entity_key": "name",
    },
}

# ---------------------------------------------------------------------------
# URL regex fast-path (Path D)
# ---------------------------------------------------------------------------

_URL_PATTERNS: dict[str, list[dict[str, Any]]] = {
    "media_gamers": [
        {"re": re.compile(r"store\.steampowered\.com/app/(\d+)/([^/?#]+)", re.I), "idx": 2, "meta": {"store": "steam"}},
        {"re": re.compile(r"mobygames\.com/game/(?:[^/]+/)?([^/?#]+)", re.I), "idx": 1, "meta": {"store": "mobygames"}},
        {"re": re.compile(r"metacritic\.com/game/(?:[^/]+/)?([^/?#]+)", re.I), "idx": 1},
        {"re": re.compile(r"gamespot\.com/games/([^/?#]+)", re.I), "idx": 1},
        {"re": re.compile(r"nintendo\.com/store/products/([^/?#]+)", re.I), "idx": 1, "meta": {"store": "nintendo"}},
        {"re": re.compile(r"playstation\.com/[a-z-]+/games/([^/?#]+)", re.I), "idx": 1, "meta": {"store": "playstation"}},
        {"re": re.compile(r"xbox\.com/[a-z-]+/games/store/([^/?#]+)", re.I), "idx": 1, "meta": {"store": "xbox"}},
        {"re": re.compile(r"gog\.com/game/([^/?#]+)", re.I), "idx": 1, "meta": {"store": "gog"}},
        {"re": re.compile(r"epicgames\.com/store/[a-z-]+/p/([^/?#]+)", re.I), "idx": 1, "meta": {"store": "epic"}},
    ],
    "media_anime": [
        {"re": re.compile(r"myanimelist\.net/anime/(\d+)/([^/?#]+)", re.I), "idx": 2, "meta": {"source": "mal"}},
        {"re": re.compile(r"anilist\.co/anime/(\d+)/([^/?#]+)", re.I), "idx": 2, "meta": {"source": "anilist"}},
        {"re": re.compile(r"anidb\.net/anime/(\d+)/([^/?#]*)", re.I), "idx": 2, "meta": {"source": "anidb"}},
        {"re": re.compile(r"kitsu\.io/anime/([^/?#]+)", re.I), "idx": 1, "meta": {"source": "kitsu"}},
        {"re": re.compile(r"anime-planet\.com/anime/([^/?#]+)", re.I), "idx": 1, "meta": {"source": "anime-planet"}},
    ],
    "kuruma": [
        {"re": re.compile(r"wheelsage\.org/([^/]+)/([^/?#]+)", re.I), "idx": 2, "maker_idx": 1},
        {"re": re.compile(r"www\.(toyota|honda|bmw|ford|nissan|audi|tesla|hyundai|mazdausa|subaru|porsche)\.com/[^?#]*?([a-z0-9-]{3,40})/?$", re.I), "idx": 2, "maker_idx": 1},
    ],
    "handotai": [
        {"re": re.compile(r"en\.wikichip\.org/wiki/[^/]+/(?:[^/]+/)?([^/?#]+)$", re.I), "idx": 1},
        {"re": re.compile(r"ark\.intel\.com/content/[^?#]*/products/\d+/([^./?#]+)\.html", re.I), "idx": 1, "meta": {"manufacturer": "Intel"}},
        {"re": re.compile(r"amd\.com/en/products/[^/]+/(?:[^/]+/)?([^/?#]+)", re.I), "idx": 1, "meta": {"manufacturer": "AMD"}},
        {"re": re.compile(r"nvidia\.com/en-us/geforce/graphics-cards/[^/]+/([^/?#]+)", re.I), "idx": 1, "meta": {"manufacturer": "NVIDIA"}},
    ],
}

_ENTITY_KEY_MAP = {
    "kuruma":       "model_name",
    "media_anime":  "title",
    "media_gamers": "title",
    "handotai":     "name",
}


def _fast_extract(url: str, domain: str) -> dict[str, str] | None:
    for pat in _URL_PATTERNS.get(domain, []):
        m = pat["re"].search(url)
        if not m:
            continue
        idx = pat["idx"]
        groups = m.groups()
        if idx > len(groups) or not groups[idx - 1]:
            continue
        slug_raw = groups[idx - 1]
        if len(slug_raw) < 2:
            continue
        name = re.sub(r"[_+\-]+", " ", slug_raw).strip()
        if not name:
            continue
        out: dict[str, str] = {"name": name, "slug": slug_raw}
        if "meta" in pat:
            out.update(pat["meta"])
        maker_idx = pat.get("maker_idx")
        if maker_idx and len(groups) >= maker_idx:
            out["maker"] = groups[maker_idx - 1] or ""
        return out
    return None


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _prompt(domain: str, url: str, title: str, description: str) -> str:
    slug_hint = _url_slug(url)
    desc = (description or "")[:800]
    if domain == "kuruma":
        schema = '{"model_name": string|null, "maker": string|null, "year": int|null, "body_type": string|null, "country": string|null}'
        topic = "automobile model"
        null_key = "model_name"
    elif domain == "media_anime":
        schema = '{"title": string|null, "title_ja": string|null, "studio": string|null, "year": int|null, "type": "TV"|"OVA"|"Movie"|null}'
        topic = "anime title"
        null_key = "title"
    elif domain == "media_gamers":
        schema = '{"title": string|null, "developer": string|null, "publisher": string|null, "year": int|null, "platform": string|null, "genre": string|null}'
        topic = "video game title"
        null_key = "title"
    else:  # handotai
        schema = '{"name": string|null, "manufacturer": string|null, "process_nm": int|null, "category": "CPU"|"GPU"|"SoC"|"memory"|"MCU"|"ASIC"|null, "year": int|null}'
        topic = "semiconductor chip/component"
        null_key = "name"
    return (
        f"Extract the {topic} described on this page. Return JSON only:\n"
        f"{schema}\n"
        f'If not about a specific {topic}, return {{"{null_key}": null}}.\n\n'
        f"URL: {url}\nTitle: {title}\nDescription: {desc}\nURL slug hint: {slug_hint}"
    )


def _url_slug(url: str) -> str:
    try:
        from urllib.parse import urlparse, unquote
        p = urlparse(url)
        segs = [s for s in p.path.split("/") if s]
        for s in reversed(segs):
            if not re.match(r"^\d+$", s) and len(s) > 2:
                return re.sub(r"[-_]+", " ", unquote(s)).strip()
        return " ".join(segs)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# OpenRouter LLM call (Path A)
# ---------------------------------------------------------------------------

def _openrouter_extract(domain: str, url: str, title: str, description: str) -> dict[str, Any] | None:
    if not _OPENROUTER_KEY:
        return None
    prompt_text = _prompt(domain, url, title or "", description or "")
    payload = json.dumps({
        "model": _OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }).encode()
    req = _req.Request(_OPENROUTER_URL, data=payload, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_OPENROUTER_KEY}",
        "HTTP-Referer": "https://cc26m4x1.etzhayyim.com",
        "X-Title": "etzhayyim-common-crawl",
    })
    try:
        with _req.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read())
        raw = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        content = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.I)
        content = re.sub(r"\s*```\s*$", "", content).strip()
        return json.loads(content)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Zeebe task
# ---------------------------------------------------------------------------

def _get_cursor(dom: str) -> str:
    """Return last processed vertex_id for this domain ('' = start from beginning)."""
    try:
        with sync_cursor() as cur:
            cur.execute(
                "SELECT last_vertex_id FROM vertex_cc_entity_cursor WHERE domain = %s",
                [dom],
            )
            row = cur.fetchone()
            return row[0] if row else ""
    except Exception:
        return ""


def _set_cursor(dom: str, last_vertex_id: str) -> None:
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_cc_entity_cursor (domain, last_vertex_id, updated_at)
                VALUES (%s, %s, %s)
                """,
                [dom, last_vertex_id, now_iso],
            )
    except Exception:
        pass


def _write_entity_record(cur: Any, *, dom: str, cfg: dict[str, Any], rec: dict[str, Any], now_iso: str) -> None:
    uri = f"at://{cfg['repo']}/{cfg['collection']}/{rec['rkey']}"
    value = {"$type": cfg["collection"], **rec["value"]}
    name = str(rec["value"].get(cfg["entity_key"]) or rec["value"].get("name") or rec["value"].get("title") or "")[:512]
    source = str(rec["value"].get("_source") or "")

    if dom == "kuruma":
        cur.execute(
            """
            INSERT INTO vertex_kuruma_model
              (vertex_id, _seq, created_date, sensitivity_ord, owner_did, name, wikidata_qid)
            VALUES (%s, 0, %s, 300, %s, %s, %s)
            ON CONFLICT (vertex_id) DO UPDATE SET name = EXCLUDED.name, wikidata_qid = EXCLUDED.wikidata_qid
            """,
            (uri, now_iso[:10], cfg["repo"], name, str(rec["value"].get("wikidata_qid") or "")),
        )
        return

    if dom == "media_anime":
        cur.execute(
            """
            INSERT INTO vertex_anime_title
              (vertex_id, _seq, created_date, sensitivity_ord, owner_did, external_ids, title_en, title_ja, type, status)
            VALUES (%s, 0, %s, 300, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (vertex_id) DO UPDATE SET title_en = EXCLUDED.title_en, external_ids = EXCLUDED.external_ids
            """,
            (uri, now_iso[:10], cfg["repo"], source, name, str(rec["value"].get("title_ja") or ""), str(rec["value"].get("type") or ""), str(rec["value"].get("status") or "")),
        )
        return

    if dom == "media_gamers":
        cur.execute(
            """
            INSERT INTO vertex_game_title
              (vertex_id, _seq, created_date, sensitivity_ord, owner_did, external_ids, title_en, title_ja)
            VALUES (%s, 0, %s, 300, %s, %s, %s, %s)
            ON CONFLICT (vertex_id) DO UPDATE SET title_en = EXCLUDED.title_en, external_ids = EXCLUDED.external_ids
            """,
            (uri, now_iso[:10], cfg["repo"], source, name, str(rec["value"].get("title_ja") or "")),
        )
        return

    if dom == "handotai":
        value_json = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        source_url = str(rec["value"].get("_source_url") or "")
        source_page_did = str(rec["value"].get("_source_page_did") or "")
        manufacturer = str(rec["value"].get("manufacturer") or rec["value"].get("vendor") or "")
        family = str(rec["value"].get("product_family") or rec["value"].get("family") or rec["value"].get("series") or "")
        cur.execute(
            """
            INSERT INTO vertex_handotai_chip
              (vertex_id, chip_id, name, manufacturer, product_family,
               source_url, source_title, source_domain, value_json,
               indexed_at, created_at, updated_at, actor_did, org_did,
               owner_did, sensitivity_ord)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 300)
            ON CONFLICT (vertex_id) DO UPDATE SET
              name = EXCLUDED.name,
              manufacturer = EXCLUDED.manufacturer,
              product_family = EXCLUDED.product_family,
              source_url = EXCLUDED.source_url,
              value_json = EXCLUDED.value_json,
              indexed_at = EXCLUDED.indexed_at,
              updated_at = EXCLUDED.updated_at
            """,
            (
                uri,
                rec["rkey"],
                name,
                manufacturer,
                family,
                source_url,
                str(rec["value"].get("title") or ""),
                source,
                value_json,
                now_iso,
                now_iso,
                now_iso,
                cfg["repo"],
                "anon",
                cfg["repo"],
            ),
        )
        if source_page_did:
            edge_id = "edge:handotai:chip_source_page:" + hashlib.sha256(f"{uri}|{source_page_did}".encode()).hexdigest()[:24]
            cur.execute(
                """
                INSERT INTO edge_handotai_chip_source_page
                  (edge_id, from_vertex_id, to_vertex_id, chip_id, source_url, relation, created_at)
                VALUES (%s, %s, %s, %s, %s, 'extracted_from', %s)
                ON CONFLICT (edge_id) DO UPDATE SET source_url = EXCLUDED.source_url
                """,
                (edge_id, uri, source_page_did, rec["rkey"], source_url, now_iso),
            )
        return

    raise ValueError(f"unsupported common-crawl entity domain: {dom!r}")


def task_common_crawl_extract_entities(
    domain: str = "",
    limit: int = 15,
) -> dict[str, Any]:
    """
    Extract structured entities from vertex_page rows using cursor-based pagination.

    Avoids IS NULL scan on a 985M-row table; uses vertex_id > last_cursor ORDER BY
    vertex_id with the domain index (INCLUDE vertex_id) instead.
    When domain is empty (timer-start), processes all 4 domains in sequence.
    Returns {processed, extracted, domain, status}.
    """
    domains_to_run = list(_DOMAINS.keys()) if not domain else [domain]

    if domain and domain not in _DOMAINS:
        raise ValueError(f"unknown domain: {domain!r}")

    limit = max(1, min(30, limit or 15))
    total_processed = 0
    total_extracted = 0
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for dom in domains_to_run:
        cfg = _DOMAINS[dom]
        domain_list = ", ".join(f"'{d.replace(chr(39), chr(39)+chr(39))}'" for d in cfg["domains"])
        cursor = _get_cursor(dom)

        with sync_cursor() as cur:
            cur.execute(
                f"""
                SELECT vertex_id, url, title, description
                FROM vertex_page
                WHERE domain IN ({domain_list})
                  AND vertex_id > %s
                ORDER BY vertex_id ASC
                LIMIT {int(limit)}
                """,
                [cursor],
            )
            rows = cur.fetchall()

        # If no rows after cursor, wrap around to beginning
        if not rows and cursor:
            _set_cursor(dom, "")
            continue

        if not rows:
            continue

        valid_records = []
        for row in rows:
            vertex_id, url, title, description = row

            fast = _fast_extract(url, dom)
            if fast:
                entity_key = _ENTITY_KEY_MAP[dom]
                rkey = hashlib.sha256(vertex_id.encode()).hexdigest()[:16]
                rkey = f"cc-{dom[:8]}-{rkey}"
                valid_records.append({
                    "rkey": rkey,
                    "value": {entity_key: fast["name"], **fast, "_source": "url-regex", "_source_url": url, "_source_page_did": vertex_id},
                })
                continue

            parsed = _openrouter_extract(dom, url, title or "", description or "")
            if parsed is None:
                continue
            key_val = parsed.get(cfg["entity_key"])
            if not isinstance(key_val, str) or not key_val:
                continue
            rkey = hashlib.sha256(vertex_id.encode()).hexdigest()[:16]
            rkey = f"cc-{dom[:8]}-{rkey}"
            valid_records.append({
                "rkey": rkey,
                "value": {**parsed, "_source": "openrouter-haiku", "_source_url": url, "_source_page_did": vertex_id},
            })

        # Write entity records to domain state tables.
        if valid_records:
            with sync_cursor() as cur:
                for rec in valid_records:
                    _write_entity_record(cur, dom=dom, cfg=cfg, rec=rec, now_iso=now_iso)

        # Advance cursor to max vertex_id processed this batch
        _set_cursor(dom, rows[-1][0])

        total_processed += len(rows)
        total_extracted += len(valid_records)

    return {
        "processed":   total_processed,
        "extracted":   total_extracted,
        "domain":      domain or "all",
        "status":      "ok",
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(worker: Any, *, timeout_ms: int) -> None:
    worker.task(
        task_type="commonCrawl.entities.extract",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_common_crawl_extract_entities)


__all__ = ["register", "task_common_crawl_extract_entities"]
