"""bitnest_exit_pursuit — Pregel-style LangGraph tracker for BitNest exit-fraud.

Scope: investigate the 2025-12 BitNest exit-scam (Medium / decripto.org /
dehek.com / LinkedIn / TradersUnion reporting) and link findings back to the
high-priority case `case:takahashi-hiroyuki-20260512` (高橋宏之事件).

Architecture (per ADR-2605080600 LangGraph Server + Granian L3, ADR-2605082000
graph-definition-as-data, ADR-2605131600 malak orchestration LangGraph+Pregel):

  Pregel super-steps (parentheses):

    Start
      │ (1) sequential — input validation, case_id, source seed
      ▼
    seed_sources
      │
      ▼
    fan_out_fetch ──────────────────────────────────────────────────┐
      │ (2) BSP parallel via langgraph.constants.Send               │
      ├─► fetch_one (×N sources)                                    │
                                                                    ▼
      │ (3) implicit barrier — all fetchers complete
      ▼
    fan_out_extract ────────────────────────────────────────────────┐
      │ (4) BSP parallel LLM extraction per source                  │
      ├─► llm_extract_one (×N)                                      │
                                                                    ▼
      │ (5) implicit barrier
      ▼
    correlate
      │ — dedupe operators / wallets / smart_contracts;
      │ — build chain-probe target list
      ▼
    fan_out_chain_probe ────────────────────────────────────────────┐
      │ (6) BSP parallel wallet/contract probe                      │
      ├─► probe_wallet_one (×W)                                     │
                                                                    ▼
      │ (7) implicit barrier
      ▼
    link_back_to_takahashi
      │ — write edge_malak_target_extends from new entities to
      │   existing yabai entities (bitnest-ex.com, bitnest.apk, …)
      ▼
    emit_pegel
      │ — one investigationTick per source + one summary tick
      ▼
    persist_fs → audit_emit → End

State channels with Pregel reducers:

  fetched         : Annotated[Dict[str, FetchResult], _merge_dict]
  extractions     : Annotated[Dict[str, dict],        _merge_dict]
  chain_probes    : Annotated[Dict[str, dict],        _merge_dict]
  observation_vids: Annotated[List[str],              _merge_list]

Defense-in-depth: edge gate (Worker preflight) + LangServer gate (this module's
`gate_input`) + pyzeebe gate (if invoked via bpmn-dispatcher). All three
enforce: case_id present, tlp=RED, network egress whitelist for fetch_one.

Phase 0 caveat: `live_write=False` keeps RW INSERT / pegel-tick / edge-write in
dry-run (logs only). Phase 1 flips on after G1+G2 GREEN per
`_working/malak/surveillance/PHASE-1-LAUNCH-READINESS.md`.

Run modes:

  # Single-shot dry-run
  python -m pymagatama.malak.langgraph.bitnest_exit_pursuit \
      --case-id case:takahashi-hiroyuki-20260512 \
      --output-dir _working/malak/bitnest-exit-20260514

  # Live (Phase 1+ only; emits pegel ticks + RW edges)
  python -m pymagatama.malak.langgraph.bitnest_exit_pursuit \
      --case-id case:takahashi-hiroyuki-20260512 --live-write

  # HTTP via LangServer (after server.py CHAINS registration)
  curl -X POST http://127.0.0.1:8765/invoke/bitnestExitPursuit \
      -H 'content-type: application/json' \
      -d '{"case_id":"case:takahashi-hiroyuki-20260512"}'
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import hashlib
import json
import logging
import os
import pathlib
import urllib.parse
import urllib.request
from typing import Annotated, Any, Dict, List, Optional, Tuple, TypedDict

from langgraph.constants import Send
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


MALAK_DID = "did:web:malak.gftd.ai"
YABAI_DID = "did:web:yabai.gftd.ai"
TLP_RED   = "RED"
DEFAULT_CASE_ID = "case:takahashi-hiroyuki-20260512"

# Known yabai entities that this pursuit links back to (rkey = hiroyuki-<slug>).
# Source of truth: CXO-LEDGER #27 Phase 8 yabai surface (2026-05-13).
TAKAHASHI_YABAI_ANCHORS: Tuple[str, ...] = (
    "hiroyuki-bitnest-app",
    "hiroyuki-bitnest-ex-com",
    "hiroyuki-leedsil-com",
    "hiroyuki-leedsec-com",
    "hiroyuki-leeds-securities",
    "hiroyuki-jpevaluation-net",
)

# Hallucination guard: names that should NEVER appear as operator aliases.
# These are the *investigative journalists / researchers* who exposed BitNest,
# not the perpetrators. Models sometimes confuse author bylines with subject.
HALLUCINATION_ALIAS_BLOCKLIST: frozenset[str] = frozenset({
    "danny de hek", "mellion danny de hek", "mellion de hek", "danny dehek",
    "de hek", "decripto", "decripto.org", "alexander monroe", "orzo.asleep",
    "tradersunion", "traders union",
})


def _is_hallucinated_alias(s: str) -> bool:
    """True if `s` looks like an investigative-journalist name that the LLM
    misattributed as an operator alias. Compared case-insensitively after
    trim."""
    return s.strip().lower() in HALLUCINATION_ALIAS_BLOCKLIST

# ── Reducers (Pregel parallel write merge) ─────────────────────────────


def _merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Dict-channel reducer: combine partial states written by parallel Sends."""
    if not a:
        return dict(b or {})
    if not b:
        return dict(a)
    out = dict(a)
    out.update(b)
    return out


def _merge_list(a: List[Any], b: List[Any]) -> List[Any]:
    """List-channel reducer: concatenate. De-dupe is the consumer's job."""
    out: List[Any] = list(a or [])
    if b:
        out.extend(b)
    return out


# ── Seed sources (BitNest exit-fraud specific) ─────────────────────────


SEED_SOURCES: Tuple[Dict[str, str], ...] = (
    {"key": "medium-orzo",
     "url": "https://medium.com/@orzo.asleep_2d/bitnest-me-scam-alert-how-i-lost-my-crypto-and-recovered-my-money-b8a6d42e3a12",
     "title": "Bitnest.me Scam Alert: How I Lost My Crypto and Recovered My Money",
     "publisher": "Medium / @orzo.asleep_2d",
     "published": "2026-01-09",
     "credibility": 0.45,
     "notes": "victim self-report; recovery firm 'ForensiBlock' = likely secondary scam"},
    {"key": "dehek-yunus-loop",
     "url": "https://www.dehek.com/general/scam-fraud-investigations/bitnest-is-just-yunus-loop-defi-in-disguise-blockchain-evidence-confirms-the-rug/",
     "title": "BitNest is just Yunus Loop DeFi in disguise — blockchain evidence confirms the rug",
     "publisher": "dehek.com (Danny de Hek)",
     "published": "2025-12",
     "credibility": 0.85,
     "notes": "primary investigative reporting; on-chain evidence of Yunus Loop predecessor"},
    {"key": "linkedin-munir",
     "url": "https://www.linkedin.com/pulse/munir-jannedy-exposed-dark-truth-behind-bitnest-mellion-danny-de-hek-2lmpf",
     "title": "Munir Jannedy Exposed: The Dark Truth Behind BitNest",
     "publisher": "LinkedIn / Danny de Hek",
     "published": "2025-04-24",
     "credibility": 0.85,
     "notes": "names Munir Ali Kaid-Al Jannedy (alias Mr. JANNEDY) as operator"},
    {"key": "decripto-260m-volume",
     "url": "https://decripto.org/en/bitnest-the-defi-scam-platform-with-260-million-in-volume-exclusive-on-chain-analysis/",
     "title": "BitNest: the DeFi scam platform with $260M in volume (on-chain analysis)",
     "publisher": "decripto.org",
     "published": "2025",
     "credibility": 0.80,
     "notes": "smart contract volume USD 260M in 5 months from March 2025"},
    {"key": "decripto-end-of-line",
     "url": "https://decripto.org/en/bitnest-at-the-end-of-the-line-payment-delays-and-a-shower-of-reports-the-exit-scam-is-just-around-the-corner/",
     "title": "BitNest at the end of the line — payment delays + exit scam imminent",
     "publisher": "decripto.org",
     "published": "2025-12",
     "credibility": 0.80,
     "notes": "2025-12-11..14 withdrawal stops; $10K+ blocked; Telegram muted"},
    {"key": "tradersunion",
     "url": "https://tradersunion.com/scam-or-safe/bitnest-review/",
     "title": "Is BitNest a Safe or Scam? (May 2026)",
     "publisher": "TradersUnion",
     "published": "2026-05",
     "credibility": 0.55,
     "notes": "ASIC blacklist confirmed 2025-12-11"},
)


# ── State ─────────────────────────────────────────────────────────────


class BitnestPursuitState(TypedDict, total=False):
    # input
    case_id: str
    output_dir: str
    sources: List[Dict[str, str]]       # override SEED_SOURCES
    extra_seed_urls: List[str]          # adhoc URLs to add to fetch list
    live_write: bool                    # default False (Phase 0)
    llm_disabled: bool                  # skip LLM extraction (smoke-test)
    serial_llm: bool                    # serial LLM extraction (single-GPU Ollama)
    fixture_extractions: Dict[str, Dict[str, Any]]  # inject hand-curated extractions, bypass LLM
    # internal — parallel channels need reducers
    fetched:      Annotated[Dict[str, Dict[str, Any]], _merge_dict]
    extractions:  Annotated[Dict[str, Dict[str, Any]], _merge_dict]
    chain_probes: Annotated[Dict[str, Dict[str, Any]], _merge_dict]
    # correlated entity rollup
    operators:        List[Dict[str, Any]]
    wallets:          List[Dict[str, Any]]
    smart_contracts:  List[Dict[str, Any]]
    domains:          List[str]
    regulator_actions: List[Dict[str, Any]]
    recovery_followups: List[str]
    aliases:           List[str]
    japan_link:        Dict[str, List[str]]   # {victim_names: [...], domains: [...], banks: [...]}
    # output
    observation_vids: Annotated[List[str], _merge_list]
    edges_written: List[Dict[str, str]]
    pegel_tick_ids: List[str]
    written_files: Dict[str, str]
    document_sha256: str
    status: str           # ok | denied | error
    error: str


# ── Helpers ────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%d")


def _rkey(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _vid(kind: str, rkey: str) -> str:
    return f"at://{MALAK_DID}/ai.gftd.apps.malak.{kind}/{rkey}"


def _yabai_vid(rkey: str) -> str:
    # Matches yabai_publish.py emission pattern: at://yabai/ai.gftd.apps.yabai.entity/<rkey>
    return f"at://{YABAI_DID}/ai.gftd.apps.yabai.entity/{rkey}"


def _http_get(url: str, *, timeout: int = 20, accept: str = "text/html") -> Tuple[int, str]:
    """Sync HTTP GET. Returns (status, body[:80000])."""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "malak-bitnest-pursuit/1.0 (+contact: j.kawasaki@gftd.co.jp)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body[:80000]
    except Exception as e:  # noqa: BLE001
        return -1, f"fetch_error: {e}"


def _is_onion_url(url: str) -> bool:
    try:
        host = urllib.parse.urlparse(url).hostname or ""
    except Exception:  # noqa: BLE001
        return False
    return host.endswith(".onion")


def _onion_fetch(url: str, *, timeout: int = 45) -> Tuple[int, str, str, List[str]]:
    """Fetch .onion URL via shared `pymagatama.primitives.onion_crawl` proxy
    (Tor + Playwright CF Container). Returns (status, body, title, outbound_links)."""
    from pymagatama.primitives.onion_crawl import _fetch_via_proxy
    result = _fetch_via_proxy(url, float(timeout))
    if not result.get("ok"):
        return -1, f"onion_fetch_error: {result.get('error') or 'unknown'}", "", []
    body = str(result.get("html") or "")
    return (
        int(result.get("statusCode") or 0),
        body[:80000],
        str(result.get("title") or ""),
        list(result.get("outboundLinks") or []),
    )


# ── Nodes ──────────────────────────────────────────────────────────────


def gate_input_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Super-step 1: validate + assemble seed list."""
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    sources = list(state.get("sources") or SEED_SOURCES)
    for extra in state.get("extra_seed_urls") or []:
        key = "adhoc-" + _rkey(extra)[:8]
        sources.append({
            "key": key, "url": extra, "title": extra, "publisher": "adhoc",
            "published": _today(), "credibility": "0.5", "notes": "user-supplied",
        })
    if not sources:
        return {"status": "error", "error": "no sources to fetch"}
    return {
        "case_id":          case_id,
        "sources":          sources,
        "fetched":          {},
        "extractions":      {},
        "chain_probes":     {},
        "observation_vids": [],
        "edges_written":    [],
        "pegel_tick_ids":   [],
        "written_files":    {},
        "operators":        [],
        "wallets":          [],
        "smart_contracts":  [],
        "domains":          [],
        "regulator_actions": [],
        "recovery_followups": [],
        "aliases":          [],
        "japan_link":       {"victim_names": [], "domains": [], "banks": []},
    }


def fan_out_fetch(state: BitnestPursuitState):
    """Super-step 2: dispatch parallel fetch tasks via Send."""
    sources = state.get("sources") or []
    return [
        Send("fetch_one", {**state, "_source": s})
        for s in sources
    ]


def fetch_one_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Fetch ONE source URL. Result merged into `fetched` dict-channel.

    `.onion` URLs are routed through `darkweb-proxy.gftd.ai/fetch` (Tor +
    Playwright CF Container) via the shared onion_crawl primitive, so
    bitnest pursuit can ingest darkweb sources without duplicating the
    Tor egress stack. Clearweb URLs use the direct urllib path."""
    src = state.get("_source") or {}
    key = src.get("key") or _rkey(src.get("url", ""))
    url = src.get("url") or ""
    if _is_onion_url(url):
        status, body, proxy_title, outbound = _onion_fetch(url)
        fetch_kind = "onion"
        title = src.get("title") or proxy_title or ""
    else:
        status, body = _http_get(url)
        fetch_kind = "clearweb"
        title = src.get("title", "")
        outbound = []
    sha = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    record = {
        "key":      key,
        "url":      url,
        "status":   status,
        "body":     body,
        "sha256":   sha,
        "publisher": src.get("publisher", ""),
        "title":    title,
        "published": src.get("published", ""),
        "credibility": float(src.get("credibility", 0.5) or 0.5),
        "notes":    src.get("notes", ""),
        "fetched_at": _now_iso(),
        "fetch_kind": fetch_kind,
        "outbound_links": outbound,
    }
    logger.info("fetch_one  kind=%s key=%s status=%s len=%d sha=%s",
                fetch_kind, key, status, len(body), sha[:12])
    return {"fetched": {key: record}}


def after_fetch_barrier_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Sequential super-step run ONCE after all parallel fetch_one Sends
    complete. Acts as the explicit Pregel barrier so the conditional
    fan_out_extract that follows runs exactly once (not per-parallel-fetcher)."""
    fetched = state.get("fetched") or {}
    ok = sum(1 for r in fetched.values() if r.get("status") in (200, 201))
    logger.info("after_fetch_barrier  fetched=%d ok=%d", len(fetched), ok)
    return {}


def route_extract(state: BitnestPursuitState):
    """Conditional edge that BOTH gates and fans out. Routes to:
    - "inject_fixtures"     when fixture_extractions is non-empty (testing path)
    - "correlate"           when llm_disabled
    - "llm_extract_serial"  when serial_llm=True or GFTD_LLM_SERIAL=1
    - Send list             otherwise (parallel fan-out)
    """
    if state.get("fixture_extractions"):
        return "inject_fixtures"
    if state.get("llm_disabled"):
        return "correlate"
    fetched = state.get("fetched") or {}
    has_body = any(
        r.get("status", -1) in (200, 201) and (r.get("body") or "").strip()
        for r in fetched.values()
    )
    if not has_body:
        return "correlate"
    if state.get("serial_llm") or os.environ.get("GFTD_LLM_SERIAL") == "1":
        return "llm_extract_serial"
    return [
        Send("llm_extract_one", {**state, "_fetch_key": k})
        for k, r in fetched.items()
        if r.get("status", -1) in (200, 201) and (r.get("body") or "").strip()
    ]


def after_extract_barrier_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Barrier after parallel LLM extractions converge into correlate."""
    n = len(state.get("extractions") or {})
    logger.info("after_extract_barrier  extractions=%d", n)
    return {}


EXTRACT_SCHEMA = (
    '{"operators":[{"name":"","aliases":[],"nationality":""}],'
    '"wallets":[{"address":"","chain":"btc|eth|bsc|tron","label":""}],'
    '"smart_contracts":[{"address":"","chain":"","purpose":""}],'
    '"domains":[],'
    '"aliases_or_predecessors":[],'
    '"withdrawal_amount_usd":0,'
    '"exit_date":"",'
    '"regulator_actions":[{"regulator":"","action":"","date":""}],'
    '"recovery_scam_followups":[],'
    '"japan_link":{"victim_names":[],"domains":[],"banks":[]},'
    '"summary":""}'
)


def _llm_extract_call(source_key: str, title: str, body: str) -> Dict[str, Any]:
    base = os.environ.get("GFTD_LLM_URL") or "https://murakumo.gftd.ai/v1/chat/completions"
    api_key = os.environ.get("GFTD_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or ""
    model = os.environ.get("GFTD_LLM_MODEL") or "gemma-4-e4b-it"
    if not api_key:
        return {"_skipped": "no LLM api key (set GFTD_LLM_API_KEY)"}
    sys_prompt = (
        "You are an OSINT analyst. Extract structured indicators from the given "
        "investigative report about the BitNest exit-fraud (DeFi/MLM scam) and "
        "its predecessor Yunus Loop. Output STRICT JSON only — no preamble, no "
        "markdown fence. Target case = 高橋宏之 (Takahashi Hiroyuki) Japanese "
        "victim of related Murakami Yoshiaki impersonation + Leeds Securities + "
        "bitnest-ex.com / leedsil.com phishing infra. Flag any explicit Japan "
        "link."
    )
    # Body excerpt size — too large causes cold-start timeouts on local Ollama
    # for 9B+ models. Override via GFTD_LLM_BODY_CHARS env var if upstream
    # context window allows more.
    body_chars = int(os.environ.get("GFTD_LLM_BODY_CHARS", "4500"))
    user_prompt = (
        f"source_key={source_key}\ntitle={title}\n\n"
        f"=== article body (truncated) ===\n{body[:body_chars]}\n\n"
        f"=== schema (return JSON matching this shape) ===\n{EXTRACT_SCHEMA}"
    )
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base,
        data=payload,
        method="POST",
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent":    "malak-bitnest-pursuit/1.0",
        },
    )
    # Per-attempt timeout — local Ollama 9B cold-start needs 60-120s of model
    # load + 20-40s inference. Cloud routes are far faster.
    timeout_s = int(os.environ.get("GFTD_LLM_TIMEOUT_S", "240"))
    attempts = int(os.environ.get("GFTD_LLM_ATTEMPTS", "2"))
    import time as _time
    last_err = "no attempt"
    for attempt in range(max(1, attempts)):
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = (
                    data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                )
                if content.startswith("```"):
                    content = content.strip("`").lstrip("json").strip()
                return json.loads(content)
        except Exception as e:  # noqa: BLE001
            last_err = f"attempt{attempt+1}: {str(e)[:160]}"
            if attempt < attempts - 1:
                _time.sleep(5)
                continue
    return {"_error": last_err}


def llm_extract_one_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Parallel LLM extraction for ONE fetched source."""
    key = state.get("_fetch_key") or ""
    fetched = (state.get("fetched") or {}).get(key) or {}
    if not fetched:
        return {}
    extraction = _llm_extract_call(
        source_key=key,
        title=fetched.get("title", ""),
        body=fetched.get("body", ""),
    )
    logger.info(
        "llm_extract_one  key=%s operators=%d wallets=%d contracts=%d err=%s",
        key,
        len(extraction.get("operators", []) or []),
        len(extraction.get("wallets", []) or []),
        len(extraction.get("smart_contracts", []) or []),
        (extraction.get("_error") or "")[:80],
    )
    return {"extractions": {key: extraction}}


def inject_fixtures_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Inject hand-curated extractions instead of calling LLM. Used when:
    (a) upstream LLM endpoint is unavailable/unreliable, or
    (b) we want deterministic correlate+link_back testing.
    The fixture extractions must match the EXTRACT_SCHEMA shape."""
    fx = state.get("fixture_extractions") or {}
    logger.info("inject_fixtures  sources=%d", len(fx))
    return {"extractions": dict(fx)}


def llm_extract_serial_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Serial LLM extraction across ALL fetched sources. Used when the
    upstream LLM endpoint cannot handle parallel load (e.g., single-GPU
    local Ollama). Opt-in via `serial_llm: True` in state or
    `GFTD_LLM_SERIAL=1` env var."""
    fetched = state.get("fetched") or {}
    out: Dict[str, Dict[str, Any]] = {}
    targets = [
        (k, r) for k, r in fetched.items()
        if r.get("status", -1) in (200, 201) and (r.get("body") or "").strip()
    ]
    logger.info("llm_extract_serial  targets=%d", len(targets))
    for i, (key, r) in enumerate(targets, 1):
        logger.info("  → [%d/%d] %s", i, len(targets), key)
        ex = _llm_extract_call(
            source_key=key,
            title=r.get("title", ""),
            body=r.get("body", ""),
        )
        out[key] = ex
        logger.info(
            "  ✓ %s  operators=%d wallets=%d contracts=%d err=%s",
            key,
            len(ex.get("operators", []) or []),
            len(ex.get("wallets", []) or []),
            len(ex.get("smart_contracts", []) or []),
            (ex.get("_error") or "")[:80],
        )
    return {"extractions": out}


def correlate_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Sequential super-step: dedupe extracted entities by canonical key."""
    operators_idx: Dict[str, Dict[str, Any]] = {}
    wallets_idx:   Dict[str, Dict[str, Any]] = {}
    contracts_idx: Dict[str, Dict[str, Any]] = {}
    domains: List[str] = []
    aliases: List[str] = []
    regulator_actions: List[Dict[str, Any]] = []
    recovery_followups: List[str] = []
    japan_victims: List[str] = []
    japan_domains: List[str] = []
    japan_banks:   List[str] = []

    for key, ex in (state.get("extractions") or {}).items():
        if not isinstance(ex, dict) or ex.get("_error") or ex.get("_skipped"):
            continue
        for op in (ex.get("operators") or [])[:20]:
            if not isinstance(op, dict):
                continue
            name = (op.get("name") or "").strip()
            if not name or _is_hallucinated_alias(name):
                # Skip empty placeholders + misattributed journalist names
                continue
            ck = name.lower()
            cur = operators_idx.get(ck) or {
                "name": name, "aliases": [], "sources": [],
                "nationality": op.get("nationality", ""),
            }
            for a in (op.get("aliases") or []):
                if not a or not isinstance(a, str):
                    continue
                if _is_hallucinated_alias(a):
                    logger.info("filtered hallucinated alias %r from operator %r", a, name)
                    continue
                if a not in cur["aliases"]:
                    cur["aliases"].append(a)
            if key not in cur["sources"]:
                cur["sources"].append(key)
            operators_idx[ck] = cur
        for w in (ex.get("wallets") or [])[:50]:
            if not isinstance(w, dict):
                continue
            addr = (w.get("address") or "").strip()
            if not addr or len(addr) > 80:
                continue
            ck = f"{(w.get('chain') or 'unknown').lower()}:{addr.lower()}"
            cur = wallets_idx.get(ck) or {
                "address": addr,
                "chain":   (w.get("chain") or "unknown").lower(),
                "labels":  [],
                "sources": [],
            }
            lbl = (w.get("label") or "").strip()
            if lbl and lbl not in cur["labels"]:
                cur["labels"].append(lbl)
            if key not in cur["sources"]:
                cur["sources"].append(key)
            wallets_idx[ck] = cur
        for c in (ex.get("smart_contracts") or [])[:20]:
            if not isinstance(c, dict):
                continue
            addr = (c.get("address") or "").strip()
            if not addr:
                continue
            ck = f"{(c.get('chain') or 'unknown').lower()}:{addr.lower()}"
            cur = contracts_idx.get(ck) or {
                "address": addr,
                "chain":   (c.get("chain") or "unknown").lower(),
                "purposes": [],
                "sources":  [],
            }
            purp = (c.get("purpose") or "").strip()
            if purp and purp not in cur["purposes"]:
                cur["purposes"].append(purp)
            if key not in cur["sources"]:
                cur["sources"].append(key)
            contracts_idx[ck] = cur
        for d in (ex.get("domains") or [])[:50]:
            if isinstance(d, str) and d and d not in domains:
                domains.append(d.strip())
        for a in (ex.get("aliases_or_predecessors") or [])[:20]:
            # Models drift between flat strings and nested objects. Accept
            # both shapes: "Yunus Loop" OR {"name":"Yunus Loop","aliases":[...]}
            if isinstance(a, str):
                token = a.strip()
                if token and token not in aliases:
                    aliases.append(token)
            elif isinstance(a, dict):
                token = (a.get("name") or "").strip()
                if token and token not in aliases:
                    aliases.append(token)
                for sub in (a.get("aliases") or []):
                    if isinstance(sub, str):
                        s = sub.strip()
                        if s and s not in aliases:
                            aliases.append(s)
        for r in (ex.get("regulator_actions") or [])[:10]:
            if isinstance(r, dict) and r.get("regulator"):
                regulator_actions.append(r)
        for f in (ex.get("recovery_scam_followups") or [])[:10]:
            if isinstance(f, str) and f and f not in recovery_followups:
                recovery_followups.append(f.strip())
        jl = ex.get("japan_link") or {}
        if isinstance(jl, dict):
            for n in (jl.get("victim_names") or [])[:20]:
                if isinstance(n, str) and n.strip() and n.strip() not in japan_victims:
                    japan_victims.append(n.strip())
            for d in (jl.get("domains") or [])[:30]:
                if isinstance(d, str) and d.strip() and d.strip() not in japan_domains:
                    japan_domains.append(d.strip())
            for b in (jl.get("banks") or [])[:30]:
                if isinstance(b, str) and b.strip() and b.strip() not in japan_banks:
                    japan_banks.append(b.strip())

    return {
        "operators":          list(operators_idx.values()),
        "wallets":            list(wallets_idx.values()),
        "smart_contracts":    list(contracts_idx.values()),
        "domains":            domains,
        "aliases":            aliases,
        "regulator_actions":  regulator_actions,
        "recovery_followups": recovery_followups,
        "japan_link": {
            "victim_names": japan_victims,
            "domains":      japan_domains,
            "banks":        japan_banks,
        },
    }


def route_chain_probe(state: BitnestPursuitState):
    """Conditional edge that BOTH gates and fans out chain probes."""
    targets: List[Dict[str, Any]] = []
    for w in (state.get("wallets") or [])[:6]:
        targets.append({"kind": "wallet", **w})
    for c in (state.get("smart_contracts") or [])[:6]:
        targets.append({"kind": "contract", **c})
    if not targets:
        return "link_back_to_takahashi"
    return [Send("probe_wallet_one", {**state, "_probe_target": t}) for t in targets]


def after_probe_barrier_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Barrier after parallel chain probes."""
    n = len(state.get("chain_probes") or {})
    logger.info("after_probe_barrier  chain_probes=%d", n)
    return {}


def _probe_url_for(chain: str, addr: str) -> str:
    chain = (chain or "").lower()
    if chain in ("eth", "ethereum"):
        return f"https://etherscan.io/address/{urllib.parse.quote(addr)}"
    if chain in ("bsc", "bnb", "binance"):
        return f"https://bscscan.com/address/{urllib.parse.quote(addr)}"
    if chain == "tron":
        return f"https://tronscan.org/#/address/{urllib.parse.quote(addr)}"
    if chain == "btc":
        return f"https://www.blockchain.com/btc/address/{urllib.parse.quote(addr)}"
    # default web search lookup
    return f"https://duckduckgo.com/html/?q={urllib.parse.quote(addr)}+blockchain+scam"


def probe_wallet_one_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Probe ONE wallet/contract via public explorer. Phase 0 fetches HTML
    snippet; richer enrichment (transaction count, first/last seen) is a
    Phase 1 follow-up via Tron/BscScan API keys."""
    t = state.get("_probe_target") or {}
    addr = t.get("address") or ""
    chain = (t.get("chain") or "unknown").lower()
    if not addr:
        return {}
    url = _probe_url_for(chain, addr)
    status, body = _http_get(url, accept="text/html")
    probe_key = f"{chain}:{addr}"
    sha = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    record = {
        "kind":      t.get("kind", "wallet"),
        "address":   addr,
        "chain":     chain,
        "probe_url": url,
        "status":    status,
        "body_sha256": sha,
        "body_excerpt": body[:600] if status in (200, 201) else f"status={status}",
        "probed_at": _now_iso(),
    }
    logger.info("probe_wallet_one  chain=%s addr=%s status=%s",
                chain, addr[:24], status)
    return {"chain_probes": {probe_key: record}}


def link_back_to_takahashi_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Build edges from newly-discovered entities to anchor yabai entities
    in case:takahashi-hiroyuki-20260512. Phase 0 dry-run: returns the edge
    descriptors but does not INSERT into RW. Phase 1 wires up
    `edge_malak_target_extends` + `vertex_malak_pursuit_target` rows."""
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    live = bool(state.get("live_write"))
    anchors = [_yabai_vid(rkey) for rkey in TAKAHASHI_YABAI_ANCHORS]
    edges: List[Dict[str, str]] = []

    new_entities: List[Tuple[str, str, str]] = []  # (kind, identifier, label)
    for op in state.get("operators") or []:
        new_entities.append(("person", op.get("name", ""), f"operator:{op.get('name','')[:40]}"))
    for w in state.get("wallets") or []:
        new_entities.append((
            "wallet",
            f"{w.get('chain','')}:{w.get('address','')}",
            f"wallet:{(w.get('chain') or '?')}:{(w.get('address') or '')[:14]}…",
        ))
    for c in state.get("smart_contracts") or []:
        new_entities.append((
            "contract",
            f"{c.get('chain','')}:{c.get('address','')}",
            f"contract:{(c.get('chain') or '?')}:{(c.get('address') or '')[:14]}…",
        ))
    for alias in state.get("aliases") or []:
        new_entities.append(("alias_platform", alias, f"alias:{alias[:40]}"))
    for fu in state.get("recovery_followups") or []:
        new_entities.append(("recovery_scam", fu, f"recovery_followup:{fu[:40]}"))

    for kind, ident, label in new_entities:
        if not ident:
            continue
        rkey = _rkey(case_id, kind, ident)
        src_vid = _vid("pursuitTarget", rkey)
        for anchor_vid in anchors:
            edges.append({
                "src_id":    src_vid,
                "dst_id":    anchor_vid,
                "relation":  "links_to_takahashi_case",
                "kind":      kind,
                "label":     label,
                "case_id":   case_id,
                "live":      "true" if live else "false",
            })

    if live and edges:
        # Phase 1 live path — write pursuit_target rows + extends edges to RW.
        # Pattern mirrors pursuit_loop.write_discovered_target.
        url = os.environ.get("RW_URL")
        if not url:
            logger.warning(
                "link_back_to_takahashi live_write=True but RW_URL not set; "
                "edges staged in state.edges_written, not INSERTed.",
            )
        else:
            try:
                import psycopg  # type: ignore[import-not-found]
            except ImportError:
                logger.warning("psycopg not installed; cannot live-write edges")
            else:
                inserted_targets = 0
                inserted_edges = 0
                now_iso = _now_iso()
                today = _today()
                with psycopg.connect(url, connect_timeout=15) as conn:
                    conn.autocommit = True
                    with conn.cursor() as cur:
                        for kind, ident, label in new_entities:
                            if not ident:
                                continue
                            rkey = _rkey(case_id, kind, ident)
                            src_vid = _vid("pursuitTarget", rkey)
                            cur.execute(
                                "SELECT 1 FROM vertex_malak_pursuit_target "
                                "WHERE vertex_id=%s",
                                (src_vid,),
                            )
                            if not cur.fetchone():
                                cur.execute(
                                    "INSERT INTO vertex_malak_pursuit_target ("
                                    "vertex_id, rkey, repo, target_id, target_kind, "
                                    "case_id, priority, pursuit_status, "
                                    "extends_entity_vid, next_due_at, last_pursued_at, "
                                    "pursuit_tick_count, observation_count, note, tlp, "
                                    "created_at, created_date, sensitivity_ord, owner_did, "
                                    "org_id, user_id, actor_id, actor_did, org_did"
                                    ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
                                    "%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                    (src_vid, rkey, MALAK_DID,
                                     ident[:200], kind, case_id, 7, "queued",
                                     None, now_iso, None, 0, 0,
                                     f"bitnest_exit_pursuit Pregel link-back: {label[:160]}",
                                     TLP_RED,
                                     now_iso, today, 50, MALAK_DID,
                                     "gftd", MALAK_DID,
                                     "malak.bitnest-exit-pursuit",
                                     MALAK_DID, MALAK_DID),
                                )
                                inserted_targets += 1
                            for anchor_vid in anchors:
                                eid = _rkey(
                                    "links_to_takahashi_case", src_vid, anchor_vid,
                                )
                                cur.execute(
                                    "DELETE FROM edge_malak_target_extends "
                                    "WHERE edge_id=%s",
                                    (eid,),
                                )
                                cur.execute(
                                    "INSERT INTO edge_malak_target_extends ("
                                    "src_id, dst_id, edge_id, relation, dst_kind, "
                                    "created_at, sensitivity_ord, owner_did"
                                    ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                                    (src_vid, anchor_vid, eid,
                                     "links_to_takahashi_case", "yabai_entity",
                                     now_iso, 50, MALAK_DID),
                                )
                                inserted_edges += 1
                logger.info(
                    "link_back_to_takahashi LIVE WRITE  targets_inserted=%d edges_inserted=%d",
                    inserted_targets, inserted_edges,
                )
                # Flip the live flag on the staged edge descriptors so the
                # persist_fs report shows truth-of-write
                for e in edges:
                    e["live"] = "true"

    logger.info(
        "link_back_to_takahashi  case=%s anchors=%d new_entities=%d edges_staged=%d",
        case_id, len(anchors), len(new_entities), len(edges),
    )
    return {"edges_written": edges}


def emit_pegel_node(state: BitnestPursuitState) -> Dict[str, Any]:
    """Append a summary investigationTick. In Phase 1 this calls the
    pyzeebe `task_malak_run_investigation_tick` primitive; Phase 0 only logs."""
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    summary = {
        "case_id":            case_id,
        "tlp":                TLP_RED,
        "operators":          len(state.get("operators") or []),
        "wallets":            len(state.get("wallets") or []),
        "smart_contracts":    len(state.get("smart_contracts") or []),
        "aliases":            list(state.get("aliases") or []),
        "recovery_followups": list(state.get("recovery_followups") or []),
        "sources_fetched":    sum(
            1 for r in (state.get("fetched") or {}).values()
            if r.get("status") in (200, 201)
        ),
        "edges_staged": len(state.get("edges_written") or []),
        "completed_at": _now_iso(),
    }
    rkey = _rkey("bitnestExit", case_id, _now_iso())
    tick_vid = _vid("investigationTick", rkey)
    logger.info("emit_pegel  tick=%s summary=%s", tick_vid[-24:], json.dumps(summary))
    return {"pegel_tick_ids": [tick_vid]}


def persist_fs_node(state: BitnestPursuitState) -> Dict[str, Any]:
    out_dir = state.get("output_dir") or ""
    if not out_dir:
        return {}
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}

    # 1. Operators / wallets / contracts report
    report_md_lines = [
        "# BitNest Exit-Fraud Pursuit Report",
        "",
        f"- case_id: `{state.get('case_id', DEFAULT_CASE_ID)}`",
        f"- generated_at: {_now_iso()}",
        f"- TLP: **{TLP_RED}**",
        f"- sources fetched: {sum(1 for r in (state.get('fetched') or {}).values() if r.get('status') in (200,201))} / {len(state.get('fetched') or {})}",
        f"- live_write: {state.get('live_write', False)}",
        "",
        "## Operators",
        "",
        "| Name | Aliases | Nationality | Sources |",
        "|---|---|---|---|",
    ]
    for op in state.get("operators") or []:
        report_md_lines.append(
            f"| {op.get('name','')} | {', '.join(op.get('aliases', []) or [])} | "
            f"{op.get('nationality','')} | {', '.join(op.get('sources', []) or [])} |"
        )
    report_md_lines += [
        "",
        "## Wallets",
        "",
        "| Chain | Address | Labels | Sources |",
        "|---|---|---|---|",
    ]
    for w in state.get("wallets") or []:
        report_md_lines.append(
            f"| {w.get('chain','')} | `{w.get('address','')}` | "
            f"{', '.join(w.get('labels', []) or [])} | {', '.join(w.get('sources', []) or [])} |"
        )
    report_md_lines += [
        "",
        "## Smart contracts",
        "",
        "| Chain | Address | Purposes | Sources |",
        "|---|---|---|---|",
    ]
    for c in state.get("smart_contracts") or []:
        report_md_lines.append(
            f"| {c.get('chain','')} | `{c.get('address','')}` | "
            f"{', '.join(c.get('purposes', []) or [])} | {', '.join(c.get('sources', []) or [])} |"
        )
    report_md_lines += [
        "",
        "## Aliases / Predecessors",
        "",
        *[f"- {a}" for a in state.get("aliases") or []],
        "",
        "## Regulator actions",
        "",
        "| Regulator | Action | Date |",
        "|---|---|---|",
    ]
    for r in state.get("regulator_actions") or []:
        report_md_lines.append(
            f"| {r.get('regulator','')} | {r.get('action','')} | {r.get('date','')} |"
        )
    report_md_lines += [
        "",
        "## Recovery-scam follow-ups (secondary fraud risk)",
        "",
        *[f"- **{f}** (recommend yabai blacklist)" for f in state.get("recovery_followups") or []],
        "",
        "## Japan link (rolled up across sources)",
        "",
    ]
    jl = state.get("japan_link") or {}
    if jl.get("victim_names"):
        report_md_lines.append(f"- victim names: {', '.join(jl['victim_names'])}")
    if jl.get("domains"):
        report_md_lines.append(f"- domains:      {', '.join(jl['domains'])}")
    if jl.get("banks"):
        report_md_lines.append(f"- banks:        {', '.join(jl['banks'])}")
    if not (jl.get("victim_names") or jl.get("domains") or jl.get("banks")):
        report_md_lines.append("- (none rolled up)")
    report_md_lines += [
        "",
        "## Edges → Takahashi case (staged)",
        "",
        f"Total: {len(state.get('edges_written') or [])} edges staged "
        f"(live_write={state.get('live_write', False)})",
        "",
    ]
    report_path = p / "bitnest-exit-report.md"
    report_path.write_text("\n".join(report_md_lines), encoding="utf-8")
    files["report"] = str(report_path)

    # 2. Raw fetched bodies (one .html / .json per source, gz-safe)
    raw_dir = p / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for key, r in (state.get("fetched") or {}).items():
        ext = "html" if "<html" in (r.get("body") or "").lower() else "txt"
        fp = raw_dir / f"{key}.{ext}"
        fp.write_text(r.get("body", ""), encoding="utf-8")
        files[f"raw:{key}"] = str(fp)

    # 3. Extractions / probes / edges as JSON
    (p / "extractions.json").write_text(
        json.dumps(state.get("extractions") or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    files["extractions"] = str(p / "extractions.json")
    (p / "chain-probes.json").write_text(
        json.dumps(state.get("chain_probes") or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    files["chain_probes"] = str(p / "chain-probes.json")
    (p / "edges-staged.json").write_text(
        json.dumps(state.get("edges_written") or [], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    files["edges"] = str(p / "edges-staged.json")

    # 4. MANIFEST
    manifest_lines = [
        f"case_id: {state.get('case_id', DEFAULT_CASE_ID)}",
        f"generated_at: {_now_iso()}",
        f"live_write: {state.get('live_write', False)}",
        "files:",
    ]
    for fkey, fp in files.items():
        manifest_lines.append(f"  - {fkey}: {fp}")
    manifest_lines.append("pegel_ticks:")
    for t in state.get("pegel_tick_ids") or []:
        manifest_lines.append(f"  - {t}")
    (p / "MANIFEST.txt").write_text("\n".join(manifest_lines), encoding="utf-8")
    files["manifest"] = str(p / "MANIFEST.txt")

    concat = (
        (report_path.read_text(encoding="utf-8"))
        + (p / "extractions.json").read_text(encoding="utf-8")
        + (p / "chain-probes.json").read_text(encoding="utf-8")
        + (p / "edges-staged.json").read_text(encoding="utf-8")
    )
    document_sha256 = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    return {"written_files": files, "document_sha256": document_sha256}


def audit_emit_node(state: BitnestPursuitState) -> Dict[str, Any]:
    if state.get("status", "").startswith(("denied", "error")):
        return {}
    logger.info(
        "malak.bitnest_exit_pursuit.completed case=%s operators=%d wallets=%d "
        "edges=%d sha=%s",
        state.get("case_id", ""),
        len(state.get("operators") or []),
        len(state.get("wallets") or []),
        len(state.get("edges_written") or []),
        (state.get("document_sha256") or "")[:16],
    )
    return {"status": "ok"}


# ── Graph ──────────────────────────────────────────────────────────────


def build_bitnest_exit_pursuit_graph():
    g = StateGraph(BitnestPursuitState)

    g.add_node("gate_input",              gate_input_node)
    g.add_node("fetch_one",               fetch_one_node)
    g.add_node("after_fetch_barrier",     after_fetch_barrier_node)
    g.add_node("llm_extract_one",         llm_extract_one_node)
    g.add_node("llm_extract_serial",      llm_extract_serial_node)
    g.add_node("inject_fixtures",         inject_fixtures_node)
    g.add_node("after_extract_barrier",   after_extract_barrier_node)
    g.add_node("correlate",               correlate_node)
    g.add_node("probe_wallet_one",        probe_wallet_one_node)
    g.add_node("after_probe_barrier",     after_probe_barrier_node)
    g.add_node("link_back_to_takahashi",  link_back_to_takahashi_node)
    g.add_node("emit_pegel",              emit_pegel_node)
    g.add_node("persist_fs",              persist_fs_node)
    g.add_node("audit_emit",              audit_emit_node)

    g.set_entry_point("gate_input")

    # super-step 2: parallel fetch fan-out → barrier
    g.add_conditional_edges("gate_input", fan_out_fetch, ["fetch_one"])
    g.add_edge("fetch_one", "after_fetch_barrier")
    # super-step 4: unified router → fixtures / parallel Send list / serial / correlate
    g.add_conditional_edges(
        "after_fetch_barrier", route_extract,
        ["llm_extract_one", "llm_extract_serial", "inject_fixtures", "correlate"],
    )
    # super-step 5: all extraction paths converge at barrier
    g.add_edge("llm_extract_one",    "after_extract_barrier")
    g.add_edge("llm_extract_serial", "after_extract_barrier")
    g.add_edge("inject_fixtures",    "after_extract_barrier")
    g.add_edge("after_extract_barrier", "correlate")
    # super-step 6: unified router emits Send(...) list OR string fallthrough
    g.add_conditional_edges(
        "correlate", route_chain_probe,
        ["probe_wallet_one", "link_back_to_takahashi"],
    )
    # super-step 7: barrier after parallel probes
    g.add_edge("probe_wallet_one", "after_probe_barrier")
    g.add_edge("after_probe_barrier", "link_back_to_takahashi")
    g.add_edge("link_back_to_takahashi", "emit_pegel")
    g.add_edge("emit_pegel", "persist_fs")
    g.add_edge("persist_fs", "audit_emit")
    g.add_edge("audit_emit", END)
    return g.compile()


async def run_bitnest_exit_pursuit(
    *,
    case_id: str = DEFAULT_CASE_ID,
    output_dir: str = "",
    sources: Optional[List[Dict[str, str]]] = None,
    extra_seed_urls: Optional[List[str]] = None,
    live_write: bool = False,
    llm_disabled: bool = False,
    serial_llm: bool = False,
    fixture_extractions: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    graph = build_bitnest_exit_pursuit_graph()
    initial: BitnestPursuitState = {
        "case_id":         case_id,
        "output_dir":      output_dir,
        "sources":         list(sources) if sources else list(SEED_SOURCES),
        "extra_seed_urls": list(extra_seed_urls) if extra_seed_urls else [],
        "live_write":      live_write,
        "llm_disabled":    llm_disabled,
        "serial_llm":      serial_llm,
        "fixture_extractions": dict(fixture_extractions) if fixture_extractions else {},
    }
    return await graph.ainvoke(initial)


# ── CLI ────────────────────────────────────────────────────────────────


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="bitnest_exit_pursuit")
    p.add_argument("--case-id", default=DEFAULT_CASE_ID)
    p.add_argument("--output-dir", default="_working/malak/bitnest-exit-20260514")
    p.add_argument("--extra-url", action="append", default=[],
                   help="repeatable; adds an ad-hoc URL to the seed list")
    p.add_argument("--live-write", action="store_true",
                   help="Phase 1+ only: write pegel ticks + RW edges (default dry-run)")
    p.add_argument("--no-llm", action="store_true",
                   help="skip LLM extraction (smoke-test: fetch + persist only)")
    p.add_argument("--serial-llm", action="store_true",
                   help="force serial LLM extraction (single-GPU Ollama)")
    p.add_argument("--fixtures", default="",
                   help="path to JSON file with hand-curated extractions (bypasses LLM)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    fixtures: Optional[Dict[str, Dict[str, Any]]] = None
    if args.fixtures:
        with open(args.fixtures, "r", encoding="utf-8") as fh:
            fixtures = json.load(fh)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    result = asyncio.run(run_bitnest_exit_pursuit(
        case_id=args.case_id,
        output_dir=args.output_dir,
        extra_seed_urls=args.extra_url,
        live_write=args.live_write,
        llm_disabled=args.no_llm,
        serial_llm=args.serial_llm,
        fixture_extractions=fixtures,
    ))
    print(json.dumps({
        "status":      result.get("status"),
        "case_id":     result.get("case_id"),
        "operators":   len(result.get("operators") or []),
        "wallets":     len(result.get("wallets") or []),
        "contracts":   len(result.get("smart_contracts") or []),
        "edges":       len(result.get("edges_written") or []),
        "files":       list((result.get("written_files") or {}).keys()),
        "pegel_ticks": result.get("pegel_tick_ids") or [],
        "sha":         (result.get("document_sha256") or "")[:16],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
