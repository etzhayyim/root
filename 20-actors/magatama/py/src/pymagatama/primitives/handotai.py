"""handotai semiconductor intelligence primitives (ADR-0056 BPMN-as-actor).

3 Zeebe task types for handotai.etzhayyim.com:
  handotai.seed.writers    — idempotent upsert of 6 built-in RSS writer sources
  handotai.collect.rssAll  — fetch all enabled sources, parse items, write articles
  handotai.generate.digest — read today's articles, LLM-summarize, write digest

Tables: vertex_handotai_source / vertex_handotai_article / vertex_handotai_digest
"""

from __future__ import annotations

import hashlib
import re
import time
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp

from pymagatama import llm as _llm
from pymagatama.db_sync import sync_cursor


_OWNER_DID = "did:web:handotai.etzhayyim.com"
_COL_SRC = "app.etzhayyim.apps.handotai.source"
_COL_ART = "app.etzhayyim.apps.handotai.article"
_COL_DIG = "app.etzhayyim.apps.handotai.digest"

_WRITERS: list[dict[str, str]] = [
    {"source_id": "src-pcw",  "name": "PC Watch",                  "url": "https://pc.watch.impress.co.jp/data/rss/1.0/pcw/feed.rdf", "language": "ja", "category": "fabrication"},
    {"source_id": "src-itm",  "name": "ITmedia NEWS",               "url": "https://rss.itmedia.co.jp/rss/2.0/newsBursts.xml",         "language": "ja", "category": "market"},
    {"source_id": "src-pubk", "name": "Publickey",                  "url": "https://www.publickey1.jp/atom.xml",                       "language": "ja", "category": "design"},
    {"source_id": "src-semia","name": "SemiAnalysis",               "url": "https://www.semianalysis.com/feed",                        "language": "en", "category": "market"},
    {"source_id": "src-semie","name": "Semiconductor Engineering",  "url": "https://semiengineering.com/feed/",                        "language": "en", "category": "design"},
    {"source_id": "src-eet",  "name": "EE Times",                   "url": "https://www.eetimes.com/feed/",                            "language": "en", "category": "market"},
]

# Semiconductor keyword → category hint (used for fast T1 categorisation)
_CAT_KEYWORDS: list[tuple[list[str], str]] = [
    (["tsmc", "samsung", "intel foundry", "globalfoundries", "smic", "rapidus", "foundry", "fab ", "node", "nm "], "fabrication"),
    (["dram", "hbm", "nand", "memory", "kioxia", "micron", "sk hynix", "flash"], "materials"),
    (["asml", "applied materials", "tokyo electron", "lam research", "kla", "screen holdings", "lasertec", "disco"], "equipment"),
    (["arm", "cadence", "synopsys", "siemens eda", "eda ", "ip core", "risc-v", "verilog", "rtl "], "design"),
    (["supply chain", "chip shortage", "export control", "tariff", "trade"], "supply_chain"),
    (["gpu", "ai chip", "ai accelerator", "nvidia", "amd ", "tpu", "npu", "inference", "training"], "market"),
    (["automotive", "ev ", "electric vehicle", "power device", "sic ", "gan "], "market"),
    (["policy", "chips act", "government", "subsidy", "経産省", "meti", "regulation"], "policy"),
    (["quantum", "photonic", "research", "university", "lab "], "research"),
]


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _src_vid(source_id: str) -> str:
    return f"at://{_OWNER_DID}/{_COL_SRC}/{source_id}"


def _art_vid(article_id: str) -> str:
    return f"at://{_OWNER_DID}/{_COL_ART}/{article_id}"


def _dig_vid(date: str) -> str:
    return f"at://{_OWNER_DID}/{_COL_DIG}/{date}"


def _article_id(url: str) -> str:
    return "art-" + hashlib.sha256(url.encode()).hexdigest()[:16]


def _guess_category(text: str, default: str) -> str:
    low = (text or "").lower()
    for keywords, cat in _CAT_KEYWORDS:
        if any(kw in low for kw in keywords):
            return cat
    return default


def _strip_html(raw: str) -> str:
    if not raw:
        return ""
    return re.sub(r"<[^>]+>", "", raw).strip()[:1000]


# ---------------------------------------------------------------------------
# RSS / Atom feed parser
# ---------------------------------------------------------------------------

_NS = {
    "atom":    "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "rss10":   "http://purl.org/rss/1.0/",
    "rdf":     "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}


def _parse_feed(xml_bytes: bytes, source_name: str, source_lang: str, category: str) -> list[dict[str, Any]]:
    """Parse RSS 1.0/2.0 or Atom feed into article dicts."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    tag = root.tag
    articles: list[dict[str, Any]] = []

    if "Atom" in tag or "atom" in tag or root.tag == "{http://www.w3.org/2005/Atom}feed":
        # Atom 1.0
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title_el = entry.find("{http://www.w3.org/2005/Atom}title")
            link_el  = entry.find("{http://www.w3.org/2005/Atom}link[@rel='alternate']")
            if link_el is None:
                link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            summ_el  = entry.find("{http://www.w3.org/2005/Atom}summary")
            cont_el  = entry.find("{http://www.w3.org/2005/Atom}content")
            pub_el   = entry.find("{http://www.w3.org/2005/Atom}published") or entry.find("{http://www.w3.org/2005/Atom}updated")
            title = title_el.text if title_el is not None else ""
            url   = link_el.get("href", "") if link_el is not None else ""
            if not url:
                url = link_el.text.strip() if (link_el is not None and link_el.text) else ""
            summary = _strip_html((summ_el.text or "") if summ_el is not None else (cont_el.text or "") if cont_el is not None else "")
            pub = pub_el.text if pub_el is not None else _utc_now()
            if url:
                articles.append({"title": title or "", "url": url, "summary": summary, "pub": pub or _utc_now()})

    else:
        # RSS 2.0 or RSS 1.0 (RDF-based)
        channel = root.find("channel")
        items = root.findall(".//item")
        if not items and channel is not None:
            items = channel.findall("item")

        for item in items:
            title_el = item.find("title")
            link_el  = item.find("link")
            desc_el  = item.find("description")
            pub_el   = item.find("pubDate") or item.find("{http://purl.org/dc/elements/1.1/}date")
            title = title_el.text if title_el is not None else ""
            url   = link_el.text.strip() if (link_el is not None and link_el.text) else ""
            summary = _strip_html(desc_el.text or "" if desc_el is not None else "")
            pub = pub_el.text if pub_el is not None else _utc_now()
            if url:
                articles.append({"title": title or "", "url": url, "summary": summary, "pub": pub or _utc_now()})

    result = []
    for a in articles[:20]:  # cap at 20 per source
        url = a["url"]
        title = a["title"]
        summary = a["summary"]
        cat = _guess_category(f"{title} {summary}", category)
        result.append({
            "article_id":       _article_id(url),
            "source_url":       url,
            "source_name":      source_name,
            "source_lang":      source_lang,
            "title_original":   title,
            "title_ja":         "" if source_lang != "ja" else title,
            "title_en":         "" if source_lang != "en" else title,
            "summary_original": summary,
            "summary_ja":       "" if source_lang != "ja" else summary,
            "summary_en":       "" if source_lang != "en" else summary,
            "category":         cat,
            "subcategory":      "",
            "entities":         "[]",
            "tags":             "[]",
            "sentiment":        "neutral",
            "importance":       3,
            "published_at":     (a["pub"] or _utc_now())[:64],
            "crawled_at":       _utc_now(),
            "visibility":       "free",
            "writer_did":       f"{_OWNER_DID}:writer:{source_name.lower().replace(' ', '_')}",
        })
    return result


# ---------------------------------------------------------------------------
# handotai.seed.writers
# ---------------------------------------------------------------------------

def task_handotai_seed_writers() -> dict:
    """Idempotent upsert of 6 built-in RSS writer entries into vertex_handotai_source."""
    now = _utc_now()
    written = 0
    with sync_cursor() as cur:
        for w in _WRITERS:
            vid = _src_vid(w["source_id"])
            try:
                cur.execute(
                    """
                    INSERT INTO vertex_handotai_source (
                        vertex_id, source_id, name, url, source_type, language, category,
                        crawl_interval_min, enabled, writer_did, actor_did, org_did, created_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        vid, w["source_id"], w["name"], w["url"], "rss",
                        w["language"], w["category"], 15, True,
                        f"{_OWNER_DID}:writer:{w['source_id']}",
                        _OWNER_DID, _OWNER_DID, now,
                    ),
                )
                written += 1
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    pass
                else:
                    raise
    return {"written": written, "total": len(_WRITERS)}


# ---------------------------------------------------------------------------
# handotai.collect.rssAll
# ---------------------------------------------------------------------------

async def task_handotai_collect_rss_all(maxPerSource: int = 20) -> dict:
    """Fetch all 6 RSS feeds, parse articles, write to vertex_handotai_article."""
    cap = max(1, min(int(maxPerSource or 20), 50))
    total_written = 0
    total_skipped = 0
    errors: list[str] = []
    now = _utc_now()

    async with aiohttp.ClientSession(
        headers={"User-Agent": "handotai.etzhayyim.com/1.0 contact@etzhayyim.com"},
        timeout=aiohttp.ClientTimeout(total=30),
    ) as session:
        for w in _WRITERS:
            try:
                async with session.get(w["url"]) as resp:
                    if resp.status != 200:
                        errors.append(f"{w['source_id']}:http{resp.status}")
                        continue
                    body = await resp.read()
            except Exception as e:
                errors.append(f"{w['source_id']}:{type(e).__name__}")
                continue

            articles = _parse_feed(body, w["name"], w["language"], w["category"])
            articles = articles[:cap]

            with sync_cursor() as cur:
                for art in articles:
                    vid = _art_vid(art["article_id"])
                    try:
                        cur.execute(
                            """
                            INSERT INTO vertex_handotai_article (
                                vertex_id, article_id, source_url, source_name, source_lang,
                                title_original, title_ja, title_en,
                                summary_original, summary_ja, summary_en,
                                category, subcategory, entities, tags,
                                sentiment, importance, published_at, crawled_at,
                                visibility, writer_did, actor_did, org_did, created_at
                            ) VALUES (
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,
                                %s,%s,%s,
                                %s,%s,%s,%s,
                                %s,%s,%s,%s,
                                %s,%s,%s,%s,%s
                            )
                            """,
                            (
                                vid, art["article_id"], art["source_url"], art["source_name"],
                                art["source_lang"],
                                art["title_original"], art["title_ja"], art["title_en"],
                                art["summary_original"], art["summary_ja"], art["summary_en"],
                                art["category"], art["subcategory"], art["entities"], art["tags"],
                                art["sentiment"], art["importance"],
                                art["published_at"], now,
                                art["visibility"], art["writer_did"],
                                _OWNER_DID, _OWNER_DID, now,
                            ),
                        )
                        total_written += 1
                    except Exception as e:
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            total_skipped += 1
                        else:
                            errors.append(f"insert:{art['article_id']}:{e!s:.60}")

    return {"written": total_written, "skipped": total_skipped, "errors": errors[:10]}


# ---------------------------------------------------------------------------
# handotai.generate.digest
# ---------------------------------------------------------------------------

def task_handotai_generate_digest(date: str = "") -> dict:
    """Read today's articles from vertex_handotai_article, LLM-summarize, upsert digest."""
    if not date:
        date = time.strftime("%Y-%m-%d", time.gmtime())

    articles: list[dict[str, Any]] = []
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT title_original, title_ja, title_en, category, importance, source_lang
            FROM vertex_handotai_article
            WHERE crawled_at >= %s AND crawled_at < %s
            ORDER BY importance DESC
            LIMIT {lim}
            """.format(lim=50),
            (f"{date}T00:00:00Z", f"{date}T23:59:59Z"),
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        articles = [dict(zip(cols, r)) for r in (rows or [])]

    if not articles:
        return {"date": date, "articles": 0, "status": "noArticles"}

    lines = []
    for a in articles:
        title = a.get("title_ja") or a.get("title_original") or a.get("title_en") or ""
        cat = a.get("category", "")
        imp = a.get("importance", 3)
        lines.append(f"- [{cat}] {title} (importance:{imp})")

    bullet_text = "\n".join(lines)
    try:
        result = _llm.call_tier(
            "structured",
            "You are a semiconductor industry analyst. Write a concise daily digest in Japanese (3-4 paragraphs). Focus on key trends.",
            f"Date: {date}\nArticles ({len(articles)}):\n{bullet_text}",
            max_tokens=600,
            temperature=0.3,
        )
        summary = result.get("content", "").strip()
    except Exception as e:
        summary = f"[digest generation failed: {e!s:.80}]"

    now = _utc_now()
    vid = _dig_vid(date)
    with sync_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO vertex_handotai_digest (
                    vertex_id, date, total_articles, summary_ja,
                    generated_at, actor_did, org_did, created_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (vid, date, len(articles), summary, now, _OWNER_DID, _OWNER_DID, now),
            )
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                cur.execute(
                    "DELETE FROM vertex_handotai_digest WHERE vertex_id = %s",
                    (vid,),
                )
                cur.execute(
                    """
                    INSERT INTO vertex_handotai_digest (
                        vertex_id, date, total_articles, summary_ja,
                        generated_at, actor_did, org_did, created_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (vid, date, len(articles), summary, now, _OWNER_DID, _OWNER_DID, now),
                )
            else:
                raise

    return {"date": date, "articles": len(articles), "status": "generated"}


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------

def register(worker: Any, *, timeout_ms: int) -> None:
    worker.task(task_type="handotai.seed.writers",    single_value=False, timeout_ms=60_000)(task_handotai_seed_writers)
    worker.task(task_type="handotai.collect.rssAll",  single_value=False, timeout_ms=120_000)(task_handotai_collect_rss_all)
    worker.task(task_type="handotai.generate.digest", single_value=False, timeout_ms=60_000)(task_handotai_generate_digest)
