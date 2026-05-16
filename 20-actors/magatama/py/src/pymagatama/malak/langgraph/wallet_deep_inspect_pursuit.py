"""wallet_deep_inspect_pursuit — Pregel for whale + protocol classifier.

Given a target BSC address (typically high-balance or high-tx, surfaced by
upstream Pregel `bitnest_exit_pursuit` etc.), determine the address's
classification, beneficial-ownership signals, top counterparties, and risk
score.

Topology (7 super-steps; ADR-2605152000):

  gate_input
    ↓ (1) sequential
  fetch_address_meta
    ↓ (2) BSP parallel — Send × N pages of /txs?a=<addr>&p={i}
  fan_out_fetch_pages → fetch_page_one
    ↓ (3) implicit barrier
  collect_and_dedupe
    ↓ (4) BSP parallel — Send × top K counterparties
  fan_out_label_top_K → label_counterparty_one
    ↓ (5) implicit barrier
  classify
    ↓
  link_back_to_case
    ↓
  emit_pegel + persist_fs + audit_emit → END

Phase 0 default: live_write=False, dry-run. Phase 1 flips RW INSERTs on.

CLI:
  python -m pymagatama.malak.langgraph.wallet_deep_inspect_pursuit \\
      --target 0x06f3fffe777d69c0575bf51357d2e965f6385d9b \\
      --case-id case:takahashi-hiroyuki-20260512 \\
      --output-dir _working/malak/wallet-deep-inspect-20260515-06f3fffe
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
import re
import time
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

# Yabai anchors for case-anchored link-back. Same convention as bitnest_exit_pursuit.
CASE_ANCHORS: Dict[str, Tuple[str, ...]] = {
    "case:takahashi-hiroyuki-20260512": (
        "hiroyuki-bitnest-app",
        "hiroyuki-bitnest-ex-com",
        "hiroyuki-leedsil-com",
        "hiroyuki-leedsec-com",
        "hiroyuki-leeds-securities",
        "hiroyuki-jpevaluation-net",
    ),
}

# Classification confidence by class
CLASSIFICATION_CONFIDENCE = {
    "cex_cold": 0.95, "cex_hot": 0.90, "cex_unknown": 0.85,
    "dex_router": 0.95, "bridge_pool": 0.85, "protocol_pool": 0.80,
    "whale_eoa": 0.60, "mixer": 0.95, "sanctioned": 0.95,
    "unverified_contract": 0.30, "unknown_eoa": 0.30,
}

CEX_NAME_TAGS = (
    "Binance", "OKX", "Bybit", "Bitget", "Coinbase", "Kraken",
    "Huobi", "KuCoin", "Gate.io", "Bitfinex", "MEXC", "Bithumb",
    "BingX", "WhiteBIT", "Bitmart", "Crypto.com",
    "WazirX", "CoinDCX", "Mudrex", "Bitbns", "Vauld",
)

DEX_INFRA_TAGS = (
    "PancakeSwap", "Uniswap", "Biswap", "BakerySwap", "SushiSwap",
    "Router", "MasterChef", "Earn", "Farm", "WBNB", "BUSD", "USDT",
)

BRIDGE_TAGS = (
    "Multichain Bridge", "Stargate Bridge", "Hop Protocol",
    "Across Protocol", "Axelar", "deBridge",
    "Synapse Bridge", "Wormhole",
)


# ── Reducers ──────────────────────────────────────────────────────────


def _merge_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    if not a: return dict(b or {})
    if not b: return dict(a)
    out = dict(a)
    out.update(b)
    return out


def _merge_list(a: List[Any], b: List[Any]) -> List[Any]:
    out = list(a or [])
    if b: out.extend(b)
    return out


# ── State ─────────────────────────────────────────────────────────────


class WalletDeepInspectState(TypedDict, total=False):
    # input
    case_id: str
    target_address: str
    max_pages: int            # default 5 (= 500 tx)
    top_k_counterparties: int # default 20
    llm_disabled: bool
    live_write: bool
    output_dir: str
    # internal (parallel channels)
    address_meta: Dict[str, Any]
    pages: Annotated[Dict[int, Dict[str, Any]], _merge_dict]
    counterparties: Dict[str, Dict[str, Any]]  # built sequentially from pages
    labels: Annotated[Dict[str, Dict[str, Any]], _merge_dict]
    # output
    classification: str
    classification_confidence: float
    observation_vids: Annotated[List[str], _merge_list]
    edges_written: List[Dict[str, Any]]
    pegel_tick_ids: List[str]
    written_files: Dict[str, str]
    document_sha256: str
    status: str
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
    return f"at://{YABAI_DID}/ai.gftd.apps.yabai.entity/{rkey}"


def _http_get(url: str, *, timeout: int = 30) -> Tuple[int, str]:
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")[:2000000]
    except Exception as e:  # noqa: BLE001
        return -1, f"err: {type(e).__name__}: {str(e)[:300]}"


# ── Nodes ──────────────────────────────────────────────────────────────


def gate_input_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    if not state.get("target_address"):
        return {"status": "error", "error": "target_address is required"}
    if not re.match(r"^0x[a-fA-F0-9]{40}$", state["target_address"]):
        return {"status": "error", "error": f"invalid target_address: {state['target_address']}"}
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    return {
        "case_id":               case_id,
        "max_pages":             int(state.get("max_pages") or 5),
        "top_k_counterparties":  int(state.get("top_k_counterparties") or 20),
        "address_meta":          {},
        "pages":                 {},
        "counterparties":        {},
        "labels":                {},
        "observation_vids":      [],
        "edges_written":         [],
        "pegel_tick_ids":        [],
        "written_files":         {},
    }


def fetch_address_meta_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    addr = state["target_address"]
    url = f"https://bscscan.com/address/{addr}"
    status, body = _http_get(url)
    meta = {"url": url, "status": status, "title": "", "og_description": "",
            "balance_usd": "?", "tx_count": "?", "is_contract": False,
            "verified": False, "name_tag": "", "labels": []}
    if status == 200:
        m = re.search(r'<title>([^<]+)</title>', body)
        meta["title"] = (m.group(1).strip() if m else "")[:200]
        m = re.search(r'og:description"\s+content="([^"]+)"', body)
        if m:
            meta["og_description"] = m.group(1)[:400]
        m = re.search(r'Balance:\s*\$?([\d,]+(?:\.\d+)?)', body)
        if m: meta["balance_usd"] = m.group(1)
        m = re.search(r'Transactions:\s*([\d,]+)', body)
        if m: meta["tx_count"] = m.group(1)
        meta["is_contract"] = "Contract" in body and "Contract Source Code" in body.lower() or "contract: verified" in body.lower()
        meta["verified"] = "<i class=\"fa-solid fa-check\"" in body or "Verified" in (meta.get("og_description") or "")
        for tag in re.findall(r'data-bs-toggle="tooltip"\s+data-bs-title="([^"]+)"', body)[:30]:
            if any(p in tag for p in (*CEX_NAME_TAGS, *DEX_INFRA_TAGS, *BRIDGE_TAGS)):
                meta["labels"].append(tag[:120])
    logger.info("fetch_address_meta  target=%s bal=$%s tx=%s labels=%d",
                addr, meta["balance_usd"], meta["tx_count"], len(meta["labels"]))
    return {"address_meta": meta}


def fan_out_fetch_pages(state: WalletDeepInspectState):
    n = state.get("max_pages") or 5
    return [Send("fetch_page_one", {**state, "_page": p}) for p in range(1, n + 1)]


def fetch_page_one_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    addr = state["target_address"]
    page = int(state["_page"])
    url = f"https://bscscan.com/txs?a={addr}&ps=100&p={page}"
    time.sleep(0.5 + 0.1 * page)  # rate-limit politeness, stagger
    status, body = _http_get(url)
    rows: List[Dict[str, Any]] = []
    if status == 200:
        tr_blocks = re.findall(r'<tr[^>]*>(.*?)</tr>', body, re.DOTALL)
        for tr in tr_blocks:
            tx_m = re.search(r'/tx/(0x[a-fA-F0-9]{64})', tr)
            if not tx_m:
                continue
            addrs = []
            for a in re.findall(r'/address/(0x[a-fA-F0-9]{40})', tr):
                la = a.lower()
                if la == addr.lower() or la in {x.lower() for x in addrs}:
                    continue
                addrs.append(a)
            if not addrs:
                continue
            val_m = re.search(r'>([\d,]+(?:\.\d+)?)\s*(BNB|USDT|BUSD|USDC)\b', tr)
            ts_m = re.search(r'data-bs-toggle="tooltip"\s+data-bs-title="(\d{4}-\d{2}-\d{2}[^"]*)"', tr)
            rows.append({
                "tx_hash": tx_m.group(1),
                "counterparty": addrs[0],
                "value": f"{val_m.group(1)} {val_m.group(2)}" if val_m else "",
                "timestamp": ts_m.group(1) if ts_m else "",
            })
    logger.info("fetch_page_one  page=%d status=%s rows=%d", page, status, len(rows))
    return {"pages": {page: {"status": status, "rows": rows}}}


def after_fetch_pages_barrier_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    pages = state.get("pages") or {}
    total_rows = sum(len(p.get("rows", [])) for p in pages.values())
    logger.info("after_fetch_pages_barrier  pages=%d total_rows=%d", len(pages), total_rows)
    return {}


def collect_and_dedupe_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    """Aggregate paginated tx rows into per-counterparty stats."""
    cps: Dict[str, Dict[str, Any]] = {}
    for page, data in (state.get("pages") or {}).items():
        for row in data.get("rows", []):
            cp = row["counterparty"].lower()
            entry = cps.setdefault(cp, {
                "address": row["counterparty"],
                "tx_count": 0, "first_seen": "", "last_seen": "",
                "sample_tx_hashes": [],
            })
            entry["tx_count"] += 1
            ts = row.get("timestamp", "")
            if ts:
                if not entry["first_seen"] or ts < entry["first_seen"]:
                    entry["first_seen"] = ts
                if not entry["last_seen"] or ts > entry["last_seen"]:
                    entry["last_seen"] = ts
            if len(entry["sample_tx_hashes"]) < 3:
                entry["sample_tx_hashes"].append(row["tx_hash"])
    logger.info("collect_and_dedupe  counterparties=%d", len(cps))
    return {"counterparties": cps}


def fan_out_label_top_K(state: WalletDeepInspectState):
    cps = state.get("counterparties") or {}
    k = state.get("top_k_counterparties") or 20
    top = sorted(cps.values(), key=lambda x: -x["tx_count"])[:k]
    return [Send("label_counterparty_one", {**state, "_counterparty": cp}) for cp in top]


def label_counterparty_one_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    cp = state["_counterparty"]
    addr = cp["address"]
    time.sleep(0.5)
    url = f"https://bscscan.com/address/{addr}"
    status, body = _http_get(url)
    info: Dict[str, Any] = {"address": addr, "url": url, "status": status,
                            "labels": [], "title": "", "balance_usd": "?",
                            "tx_count": "?", "is_contract": False, "verified": False,
                            "name_tag": ""}
    if status == 200:
        m = re.search(r'<title>([^<]+)</title>', body)
        info["title"] = (m.group(1).strip() if m else "")[:200]
        m = re.search(r'og:description"\s+content="([^"]+)"', body)
        if m: info["og_description"] = m.group(1)[:400]
        m = re.search(r'Balance:\s*\$?([\d,]+(?:\.\d+)?)', body)
        if m: info["balance_usd"] = m.group(1)
        m = re.search(r'Transactions:\s*([\d,]+)', body)
        if m: info["tx_count"] = m.group(1)
        info["is_contract"] = "Contract Source Code" in body.lower() or "contract: verified" in body.lower()
        info["verified"] = "<i class=\"fa-solid fa-check\"" in body
        for tag in re.findall(r'data-bs-toggle="tooltip"\s+data-bs-title="([^"]+)"', body)[:30]:
            if any(p in tag for p in (*CEX_NAME_TAGS, *DEX_INFRA_TAGS, *BRIDGE_TAGS)):
                info["labels"].append(tag[:120])
    return {"labels": {addr.lower(): info}}


def after_label_barrier_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    logger.info("after_label_barrier  labels=%d", len(state.get("labels") or {}))
    return {}


def classify_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    """Classify the TARGET address (not the counterparties; counterparties are
    just signals)."""
    meta = state.get("address_meta") or {}
    # combine target labels + sampled counterparty labels for signal
    target_text = " ".join([
        meta.get("title", ""),
        meta.get("og_description", ""),
        *meta.get("labels", []),
    ]).lower()
    bal = 0.0
    if meta.get("balance_usd") and meta["balance_usd"] != "?":
        try: bal = float(meta["balance_usd"].replace(",", ""))
        except Exception: pass  # noqa: BLE001
    tx = 0
    if meta.get("tx_count") and meta["tx_count"] != "?":
        try: tx = int(meta["tx_count"].replace(",", ""))
        except Exception: pass  # noqa: BLE001

    if any(p.lower() in target_text for p in CEX_NAME_TAGS):
        cls = "cex_hot" if tx > 1000 else "cex_unknown"
    elif any(p.lower() in target_text for p in BRIDGE_TAGS):
        cls = "bridge_pool"
    elif any(p.lower() in target_text for p in DEX_INFRA_TAGS):
        cls = "dex_router"
    elif meta.get("is_contract") and not meta.get("verified"):
        cls = "unverified_contract"
    elif bal > 1_000_000 and tx > 1000 and not meta.get("is_contract"):
        cls = "whale_eoa"
    elif tx == 0 and bal == 0:
        cls = "unknown_eoa"
    else:
        cls = "unknown_eoa"

    conf = CLASSIFICATION_CONFIDENCE.get(cls, 0.30)
    logger.info("classify  target=%s class=%s conf=%.2f  bal=$%s tx=%d",
                state["target_address"], cls, conf, bal, tx)
    return {"classification": cls, "classification_confidence": conf}


def link_back_to_case_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    anchors_rkeys = CASE_ANCHORS.get(case_id, ())
    anchor_vids = [_yabai_vid(rk) for rk in anchors_rkeys]
    target = state["target_address"]
    cls = state.get("classification") or "unknown_eoa"
    ident = f"bsc:{target}"
    rkey = _rkey(case_id, "wallet", ident)
    target_vid = _vid("pursuitTarget", rkey)
    edges = [{
        "src_id":    target_vid,
        "dst_id":    av,
        "relation":  "links_to_takahashi_case",
        "kind":      cls,
        "label":     f"wallet_deep_inspect:{cls}",
        "case_id":   case_id,
        "live":      "false",
    } for av in anchor_vids]
    if state.get("live_write") and (url := os.environ.get("RW_URL")):
        try:
            import psycopg  # type: ignore[import-not-found]
        except ImportError:
            logger.warning("psycopg not installed; skipping RW writes")
        else:
            now_iso = _now_iso()
            today = _today()
            with psycopg.connect(url, connect_timeout=15) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM vertex_malak_pursuit_target WHERE vertex_id=%s", (target_vid,))
                    if not cur.fetchone():
                        cur.execute(
                            "INSERT INTO vertex_malak_pursuit_target ("
                            "vertex_id, rkey, repo, target_id, target_kind, case_id, "
                            "priority, pursuit_status, extends_entity_vid, next_due_at, "
                            "last_pursued_at, pursuit_tick_count, observation_count, "
                            "note, tlp, created_at, created_date, sensitivity_ord, "
                            "owner_did, org_id, user_id, actor_id, actor_did, org_did) "
                            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (target_vid, rkey, MALAK_DID, ident, cls, case_id, 13, "queued",
                             None, now_iso, None, 0, 0,
                             f"wallet_deep_inspect:{cls}:{target[:24]}", TLP_RED,
                             now_iso, today, 50, MALAK_DID, "gftd", MALAK_DID,
                             "malak.wallet-deep-inspect", MALAK_DID, MALAK_DID),
                        )
                    for av in anchor_vids:
                        eid = _rkey("links_to_takahashi_case", target_vid, av)
                        cur.execute("DELETE FROM edge_malak_target_extends WHERE edge_id=%s", (eid,))
                        cur.execute(
                            "INSERT INTO edge_malak_target_extends ("
                            "src_id, dst_id, edge_id, relation, dst_kind, "
                            "created_at, sensitivity_ord, owner_did) "
                            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                            (target_vid, av, eid, "links_to_takahashi_case",
                             "yabai_entity", now_iso, 50, MALAK_DID),
                        )
            for e in edges:
                e["live"] = "true"
    logger.info("link_back_to_case  edges=%d (live_write=%s)", len(edges), state.get("live_write", False))
    return {"edges_written": edges}


def emit_pegel_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    rkey = _rkey("walletDeepInspect", case_id, state["target_address"], _now_iso())
    tick_vid = _vid("investigationTick", rkey)
    logger.info("emit_pegel  tick=%s  target=%s class=%s",
                tick_vid[-24:], state["target_address"], state.get("classification"))
    return {"pegel_tick_ids": [tick_vid]}


def persist_fs_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    out_dir = state.get("output_dir") or ""
    if not out_dir: return {}
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    findings = {
        "case_id": state.get("case_id"),
        "target_address": state["target_address"],
        "classification": state.get("classification"),
        "classification_confidence": state.get("classification_confidence"),
        "address_meta": state.get("address_meta", {}),
        "counterparty_count": len(state.get("counterparties") or {}),
        "top_counterparties": sorted(
            (state.get("counterparties") or {}).values(),
            key=lambda x: -x.get("tx_count", 0),
        )[:20],
        "labels": state.get("labels", {}),
        "edges_staged": state.get("edges_written") or [],
        "pegel_ticks": state.get("pegel_tick_ids") or [],
    }
    out_path = p / "wallet-deep-inspect-findings.json"
    out_path.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    return {"written_files": {"findings": str(out_path)}, "document_sha256": sha}


def audit_emit_node(state: WalletDeepInspectState) -> Dict[str, Any]:
    if state.get("status", "").startswith(("denied", "error")):
        return {}
    logger.info(
        "malak.wallet_deep_inspect.completed target=%s class=%s cps=%d edges=%d sha=%s",
        state.get("target_address", ""),
        state.get("classification", ""),
        len(state.get("counterparties") or {}),
        len(state.get("edges_written") or []),
        (state.get("document_sha256") or "")[:16],
    )
    return {"status": "ok"}


# ── Graph ──────────────────────────────────────────────────────────────


def build_wallet_deep_inspect_graph():
    g = StateGraph(WalletDeepInspectState)
    g.add_node("gate_input", gate_input_node)
    g.add_node("fetch_address_meta", fetch_address_meta_node)
    g.add_node("fetch_page_one", fetch_page_one_node)
    g.add_node("after_fetch_pages_barrier", after_fetch_pages_barrier_node)
    g.add_node("collect_and_dedupe", collect_and_dedupe_node)
    g.add_node("label_counterparty_one", label_counterparty_one_node)
    g.add_node("after_label_barrier", after_label_barrier_node)
    g.add_node("classify", classify_node)
    g.add_node("link_back_to_case", link_back_to_case_node)
    g.add_node("emit_pegel", emit_pegel_node)
    g.add_node("persist_fs", persist_fs_node)
    g.add_node("audit_emit", audit_emit_node)

    g.set_entry_point("gate_input")
    g.add_edge("gate_input", "fetch_address_meta")
    g.add_conditional_edges("fetch_address_meta", fan_out_fetch_pages, ["fetch_page_one"])
    g.add_edge("fetch_page_one", "after_fetch_pages_barrier")
    g.add_edge("after_fetch_pages_barrier", "collect_and_dedupe")
    g.add_conditional_edges("collect_and_dedupe", fan_out_label_top_K, ["label_counterparty_one"])
    g.add_edge("label_counterparty_one", "after_label_barrier")
    g.add_edge("after_label_barrier", "classify")
    g.add_edge("classify", "link_back_to_case")
    g.add_edge("link_back_to_case", "emit_pegel")
    g.add_edge("emit_pegel", "persist_fs")
    g.add_edge("persist_fs", "audit_emit")
    g.add_edge("audit_emit", END)
    return g.compile()


async def run_wallet_deep_inspect(
    *, target_address: str,
    case_id: str = DEFAULT_CASE_ID,
    max_pages: int = 5,
    top_k_counterparties: int = 20,
    llm_disabled: bool = False,
    live_write: bool = False,
    output_dir: str = "",
) -> Dict[str, Any]:
    graph = build_wallet_deep_inspect_graph()
    initial: WalletDeepInspectState = {
        "target_address": target_address,
        "case_id": case_id,
        "max_pages": max_pages,
        "top_k_counterparties": top_k_counterparties,
        "llm_disabled": llm_disabled,
        "live_write": live_write,
        "output_dir": output_dir,
    }
    return await graph.ainvoke(initial)


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="wallet_deep_inspect_pursuit")
    p.add_argument("--target", required=True)
    p.add_argument("--case-id", default=DEFAULT_CASE_ID)
    p.add_argument("--max-pages", type=int, default=5)
    p.add_argument("--top-k", type=int, default=20)
    p.add_argument("--live-write", action="store_true")
    p.add_argument("--output-dir", default="")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    result = asyncio.run(run_wallet_deep_inspect(
        target_address=args.target,
        case_id=args.case_id,
        max_pages=args.max_pages,
        top_k_counterparties=args.top_k,
        live_write=args.live_write,
        output_dir=args.output_dir,
    ))
    print(json.dumps({
        "status": result.get("status"),
        "target": result.get("target_address"),
        "classification": result.get("classification"),
        "confidence": result.get("classification_confidence"),
        "counterparty_count": len(result.get("counterparties") or {}),
        "labels": len(result.get("labels") or {}),
        "edges": len(result.get("edges_written") or []),
        "files": list((result.get("written_files") or {}).keys()),
        "pegel_ticks": result.get("pegel_tick_ids") or [],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
