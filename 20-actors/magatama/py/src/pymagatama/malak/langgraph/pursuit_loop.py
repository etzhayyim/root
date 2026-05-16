"""pursuit_loop — resident LangGraph agent loop for malak OSINT pursuit.

Architecture (ADR-2605072000 agent-loop pattern):

    pick_target → plan_queries → fetch_sources → write_observations
                ↳ harvest_new_targets → update_target → sleep_or_continue

State persistence: every meaningful transition is a row in
`vertex_malak_pursuit_target` / `vertex_malak_osint_observation`
(+ edges) so the agent is fully resumable after process restart.

Sources (initial set):
    - crt.sh         (CT log JSON)
    - urlscan.io     (public domain page HTML)
    - gbizinfo       (国税庁/経産省 corporate registry, public JSON when available)

Each source has a `vertex_malak_osint_source` row registering its
identity, reliability, license. Adding a new source = data work
(seed_sources + extend fetch_sources branch).

CLI usage:

    python -m pymagatama.malak.langgraph.pursuit_loop \
        --case-id case:takahashi-hiroyuki-20260512 \
        --max-ticks 5

To run as daemon: drop --max-ticks; the loop will sleep `tick_interval_s`
seconds between ticks and pick the next stalest target.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

import psycopg
import urllib.request
from langgraph.graph import StateGraph, END

from .pursuit import classify_identifier, plan_queries


MALAK_DID  = "did:web:malak.gftd.ai"
YABAI_DID  = "did:web:yabai.gftd.ai"
TLP_RED    = "RED"

DEFAULT_TICK_INTERVAL_S = 90    # base wait between ticks
TICK_JITTER_S           = 30
TARGET_REQUEUE_S        = 3600  # re-pursue same target after 1h


# ── DB primitives ──────────────────────────────────────────────────────
def _conn():
    url = os.environ.get("RW_URL")
    if not url:
        raise RuntimeError("RW_URL not set — pursuit_loop requires RW")
    c = psycopg.connect(url, connect_timeout=15)
    c.autocommit = True
    return c


def _iso(dt: datetime | None = None) -> str:
    return (dt or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _vid(kind: str, rkey: str) -> str:
    return f"at://{MALAK_DID}/ai.gftd.apps.malak.{kind}/{rkey}"


def _rkey(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _http_get(url: str, *, timeout: int = 15, accept: str = "application/json") -> tuple[int, str]:
    """Minimal HTTP GET with User-Agent. Returns (status, body)."""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "malak-pursuit-loop/1.0 (+contact: j.kawasaki@gftd.co.jp)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except Exception as e:  # noqa: BLE001
        return -1, f"fetch_error: {e}"


# ── Source registry seeding ────────────────────────────────────────────
SOURCES: list[dict[str, Any]] = [
    {"source_id": "crt.sh",       "source_kind": "ct-log",        "source_url": "https://crt.sh",
     "api_endpoint": "https://crt.sh/?q={query}&output=json",
     "auth_kind": "none", "reliability_pct": 95, "licensed": False,
     "legal_basis": "公開 Certificate Transparency log",
     "note": "Comodo/Sectigo operated CT log mirror"},
    {"source_id": "urlscan.io",   "source_kind": "passive-dns",   "source_url": "https://urlscan.io",
     "api_endpoint": "https://urlscan.io/api/v1/search/?q=domain:{query}",
     "auth_kind": "scrape", "reliability_pct": 90, "licensed": False,
     "legal_basis": "公開 URL scanner free tier",
     "note": "API free tier rate-limited; falls back to /domain/{q} HTML"},
    {"source_id": "gbizinfo",     "source_kind": "corp-registry", "source_url": "https://info.gbiz.go.jp",
     "api_endpoint": "https://info.gbiz.go.jp/hojin/ichiran?hojinBango={query}",
     "auth_kind": "none", "reliability_pct": 98, "licensed": False,
     "legal_basis": "国税庁 法人番号公表サイト 公開データ",
     "note": "JP corporate registry (公開項目のみ — 役員名は別途登記必要)"},
    {"source_id": "duckduckgo",   "source_kind": "web",           "source_url": "https://duckduckgo.com",
     "api_endpoint": "https://duckduckgo.com/html/?q={query}",
     "auth_kind": "scrape", "reliability_pct": 60, "licensed": False,
     "legal_basis": "公開 search engine",
     "note": "Fallback search — heavy rate-limiting; html scrape"},
    {"source_id": "murakumo-llm", "source_kind": "manual",        "source_url": "https://murakumo.gftd.ai",
     "api_endpoint": "https://murakumo.gftd.ai/v1/chat/completions",
     "auth_kind": "api-key", "reliability_pct": 75, "licensed": True,
     "legal_basis": "内製 LLM (Gemma 4 E4B) — 自社 GPU",
     "note": "Local LLM enrichment: typed extraction from raw OSINT bodies"},
]


def seed_sources() -> int:
    inserted = 0
    with _conn() as c, c.cursor() as cur:
        for s in SOURCES:
            rkey = s["source_id"].replace(".", "-").replace("/", "-")
            vid  = _vid("osintSource", rkey)
            cur.execute("DELETE FROM vertex_malak_osint_source WHERE vertex_id=%s", (vid,))
            cur.execute(
                "INSERT INTO vertex_malak_osint_source ("
                "vertex_id, rkey, repo, source_id, source_kind, source_url, "
                "api_endpoint, auth_kind, reliability_pct, licensed, legal_basis, note, tlp, "
                "created_at, created_date, sensitivity_ord, owner_did, "
                "org_id, user_id, actor_id, actor_did, org_did"
                ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    vid, rkey, MALAK_DID, s["source_id"], s["source_kind"], s["source_url"],
                    s["api_endpoint"], s["auth_kind"], int(s["reliability_pct"]),
                    bool(s["licensed"]), s["legal_basis"], s["note"], TLP_RED,
                    _iso(), _today(), 50, MALAK_DID,
                    "gftd", MALAK_DID, "malak.pursuit-loop", MALAK_DID, MALAK_DID,
                ),
            )
            inserted += 1
    return inserted


def _source_vid(source_id: str) -> str:
    rkey = source_id.replace(".", "-").replace("/", "-")
    return _vid("osintSource", rkey)


# ── Target seeding & priority ──────────────────────────────────────────
def seed_targets_from_yabai(case_id: str) -> int:
    """Auto-promote every yabai entity flagged for this case to a pursuit_target."""
    inserted = 0
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT vertex_id, entity_type, name, canonical_name "
            "FROM vertex_yabai_entity WHERE source=%s",
            (case_id,),
        )
        rows = cur.fetchall()
        for vid_entity, etype, name, canonical in rows:
            # Map yabai entity_type → pursuit target_kind
            tkind = (
                "url" if etype == "phishing_url" and "://" in (canonical or "") else
                "domain" if etype == "phishing_url" else
                "jp-corp" if etype == "Organization" else
                "jp-name" if etype == "Person" else
                "app" if etype == "phishing_app" else
                "unknown"
            )
            # Severity → priority from yabai_flag
            cur.execute(
                "SELECT severity FROM vertex_yabai_flag WHERE entity_vid=%s LIMIT 1",
                (vid_entity,),
            )
            sev_row = cur.fetchone()
            sev = (sev_row[0] if sev_row else "high").lower()
            priority = {"critical": 9, "high": 7, "medium": 5, "low": 3}.get(sev, 5)

            target_id = canonical or name
            rkey = _rkey(case_id, tkind, target_id)
            vid_target = _vid("pursuitTarget", rkey)
            cur.execute("DELETE FROM vertex_malak_pursuit_target WHERE vertex_id=%s", (vid_target,))
            cur.execute(
                "INSERT INTO vertex_malak_pursuit_target ("
                "vertex_id, rkey, repo, target_id, target_kind, case_id, priority, pursuit_status, "
                "extends_entity_vid, next_due_at, last_pursued_at, pursuit_tick_count, observation_count, note, tlp, "
                "created_at, created_date, sensitivity_ord, owner_did, "
                "org_id, user_id, actor_id, actor_did, org_did"
                ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    vid_target, rkey, MALAK_DID, target_id, tkind, case_id, priority, "queued",
                    vid_entity, _iso(), None, 0, 0, f"seeded from yabai/{etype}/{name[:60]}", TLP_RED,
                    _iso(), _today(), 50, MALAK_DID,
                    "gftd", MALAK_DID, "malak.pursuit-loop", MALAK_DID, MALAK_DID,
                ),
            )
            # edge: target extends yabai_entity
            eid = _rkey("extends", vid_target, vid_entity)
            cur.execute("DELETE FROM edge_malak_target_extends WHERE edge_id=%s", (eid,))
            cur.execute(
                "INSERT INTO edge_malak_target_extends ("
                "src_id, dst_id, edge_id, relation, dst_kind, created_at, sensitivity_ord, owner_did"
                ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (vid_target, vid_entity, eid, "extends", "yabai_entity", _iso(), 50, MALAK_DID),
            )
            inserted += 1
    return inserted


def pick_next_target(case_id: str | None = None) -> tuple[str, str, str, int, int] | None:
    """Return (vid, target_id, target_kind, priority, tick_seq) or None."""
    with _conn() as c, c.cursor() as cur:
        params = []
        sql = (
            "SELECT vertex_id, target_id, target_kind, priority, pursuit_tick_count "
            "FROM vertex_malak_pursuit_target "
            "WHERE pursuit_status='queued' AND next_due_at <= %s "
        )
        params.append(_iso())
        if case_id:
            sql += "AND case_id=%s "
            params.append(case_id)
        sql += "ORDER BY priority DESC, next_due_at ASC LIMIT 1"
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        return row if row else None


# ── Fetchers per source ────────────────────────────────────────────────
def fetch_crt_sh(domain: str) -> tuple[str, int, str]:
    """Return (raw_url, status, body)."""
    u = f"https://crt.sh/?q={urllib.parse.quote(domain)}&output=json"
    st, body = _http_get(u, accept="application/json")
    return u, st, body[:50000]


def fetch_urlscan_search(domain: str) -> tuple[str, int, str]:
    u = f"https://urlscan.io/api/v1/search/?q=domain:{urllib.parse.quote(domain)}"
    st, body = _http_get(u, accept="application/json")
    return u, st, body[:50000]


def fetch_gbizinfo(hojin_bango_or_query: str) -> tuple[str, int, str]:
    u = f"https://info.gbiz.go.jp/hojin/ichiran?hojinBango={urllib.parse.quote(hojin_bango_or_query)}"
    st, body = _http_get(u, accept="text/html")
    return u, st, body[:50000]


def fetch_ddg(query: str) -> tuple[str, int, str]:
    u = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    st, body = _http_get(u, accept="text/html")
    return u, st, body[:50000]


SOURCE_ROUTES = {
    # target_kind → list of (source_id, fetcher, query_arg_kind)
    "domain":          [("crt.sh", fetch_crt_sh, "target_id"),
                        ("urlscan.io", fetch_urlscan_search, "target_id")],
    "url":             [("crt.sh", fetch_crt_sh, "target_host"),
                        ("urlscan.io", fetch_urlscan_search, "target_host")],
    "line-p2p":        [("duckduckgo", fetch_ddg, "target_id_search")],
    "line-open-chat":  [("duckduckgo", fetch_ddg, "target_id_search")],
    "jp-corp":         [("gbizinfo", fetch_gbizinfo, "target_id"),
                        ("duckduckgo", fetch_ddg, "target_id_search")],
    "jp-name":         [("duckduckgo", fetch_ddg, "target_id_search")],
    "person":          [("duckduckgo", fetch_ddg, "target_id_search")],
    "alias_platform":  [("duckduckgo", fetch_ddg, "target_id_search")],
    "wallet":          [("duckduckgo", fetch_ddg, "target_id_search")],
    "contract":        [("duckduckgo", fetch_ddg, "target_id_search")],
    "recovery_scam":   [("duckduckgo", fetch_ddg, "target_id_search")],
    "app":             [("duckduckgo", fetch_ddg, "target_id_search")],
    "btc":             [("duckduckgo", fetch_ddg, "target_id_search")],
    "eth":             [("duckduckgo", fetch_ddg, "target_id_search")],
    "unknown":         [("duckduckgo", fetch_ddg, "target_id_search")],
}


def _smart_route(target_id: str, target_kind: str) -> list:
    """Heuristic override: if target_id looks like a domain (has dot, no spaces,
    short TLD), route to crt.sh + urlscan regardless of target_kind. This makes
    pursuit_loop robust to upstream Pregel pipelines that emit coarse kinds
    like `alias_platform` for both names and domain strings."""
    s = (target_id or "").strip()
    if (
        "." in s
        and " " not in s
        and len(s) <= 80
        and not s.startswith(("0x", "bc1", "1", "3"))   # not wallet-looking
    ):
        last = s.rsplit(".", 1)[-1]
        if 2 <= len(last) <= 8 and last.replace("-", "").isalpha():
            return [("crt.sh", fetch_crt_sh, "target_id"),
                    ("urlscan.io", fetch_urlscan_search, "target_id")]
    return SOURCE_ROUTES.get(target_kind, SOURCE_ROUTES["unknown"])


def _query_for_route(target_id: str, target_kind: str, query_arg_kind: str) -> str:
    if query_arg_kind == "target_id":
        return target_id
    if query_arg_kind == "target_host":
        try:
            return urllib.parse.urlparse(target_id).netloc or target_id
        except Exception:  # noqa: BLE001
            return target_id
    return f'"{target_id}" 詐欺 OR fraud OR phishing'


# ── Observation writer ────────────────────────────────────────────────
def write_observation(
    target_vid: str,
    source_id: str,
    case_id: str,
    finding_kind: str,
    title: str,
    body: str,
    raw_url: str,
    raw_status: int,
    confidence: float,
    tick_seq: int,
) -> str:
    sha = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    rkey = _rkey(target_vid, source_id, sha, str(tick_seq))
    vid = _vid("osintObservation", rkey)
    source_vid = _source_vid(source_id)
    with _conn() as c, c.cursor() as cur:
        cur.execute("DELETE FROM vertex_malak_osint_observation WHERE vertex_id=%s", (vid,))
        cur.execute(
            "INSERT INTO vertex_malak_osint_observation ("
            "vertex_id, rkey, repo, observation_id, target_vid, source_vid, case_id, "
            "finding_kind, title, body, body_sha256, confidence, observed_at, fetched_at, "
            "raw_url, raw_status, tick_seq, tlp, "
            "created_at, created_date, sensitivity_ord, owner_did, "
            "org_id, user_id, actor_id, actor_did, org_did"
            ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                vid, rkey, MALAK_DID, rkey, target_vid, source_vid, case_id,
                finding_kind, title[:200], body[:8000], sha, float(confidence),
                _iso(), _iso(),
                raw_url[:500], int(raw_status), int(tick_seq), TLP_RED,
                _iso(), _today(), 50, MALAK_DID,
                "gftd", MALAK_DID, "malak.pursuit-loop", MALAK_DID, MALAK_DID,
            ),
        )
        # edges
        for rel, dst, etbl in (
            ("observation_about", target_vid, "edge_malak_observation_about"),
            ("observation_from",  source_vid, "edge_malak_observation_from"),
        ):
            eid = _rkey(rel, vid, dst)
            cur.execute(f"DELETE FROM {etbl} WHERE edge_id=%s", (eid,))
            cur.execute(
                f"INSERT INTO {etbl} (src_id, dst_id, edge_id, relation, created_at, sensitivity_ord, owner_did) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (vid, dst, eid, rel, _iso(), 50, MALAK_DID),
            )
    return vid


def update_target_after_tick(target_vid: str, observation_count_delta: int) -> None:
    next_due = (datetime.now(timezone.utc) + timedelta(seconds=TARGET_REQUEUE_S)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT vertex_id, rkey, repo, target_id, target_kind, case_id, priority, "
            "extends_entity_vid, pursuit_tick_count, observation_count, note, tlp, "
            "created_at, created_date, sensitivity_ord, owner_did, "
            "org_id, user_id, actor_id, actor_did, org_did "
            "FROM vertex_malak_pursuit_target WHERE vertex_id=%s",
            (target_vid,),
        )
        row = cur.fetchone()
        if not row:
            return
        (vid_, rkey, repo, tid, tkind, cid, prio, ext_vid,
         tick_count, obs_count, note, tlp,
         created_at, created_date, sens, owner,
         org_id, user_id, actor_id, actor_did, org_did) = row
        cur.execute("DELETE FROM vertex_malak_pursuit_target WHERE vertex_id=%s", (target_vid,))
        cur.execute(
            "INSERT INTO vertex_malak_pursuit_target ("
            "vertex_id, rkey, repo, target_id, target_kind, case_id, priority, pursuit_status, "
            "extends_entity_vid, next_due_at, last_pursued_at, pursuit_tick_count, observation_count, note, tlp, "
            "created_at, created_date, sensitivity_ord, owner_did, "
            "org_id, user_id, actor_id, actor_did, org_did"
            ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (vid_, rkey, repo, tid, tkind, cid, prio, "queued",
             ext_vid, next_due, _iso(), int(tick_count) + 1,
             int(obs_count) + int(observation_count_delta), note, tlp,
             created_at, created_date, sens, owner,
             org_id, user_id, actor_id, actor_did, org_did),
        )


# ── LangGraph state ────────────────────────────────────────────────────
class PursuitTickState(TypedDict, total=False):
    case_id: str
    target_vid: str
    target_id: str
    target_kind: str
    tick_seq: int
    plan: list[dict[str, str]]
    observations: list[str]   # observation vid list
    fetched_bodies: list[tuple[str, str]]  # (source_id, body) — passed to llm_enrich
    error: str
    done: bool


# ── Nodes ──────────────────────────────────────────────────────────────
def node_pick(state: PursuitTickState) -> dict:
    cid = state.get("case_id")
    picked = pick_next_target(case_id=cid)
    if picked is None:
        return {"done": True}
    vid, tid, tkind, _prio, tick_count = picked
    return {
        "target_vid": vid,
        "target_id":  tid,
        "target_kind": tkind,
        "tick_seq":   int(tick_count) + 1,
        "done": False,
    }


def node_plan(state: PursuitTickState) -> dict:
    if state.get("done"):
        return {}
    return {"plan": plan_queries(state.get("target_id", ""))}


def node_fetch(state: PursuitTickState) -> dict:
    if state.get("done"):
        return {}
    tid   = state.get("target_id", "")
    tkind = state.get("target_kind", "unknown")
    routes = _smart_route(tid, tkind)
    case_id = state.get("case_id", "")
    target_vid = state.get("target_vid", "")
    tick_seq = int(state.get("tick_seq", 1))
    obs_vids: list[str] = []
    fetched_bodies: list[tuple[str, str]] = []
    for source_id, fetcher, q_kind in routes:
        q = _query_for_route(tid, tkind, q_kind)
        try:
            raw_url, status, body = fetcher(q)
        except Exception as e:  # noqa: BLE001
            raw_url, status, body = f"<{source_id}>", -1, f"fetcher_exception: {e}"
        if status in (200, 201):
            fetched_bodies.append((source_id, body))
        # finding_kind by source
        fk = {
            "crt.sh":     "cert-row",
            "urlscan.io": "passive-dns",
            "gbizinfo":   "corp-record",
            "duckduckgo": "search-hit",
        }.get(source_id, "search-hit")
        if status in (200, 201):
            confidence = 0.85 if source_id in ("crt.sh", "gbizinfo") else 0.55
            title = f"{source_id}:{tkind}:{tid[:80]}"
        else:
            confidence = 0.1
            fk = "nothing-found"
            title = f"{source_id}:{tkind}:{tid[:80]} [status={status}]"
        try:
            obs_vid = write_observation(
                target_vid=target_vid, source_id=source_id, case_id=case_id,
                finding_kind=fk, title=title, body=body,
                raw_url=raw_url, raw_status=status, confidence=confidence,
                tick_seq=tick_seq,
            )
            obs_vids.append(obs_vid)
            print(f"    ✓ {source_id:<12} status={status:<4} kind={fk:<12} obs={obs_vid[-12:]}")
        except Exception as e:  # noqa: BLE001
            print(f"    ✗ {source_id:<12} write failed: {e}")
    return {"observations": obs_vids, "fetched_bodies": fetched_bodies}


def _llm_enrich(target_id: str, target_kind: str, bodies: list[tuple[str, str]]) -> dict[str, Any] | None:
    """Call murakumo (or any OpenAI-compatible) endpoint to typed-extract.

    Returns dict { director_names[], related_orgs[], addresses[], new_identifiers[],
    scam_relevance: float 0-1, summary: str } or None on failure.
    """
    base = os.environ.get("GFTD_LLM_URL") or "https://murakumo.gftd.ai/v1/chat/completions"
    api_key = os.environ.get("GFTD_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or ""
    model = os.environ.get("GFTD_LLM_MODEL") or "gemma-4-e4b-it"
    if not api_key:
        return None
    # Aggregate body excerpts (capped) for one LLM round
    excerpt = "\n\n---\n\n".join(f"[{src}]\n{body[:3000]}" for src, body in bodies)[:9000]
    sys_prompt = (
        "あなたは日本警察協力の OSINT 解析エンジン。出力は厳密 JSON のみ。"
        "対象は SNS 投資詐欺事件 (高橋宏之事件) の追跡 entity。"
        "与えられた raw fetch (crt.sh / urlscan / gbizinfo / search) から下記を抽出。"
    )
    user_prompt = (
        f"target_id={target_id}\ntarget_kind={target_kind}\n\n"
        f"=== raw fetched bodies ===\n{excerpt}\n\n"
        '=== 抽出スキーマ (JSON のみ返答, 余計な前置きなし) ===\n'
        '{"director_names":[],"related_orgs":[],"addresses":[],"phones":[],'
        '"new_identifiers":[{"id":"","kind":"domain|url|jp-corp|jp-name|phone","why":""}],'
        '"scam_relevance":0.0,"summary":""}'
    )
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "malak-pursuit-loop/1.0",
        },
    )
    # Cloudflare edge cuts at 100s — keep our deadline at 90 to leave headroom.
    # Cold-start gemma on murakumo can take 30-60s; one retry covers worker
    # rebalancing within the litellm pool.
    import time as _time
    last_err = "no attempt"
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                content = content.strip()
                if content.startswith("```"):
                    content = content.strip("`").lstrip("json").strip()
                return json.loads(content)
        except Exception as e:  # noqa: BLE001
            last_err = f"attempt{attempt+1}: {str(e)[:160]}"
            if attempt == 0:
                _time.sleep(5)
                continue
    return {"_error": last_err}


def write_discovered_target(parent_obs_vid: str, case_id: str, ident: str, kind: str, why: str) -> str | None:
    """Insert a newly-discovered identifier as a queued pursuit_target + edge."""
    rkey = _rkey(case_id, kind, ident)
    vid = _vid("pursuitTarget", rkey)
    with _conn() as c, c.cursor() as cur:
        # Skip if already exists (don't reset priority/status)
        cur.execute("SELECT 1 FROM vertex_malak_pursuit_target WHERE vertex_id=%s", (vid,))
        if cur.fetchone():
            return None
        cur.execute(
            "INSERT INTO vertex_malak_pursuit_target ("
            "vertex_id, rkey, repo, target_id, target_kind, case_id, priority, pursuit_status, "
            "extends_entity_vid, next_due_at, last_pursued_at, pursuit_tick_count, observation_count, note, tlp, "
            "created_at, created_date, sensitivity_ord, owner_did, "
            "org_id, user_id, actor_id, actor_did, org_did"
            ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (vid, rkey, MALAK_DID, ident[:200], kind, case_id, 6, "queued",
             None, _iso(), None, 0, 0, f"discovered via LLM: {why[:200]}", TLP_RED,
             _iso(), _today(), 50, MALAK_DID,
             "gftd", MALAK_DID, "malak.pursuit-loop", MALAK_DID, MALAK_DID),
        )
        eid = _rkey("discovered", parent_obs_vid, vid)
        cur.execute("DELETE FROM edge_malak_target_discovered WHERE edge_id=%s", (eid,))
        cur.execute(
            "INSERT INTO edge_malak_target_discovered ("
            "src_id, dst_id, edge_id, relation, created_at, sensitivity_ord, owner_did"
            ") VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (parent_obs_vid, vid, eid, "discovered", _iso(), 50, MALAK_DID),
        )
    return vid


def node_llm_enrich(state: PursuitTickState) -> dict:
    if state.get("done"):
        return {}
    if os.environ.get("PURSUIT_DISABLE_LLM") == "1":
        return {}
    target_vid = state.get("target_vid", "")
    target_id  = state.get("target_id", "")
    target_kind = state.get("target_kind", "unknown")
    case_id = state.get("case_id", "")
    tick_seq = int(state.get("tick_seq", 1))

    # Use bodies passed from node_fetch (RW barrier prevents re-querying
    # the rows we just wrote — pass via state instead)
    bodies = state.get("fetched_bodies") or []
    if not bodies:
        return {}

    enriched = _llm_enrich(target_id, target_kind, bodies)
    if not enriched or enriched.get("_error"):
        # Still write a tombstone observation so we know LLM was attempted
        obs_vid = write_observation(
            target_vid=target_vid, source_id="murakumo-llm", case_id=case_id,
            finding_kind="llm-extract", title=f"llm-extract:{target_id[:60]}",
            body=json.dumps({"error": (enriched or {}).get("_error", "no llm endpoint")},
                            ensure_ascii=False),
            raw_url=os.environ.get("GFTD_LLM_URL", ""), raw_status=-1,
            confidence=0.0, tick_seq=tick_seq,
        )
        return {"observations": (state.get("observations") or []) + [obs_vid]}

    body = json.dumps(enriched, ensure_ascii=False)
    confidence = float(enriched.get("scam_relevance", 0.5)) if isinstance(enriched.get("scam_relevance"), (int, float)) else 0.5
    obs_vid = write_observation(
        target_vid=target_vid, source_id="murakumo-llm", case_id=case_id,
        finding_kind="llm-extract", title=f"llm-extract:{target_id[:60]}",
        body=body, raw_url=os.environ.get("GFTD_LLM_URL", ""), raw_status=200,
        confidence=confidence, tick_seq=tick_seq,
    )
    # Spawn newly-discovered targets
    discovered = 0
    for d in (enriched.get("new_identifiers") or [])[:20]:
        if not isinstance(d, dict):
            continue
        new_id = str(d.get("id", "")).strip()
        new_kind = str(d.get("kind", "unknown")).strip() or "unknown"
        why = str(d.get("why", "")).strip()
        if not new_id or len(new_id) > 200:
            continue
        if write_discovered_target(obs_vid, case_id, new_id, new_kind, why):
            discovered += 1
    if discovered:
        print(f"    ✓ llm-extract     status=200  discovered={discovered} new targets")
    else:
        print(f"    ✓ llm-extract     status=200  (no new identifiers)")
    return {"observations": (state.get("observations") or []) + [obs_vid]}


def node_update(state: PursuitTickState) -> dict:
    if state.get("done"):
        return {}
    vid = state.get("target_vid", "")
    n = len(state.get("observations") or [])
    update_target_after_tick(vid, n)
    return {}


def build_pursuit_loop_graph():
    g = StateGraph(PursuitTickState)
    g.add_node("pick",       node_pick)
    g.add_node("plan",       node_plan)
    g.add_node("fetch",      node_fetch)
    g.add_node("llm_enrich", node_llm_enrich)
    g.add_node("update",     node_update)
    g.set_entry_point("pick")
    g.add_edge("pick",       "plan")
    g.add_edge("plan",       "fetch")
    g.add_edge("fetch",      "llm_enrich")
    g.add_edge("llm_enrich", "update")
    g.add_edge("update",     END)
    return g.compile()


# ── Resident driver ───────────────────────────────────────────────────
async def run_one_tick(case_id: str | None) -> dict[str, Any]:
    graph = build_pursuit_loop_graph()
    initial: PursuitTickState = {"case_id": case_id or ""}
    return await graph.ainvoke(initial)


async def run_resident_loop(
    case_id: str | None,
    max_ticks: int | None,
    tick_interval_s: int = DEFAULT_TICK_INTERVAL_S,
) -> dict[str, Any]:
    """Run resident agent loop. `max_ticks=None` ⇒ runs forever."""
    total_ticks = 0
    total_obs = 0
    started = _iso()
    while True:
        if max_ticks is not None and total_ticks >= max_ticks:
            break
        result = await run_one_tick(case_id)
        if result.get("done"):
            print("[pursuit_loop] queue exhausted; sleeping…")
            await asyncio.sleep(tick_interval_s)
            continue
        total_ticks += 1
        n_obs = len(result.get("observations") or [])
        total_obs += n_obs
        print(
            f"[pursuit_loop] tick #{total_ticks}  "
            f"target={(result.get('target_id') or '')[:60]:<60}  "
            f"kind={result.get('target_kind'):<14}  observations={n_obs}"
        )
        if max_ticks is not None and total_ticks >= max_ticks:
            break
        # cadence with jitter
        sleep_s = tick_interval_s + random.randint(0, TICK_JITTER_S)
        await asyncio.sleep(sleep_s)
    return {"started": started, "ended": _iso(), "ticks": total_ticks, "observations": total_obs}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="pursuit_loop")
    p.add_argument("--case-id", default=None, help="restrict targets to one case")
    p.add_argument("--max-ticks", type=int, default=None, help="finite mode (omit for daemon)")
    p.add_argument("--tick-interval", type=int, default=DEFAULT_TICK_INTERVAL_S, help="sleep seconds between ticks")
    p.add_argument("--seed-sources", action="store_true", help="upsert SOURCES then exit")
    p.add_argument("--seed-from-yabai-case", default=None, help="auto-import yabai entities of this case as targets")
    args = p.parse_args(argv)

    if args.seed_sources:
        n = seed_sources()
        print(f"[pursuit_loop] sources seeded: {n}")
        return

    if args.seed_from_yabai_case:
        n = seed_targets_from_yabai(args.seed_from_yabai_case)
        print(f"[pursuit_loop] targets seeded from yabai/{args.seed_from_yabai_case}: {n}")
        return

    result = asyncio.run(
        run_resident_loop(args.case_id, args.max_ticks, args.tick_interval)
    )
    print(f"[pursuit_loop] DONE  {result}")


if __name__ == "__main__":
    main()
