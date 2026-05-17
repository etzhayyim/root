"""
open-patent generation primitives (ai.gftd.apps.openPatent.*).

Reads from vertex_open_patent_patent corpus (ingested by patent.etzhayyim.com via AT
firehose — open-patent never calls external APIs directly).

Writes to:
  vertex_open_patent_invention_seed
  vertex_open_patent_novelty_report

HITL boundary: claim drafting and filing are human-only.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from pymagatama.db_sync import sync_cursor

# ── Actor DIDs ─────────────────────────────────────────────────────────
OWNER_DID = "did:web:open-patent.etzhayyim.com"
INVENTOR_DID = f"{OWNER_DID}:actor:inventor"
ANALYST_DID = f"{OWNER_DID}:actor:analyst"

# ── LLM ───────────────────────────────────────────────────────────────
_LLM_URL = os.environ.get("GFTD_LLM_URL", "https://murakumo.etzhayyim.com/v1/chat/completions")
_LLM_KEY = os.environ.get("GFTD_LLM_API_KEY", "sk-murakumo-local")
_LLM_MODEL = os.environ.get("OPEN_PATENT_LLM_MODEL", os.environ.get("GFTD_LLM_MODEL", "qwen3-30b"))


async def _llm(prompt: str, *, temperature: float = 0.4, max_tokens: int = 2048) -> str:
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            _LLM_URL,
            headers={"Authorization": f"Bearer {_LLM_KEY}"},
            json={
                "model": _LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


# ── ID helpers ─────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_vid(tech_domain: str, title: str) -> str:
    h = hashlib.sha256(f"seed:{tech_domain}:{title}".encode()).hexdigest()[:20]
    return f"at://{INVENTOR_DID}/ai.gftd.apps.openPatent.inventionSeed/{h}"


def _report_vid(seed_vid: str) -> str:
    h = hashlib.sha256(f"report:{seed_vid}".encode()).hexdigest()[:20]
    return f"at://{ANALYST_DID}/ai.gftd.apps.openPatent.noveltyReport/{h}"


# ── Primitive 1: gather_tech_trends ───────────────────────────────────

def task_open_patent_gather_tech_trends(limit: int = 5) -> list[dict[str, Any]]:
    """
    Read the top IPC classes from recent patents in the corpus.
    Returns list of {ipc_class, count, sample_titles}.
    """
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                COALESCE(ipc_classes, 'UNKNOWN') AS ipc_class,
                COUNT(*) AS cnt
            FROM vertex_open_patent_patent
            WHERE ipc_classes IS NOT NULL
            GROUP BY ipc_classes
            ORDER BY cnt DESC
            LIMIT {int(limit)}
            """
        )
        rows = cur.fetchall()

    return [
        {
            "ipc_class": row[0],
            "count": row[1],
            "sample_titles": [],
        }
        for row in (rows or [])
    ]


# ── Primitive 2: generate_invention_seed (async) ─────────────────────

async def _async_generate_seed(
    tech_domain: str,
    sample_titles: list[str],
    count: int = 3,
) -> list[dict[str, Any]]:
    titles_bullet = "\n".join(f"- {t}" for t in sample_titles[:10])
    prompt = (
        f"You are an expert patent agent (DID: {INVENTOR_DID}).\n"
        f"Technology domain (IPC class): {tech_domain}\n"
        "Recent patents in this domain:\n"
        f"{titles_bullet}\n\n"
        f"Generate {count} novel invention ideas that are NOT obvious continuations "
        "of the listed patents but fill real technical gaps or combine domains unexpectedly.\n\n"
        "Return ONLY valid JSON (no prose), exactly this structure:\n"
        "{\n"
        '  "seeds": [\n'
        '    {\n'
        '      "title": "...",\n'
        '      "summary": "2-3 sentence technical description",\n'
        '      "key_claims": ["claim 1 concept", "claim 2 concept"],\n'
        '      "ipc_class": "Hxx / Gxx / etc"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    raw = await _llm(prompt, temperature=0.6, max_tokens=2048)

    import re
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []

    now = _now_iso()
    results = []
    for s in (data.get("seeds") or [])[:count]:
        title = str(s.get("title", ""))[:500]
        if not title:
            continue
        vid = _seed_vid(tech_domain, title)
        results.append({
            "vertex_id": vid,
            "owner_did": OWNER_DID,
            "tech_domain": tech_domain[:50],
            "title": title,
            "summary": str(s.get("summary", ""))[:4000],
            "key_claims_json": json.dumps(
                [str(c)[:2000] for c in (s.get("key_claims") or [])[:10]]
            ),
            "ipc_class": str(s.get("ipc_class", tech_domain))[:20],
            "corpus_patent_ids_json": json.dumps(sample_titles[:5]),
            "novelty_score": None,
            "novelty_status": "pending",
            "actor_id": INVENTOR_DID,
            "created_at": now,
        })
    return results


def task_open_patent_generate_invention_seeds(
    tech_domain: str,
    sample_titles: list[str],
    count: int = 3,
) -> list[dict[str, Any]]:
    """Synchronous wrapper for LangGraph node use."""
    return asyncio.run(_async_generate_seed(tech_domain, sample_titles, count))


# ── Primitive 3: search_prior_art ─────────────────────────────────────

def task_open_patent_search_prior_art(
    title: str,
    summary: str,
    ipc_class: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Text-match search against vertex_open_patent_patent for prior art.
    Returns list of {vertex_id, patent_number, title, similarity_score(rough)}.
    IPC class filter narrows the scope first.
    """
    ipc_filter = ipc_class.split("/")[0].strip()[:4] if ipc_class else ""

    with sync_cursor() as cur:
        if ipc_filter:
            cur.execute(
                f"""
                SELECT vertex_id, patent_number, title
                FROM vertex_open_patent_patent
                WHERE ipc_classes LIKE %s
                  AND (title LIKE %s OR title LIKE %s)
                ORDER BY created_at DESC
                LIMIT {int(limit)}
                """,
                (
                    f"{ipc_filter}%",
                    f"%{title[:60]}%",
                    f"%{summary[:60]}%",
                ),
            )
        else:
            cur.execute(
                f"""
                SELECT vertex_id, patent_number, title
                FROM vertex_open_patent_patent
                WHERE title LIKE %s OR title LIKE %s
                ORDER BY created_at DESC
                LIMIT {int(limit)}
                """,
                (f"%{title[:60]}%", f"%{summary[:60]}%"),
            )
        rows = cur.fetchall() or []

    return [
        {
            "vertex_id": row[0],
            "patent_number": row[1],
            "title": row[2],
            "rough_score": 50,
        }
        for row in rows
    ]


# ── Primitive 4: assess_novelty (async) ──────────────────────────────

async def _async_assess_novelty(
    seed: dict[str, Any],
    prior_art: list[dict[str, Any]],
) -> dict[str, Any]:
    prior_titles = "\n".join(
        f"- [{p.get('patent_number','')}] {p.get('title','')}"
        for p in prior_art[:15]
    )
    prompt = (
        f"You are a patent examiner AI (DID: {ANALYST_DID}).\n\n"
        f"Invention seed:\nTitle: {seed.get('title','')}\n"
        f"Summary: {seed.get('summary','')}\n\n"
        "Prior art found:\n"
        f"{prior_titles if prior_titles else '(none found)'}\n\n"
        "Assess novelty on a scale of 0-100 where:\n"
        "  0  = identical to existing patent\n"
        "  50 = incremental improvement\n"
        "  80 = meaningfully novel combination\n"
        " 100 = entirely new concept with no close prior art\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "novelty_score": 75,\n'
        '  "reasoning": "2-3 sentences explaining the score",\n'
        '  "closest_prior_art": "patent number or title of closest match"\n'
        "}"
    )
    raw = await _llm(prompt, temperature=0.1, max_tokens=512)

    import re
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {"novelty_score": 0, "reasoning": "parse_error", "closest_prior_art": ""}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"novelty_score": 0, "reasoning": "json_error", "closest_prior_art": ""}

    return {
        "novelty_score": max(0, min(100, int(data.get("novelty_score", 0) or 0))),
        "reasoning": str(data.get("reasoning", ""))[:4000],
        "closest_prior_art": str(data.get("closest_prior_art", ""))[:200],
    }


def task_open_patent_assess_novelty(
    seed: dict[str, Any],
    prior_art: list[dict[str, Any]],
) -> dict[str, Any]:
    return asyncio.run(_async_assess_novelty(seed, prior_art))


# ── Primitive 5: persist seeds + reports ─────────────────────────────

def task_open_patent_persist_seeds(seeds: list[dict[str, Any]]) -> int:
    """
    INSERT invention seeds. Skips existing vertex_ids.
    Returns count of newly inserted rows.
    """
    if not seeds:
        return 0

    from datetime import date
    today = date.today().isoformat()
    inserted = 0
    with sync_cursor() as cur:
        cur.execute("SET dml_rate_limit = 200")
        for s in seeds:
            # RisingWave: no ON CONFLICT — skip-if-exists via NOT EXISTS
            cur.execute(
                """
                INSERT INTO vertex_open_patent_invention_seed (
                    vertex_id, created_date, sensitivity_ord, owner_did,
                    tech_domain, title, summary, key_claims_json, ipc_class,
                    corpus_patent_ids_json, novelty_score, novelty_status,
                    created_at, actor_id
                )
                SELECT %s, %s, 0, %s,
                       %s, %s, %s, %s, %s,
                       %s, %s, %s,
                       %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM vertex_open_patent_invention_seed
                    WHERE vertex_id = %s
                )
                """,
                (
                    s["vertex_id"], today, s["owner_did"],
                    s["tech_domain"], s["title"], s["summary"],
                    s["key_claims_json"], s["ipc_class"],
                    s.get("corpus_patent_ids_json", "[]"),
                    s.get("novelty_score"), s["novelty_status"],
                    s["created_at"], s["actor_id"],
                    s["vertex_id"],
                ),
            )
            inserted += cur.rowcount
    return inserted


def task_open_patent_persist_novelty_report(
    seed_vid: str,
    prior_art: list[dict[str, Any]],
    assessment: dict[str, Any],
) -> str:
    """
    INSERT a novelty report and UPDATE the seed's novelty_score/status.
    Returns the report vertex_id.
    """
    novelty_score = assessment.get("novelty_score", 0)
    status = "review" if novelty_score >= 60 else ("pass" if novelty_score >= 40 else "fail")

    report_vid = _report_vid(seed_vid)
    prior_vids = [p.get("vertex_id", "") for p in prior_art]
    sim_scores = [{"patentVid": p.get("vertex_id", ""), "score": p.get("rough_score", 50)} for p in prior_art]
    now = _now_iso()

    from datetime import date
    today = date.today().isoformat()
    with sync_cursor() as cur:
        cur.execute("SET dml_rate_limit = 100")
        # RisingWave: no ON CONFLICT — delete-then-insert for upsert semantics
        cur.execute(
            "DELETE FROM vertex_open_patent_novelty_report WHERE vertex_id = %s",
            (report_vid,),
        )
        cur.execute(
            """
            INSERT INTO vertex_open_patent_novelty_report (
                vertex_id, created_date, sensitivity_ord, owner_did,
                seed_vid, prior_art_count, prior_art_vids_json,
                similarity_scores_json, overall_novelty_score,
                reasoning, created_at, actor_id
            ) VALUES (
                %s, %s, 0, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s
            )
            """,
            (
                report_vid, today, OWNER_DID,
                seed_vid, len(prior_art),
                json.dumps(prior_vids),
                json.dumps(sim_scores), novelty_score,
                assessment.get("reasoning", "")[:4000], now, ANALYST_DID,
            ),
        )
        cur.execute(
            """
            UPDATE vertex_open_patent_invention_seed
               SET novelty_score = %s, novelty_status = %s
             WHERE vertex_id = %s
            """,
            (novelty_score, status, seed_vid),
        )

    return report_vid
