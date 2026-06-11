#!/usr/bin/env python3
"""Phase 4 (RisingWave): Murakumo LLM intelligence extraction → vertex_profile enrichment.

Reads CC domains from RisingWave vertex_domain, calls Murakumo qwen3.5-9b to extract
structured intelligence, and updates vertex_profile.description with enriched intel.
Also stores intel JSON in vertex_domain.topics column.

Replaces phase4_intel_extract.py (file-based JSONL → direct RisingWave PG INSERT/UPDATE).

Usage:
# CHARTER-VIOLATION §substrate (centralized DB forbidden — migrate to AT MST + IPFS + Base L2)
  python3 phase4_intel_risingwave.py --limit 10 --dry-run     # test 10 domains
  python3 phase4_intel_risingwave.py --limit 100              # process 100
  python3 phase4_intel_risingwave.py                          # all CC domains
  python3 phase4_intel_risingwave.py --reset                  # restart

TODO(substrate-boundary): replace RW read/update operations (psycopg2 fetch/execute)
with AT Protocol MST reads via @etzhayyim/sdk per ADR-2605172000. Domain intelligence
collection: 'com.etzhayyim.apps.commonCrawl.domainIntel', rkey=domain_slug. Remove RW_URL env.
"""

import argparse
import json
import logging
import os
import re
import signal
import sys
import time
from pathlib import Path

import psycopg2
import psycopg2.extras
import requests

# ── Config ──

RW_HOST = os.environ.get("RW_HOST", "localhost")
RW_PORT = int(os.environ.get("RW_PORT", "4566"))
RW_USER = os.environ.get("RW_USER", "root")
RW_DB = os.environ.get("RW_DB", "dev")

MURAKUMO_URL = os.environ.get("MURAKUMO_URL", "https://murakumo.etzhayyim.com")
MURAKUMO_MODEL = os.environ.get("MURAKUMO_MODEL", "qwen3.5-9b")
MURAKUMO_API_KEY = os.environ.get(
    "MURAKUMO_API_KEY",
    "",
)

# ── RunPod fallback ──
RUNPOD_GATEWAY_URL  = os.environ.get("RUNPOD_GATEWAY_URL", "https://runpod.etzhayyim.com")
RUNPOD_GATEWAY_KEY  = os.environ.get("RUNPOD_GATEWAY_KEY", "rpgw_7kXm3Nv8QwPf2RsYtUeH4JcLbA9DzGiO6WhK1MpV5nBx")
RUNPOD_MODEL        = os.environ.get("RUNPOD_MODEL", "gemma4:31b-it-q4_K_M")

PDS_URL = os.environ.get("PDS_URL", "https://atproto.etzhayyim.com")
SITE_APP_DID = "did:web:site.etzhayyim.com"

STATE_FILE = Path("/tmp/.phase4_rw_state.json")
MAX_RETRIES = 2

# Track which backend is active in this session
_active_backend = "murakumo"  # or "runpod"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

shutdown_requested = False


def handle_signal(signum, frame):
    global shutdown_requested
    log.info("Shutdown requested...")
    shutdown_requested = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def get_conn():
    return psycopg2.connect(
        host=RW_HOST, port=RW_PORT, user=RW_USER, dbname=RW_DB,
        connect_timeout=10,
    )


def load_state():
    if STATE_FILE.exists():
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            pass
    return {"done_dids": []}


def save_state(state):
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f)
    tmp.rename(STATE_FILE)


def _llm_post(session: requests.Session, url: str, headers: dict, body: dict, timeout: int) -> str:
    """POST to any OpenAI-compatible endpoint, return content string."""
    resp = session.post(url, json=body, headers=headers, timeout=timeout)
    resp.raise_for_status()
    choices = resp.json().get("choices", [])
    text = choices[0]["message"]["content"] if choices else ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return text


def _try_murakumo(session: requests.Session, prompt: str, max_tokens: int) -> str:
    if not MURAKUMO_API_KEY:
        raise RuntimeError("MURAKUMO_API_KEY env var required")
    return _llm_post(
        session,
        f"{MURAKUMO_URL}/api/openai/v1/chat/completions",
        {"x-api-key": MURAKUMO_API_KEY, "Content-Type": "application/json"},
        {"model": MURAKUMO_MODEL, "messages": [{"role": "user", "content": prompt}],
         "max_tokens": max_tokens, "temperature": 0.1},
        timeout=180,
    )


def _try_runpod(session: requests.Session, prompt: str, max_tokens: int) -> str:
    return _llm_post(
        session,
        f"{RUNPOD_GATEWAY_URL}/v1/chat/completions",
        {"x-api-key": RUNPOD_GATEWAY_KEY, "Content-Type": "application/json"},
        {"model": RUNPOD_MODEL, "messages": [{"role": "user", "content": prompt}],
         "max_tokens": min(max_tokens, 8192), "temperature": 0.1},
        timeout=120,
    )


def llm_call(session: requests.Session, prompt: str, max_tokens: int = 32000) -> str:
    """Call LLM with Murakumo → RunPod fallback.

    - Tries Murakumo (qwen3.5-9b) first (1 attempt + 1 retry).
    - On 5xx / timeout, falls back to RunPod gateway (gemma-4-e2b-it).
    - Once RunPod fallback is activated in a session it stays on RunPod
      to avoid oscillating between backends.
    """
    global _active_backend

    backends = (
        [("runpod", _try_runpod)]
        if _active_backend == "runpod"
        else [("murakumo", _try_murakumo), ("runpod", _try_runpod)]
    )

    for name, fn in backends:
        for attempt in range(MAX_RETRIES):
            try:
                text = fn(session, prompt, max_tokens)
                if text:
                    if _active_backend != name:
                        log.info(f"  LLM backend switched to {name}")
                        _active_backend = name
                    return text
            except Exception as e:
                is_5xx = hasattr(e, "response") and e.response is not None and e.response.status_code >= 500
                is_timeout = "timeout" in str(e).lower() or "524" in str(e) or "502" in str(e)
                if attempt < MAX_RETRIES - 1 and (is_5xx or is_timeout):
                    log.warning(f"  [{name}] retry {attempt + 1}: {e}")
                    time.sleep(2)
                else:
                    log.warning(f"  [{name}] failed: {e}")
                    break  # try next backend

    log.error("  All LLM backends failed")
    return ""


def parse_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences."""
    if not text:
        return {}
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    if json_start < 0 or json_end <= json_start:
        return {}
    try:
        return json.loads(text[json_start:json_end])
    except json.JSONDecodeError:
        return {}


def extract_intel(session: requests.Session, domain: str, page_count: int, sample_titles: list[str]) -> dict:
    """Extract structured intel for one domain via Murakumo LLM."""
    titles_str = json.dumps(sample_titles[:5], ensure_ascii=False) if sample_titles else "[]"
    prompt = f"""Extract structured intelligence for this internet domain. Return JSON only (English).

Domain: {domain}
Page count: {page_count}
Sample page titles: {titles_str}

Extract these fields:
- entityType: one of [organization, platform, media, government, database, marketplace, community, academic, ngo, personal]
- industry: primary industry/sector (string, max 40 chars)
- operator: organization name that operates this domain (max 60 chars)
- jurisdiction: country ISO 3166-1 alpha-2 code (e.g., "JP", "US")
- description: one-sentence English description of this domain (max 200 chars)
- services: list of services/functions (max 3 strings)
- trustLevel: one of [high, medium, low, unknown]

Return a single JSON object. No explanation."""

    text = llm_call(session, prompt, max_tokens=32000)
    result = parse_json(text)

    if isinstance(result, dict) and result.get("entityType"):
        return {
            "entityType": str(result.get("entityType", ""))[:40],
            "industry": str(result.get("industry", ""))[:80],
            "operator": str(result.get("operator", ""))[:120],
            "jurisdiction": str(result.get("jurisdiction", ""))[:8],
            "description": str(result.get("description", ""))[:300],
            "services": [str(s)[:60] for s in result.get("services", [])][:3],
            "trustLevel": str(result.get("trustLevel", "unknown"))[:20],
        }
    return {}


def update_profile_via_pds(session: requests.Session, did: str, display_name: str, description: str):
    """Update PDS profile via com.etzhayyim.pds.putProfile."""
    body = {
        "$type": "app.bsky.actor.profile",
        "repo": did,
        "displayName": display_name,
        "description": description,
    }
    headers = {
        "Content-Type": "application/json",
        "x-kotodama-verified": "true",
        "X-Active-DID": SITE_APP_DID,
    }
    resp = session.post(
        f"{PDS_URL}/xrpc/com.etzhayyim.pds.putProfile",
        json=body, headers=headers, timeout=30,
    )
    return resp.status_code < 400


def main():
    parser = argparse.ArgumentParser(description="Phase 4: Intel extraction → RisingWave profile enrichment")
    parser.add_argument("--limit", type=int, default=0, help="Max domains (0=all)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--update-pds", action="store_true", help="Also update PDS profile via putProfile")
    parser.add_argument("--gaps-only", action="store_true",
                        help="Only process domains with no actor in mv_cc_domain_coverage (coverage gap fill)")
    args = parser.parse_args()

    if args.reset and STATE_FILE.exists():
        STATE_FILE.unlink()
        log.info("State reset")

    state = load_state()
    done_dids = set(state.get("done_dids", []))

    conn = get_conn()
    cur = conn.cursor()

    if args.gaps_only:
        # Domains not yet registered as site.domain actors in vertex_actor.
        # mv_cc_domain_coverage was removed; use direct LEFT JOIN on vertex_actor.
        # Filter: domain must contain a dot (skip garbage CC entries).
        cur.execute("""
            SELECT vd.vertex_id, vd.domain, vd.topics
            FROM vertex_domain vd
            LEFT JOIN vertex_actor va
              ON va.collection = 'com.etzhayyim.apps.site.domain' AND va.rkey = vd.domain
            WHERE va.rkey IS NULL
              AND vd.domain LIKE '%.%'
              AND vd.domain ~ '^[a-zA-Z0-9]'
              AND length(vd.domain) <= 100
              AND vd.domain NOT LIKE '.%'
              AND vd.domain NOT LIKE '% %'
            ORDER BY vd.domain
        """)
        rows = cur.fetchall()
        # Normalize to (vid, did, dom, slug) format using domain as vertex_id/did
        domains = [(r[0], r[0], r[1], r[1].replace(".", "-")) for r in rows]
    else:
        cur.execute("""
            SELECT vertex_id, domain
            FROM vertex_domain
            WHERE domain LIKE '%.%'
              AND domain ~ '^[a-zA-Z0-9]'
              AND length(domain) <= 100
              AND domain NOT LIKE '.%'
              AND domain NOT LIKE '% %'
            ORDER BY domain
        """)
        rows = cur.fetchall()
        domains = [(r[0], r[0], r[1], r[1].replace(".", "-")) for r in rows]
    log.info(f"Found {len(domains)} CC domains in vertex_domain")

    remaining = [(vid, did, dom, slug) for vid, did, dom, slug in domains if dom not in done_dids]
    if args.limit > 0:
        remaining = remaining[:args.limit]
    log.info(f"Processing {len(remaining)} domains ({len(done_dids)} already done)")

    session = requests.Session()
    t0 = time.time()
    success = 0
    failed = 0

    for i, (vid, did, dom, slug) in enumerate(remaining):
        if shutdown_requested:
            break

        # New schema: vertex_page not available; titles come from edge_hosts_page if present
        sample_titles = []
        page_count = 0

        if args.dry_run:
            log.info(f"  [DRY-RUN] {dom} (pages={page_count})")
            continue

        intel = extract_intel(session, dom, page_count, sample_titles)
        if not intel:
            failed += 1
            log.warning(f"  [{i+1}/{len(remaining)}] {dom}: LLM extraction failed")
            continue

        # Build enriched description
        parts = [f"[AI Agent — unofficial]"]
        if intel["entityType"]:
            parts.append(f"{intel['entityType']}")
        if intel["industry"]:
            parts.append(f"({intel['industry']})")
        if intel["operator"]:
            parts.append(f"— {intel['operator']}")
        if intel["jurisdiction"]:
            parts.append(f"[{intel['jurisdiction']}]")
        header = " ".join(parts)
        full_desc = f"{header}\n{intel['description']}"
        if intel["services"]:
            full_desc += f"\nServices: {', '.join(intel['services'])}"

        # 1. Update vertex_domain.topics with intel JSON (new schema: domain=vertex_id)
        try:
            now = int(time.time() * 1000)
            cur.execute(
                "INSERT INTO vertex_domain (vertex_id, domain, topics, _seq, created_date, sensitivity_ord, owner_did) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (vid, dom, json.dumps(intel), now, None, 0, None),
            )
            conn.commit()
        except Exception as e:
            log.error(f"  [{i+1}] {dom}: vertex_domain INSERT failed: {e}")
            conn.rollback()
            failed += 1
            continue

        # 3. Optionally update PDS profile via putProfile API
        if args.update_pds:
            update_profile_via_pds(session, did, dom, full_desc)

        success += 1
        done_dids.add(dom)  # Track by domain name (new schema: vertex_id = domain)

        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(remaining) - i - 1) / rate / 60 if rate > 0 else 0
            log.info(
                f"  [{i+1}/{len(remaining)}] success={success} failed={failed} "
                f"({rate:.1f}/s, ETA {eta:.0f}min)"
            )
            state["done_dids"] = list(done_dids)
            save_state(state)

    state["done_dids"] = list(done_dids)
    save_state(state)
    elapsed = time.time() - t0
    log.info(f"Done: success={success} failed={failed} ({elapsed:.0f}s)")
    conn.close()


if __name__ == "__main__":
    main()
