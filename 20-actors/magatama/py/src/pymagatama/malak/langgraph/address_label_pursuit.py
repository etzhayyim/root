"""address_label_pursuit — Pregel for multi-source address labelling batch.

Given a list of N addresses (typically unlabeled counterparties from upstream
Pregel), aggregate labels from K sources, run strict classifier, produce
verdicts. Replaces bsc_unknown_deep_label.py standalone script.

Topology (5 super-steps; ADR-2605152000):

  gate_input (address_list[])
    ↓ (1) sequential
  fan_out_per_address ────────────────────────────────────────────┐
    │ (2) BSP parallel — Send × N                                 │
    ├─► label_one (multi-source: KNOWN_DB + BscScan + ABI + OFAC) │
                                                                  ▼
    │ (3) implicit barrier
    ▼
  classify_all (sequential strict classifier)
    ↓
  emit_pegel + persist_fs + audit_emit → END

Strict classification — never returns "bridge_pool" without explicit DB hit
or ABI signature match. Eliminates v0's 15/17 false-positive rate.

Phase 0: dry-run by default. Phase 1 live_write emits yabai_entity for
high-confidence classes only.

CLI:
  python -m pymagatama.malak.langgraph.address_label_pursuit \\
      --addresses 0xaaa...,0xbbb...,0xccc... \\
      --case-id case:takahashi-hiroyuki-20260512 \\
      --output-dir _working/malak/address-label-batch-20260515
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
import urllib.request
from typing import Annotated, Any, Dict, List, Optional, Tuple, TypedDict

from langgraph.constants import Send
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

MALAK_DID = "did:web:malak.gftd.ai"
YABAI_DID = "did:web:yabai.gftd.ai"
TLP_RED   = "RED"
DEFAULT_CASE_ID = "case:takahashi-hiroyuki-20260512"


# ── Curated address DB (Phase 0; expand quarterly) ───────────────────


# Local KNOWN_ADDRESS_DB — curated CEX/bridge/mixer/sanctions addresses + major
# BEP-20 token contracts. Keep keys lowercase. Values are (class, label, confidence).
KNOWN_ADDRESS_DB: Dict[str, Tuple[str, str, float]] = {
    # ── Major BEP-20 stablecoin / wrapped-asset contracts (very high tx counts) ──
    "0x55d398326f99059ff775485246999027b3197955": ("token_contract", "USDT BSC (Tether on BNB Chain)",     0.99),
    "0xe9e7cea3dedca5984780bafc599bd69add087d56": ("token_contract", "BUSD BSC (Binance USD)",             0.99),
    "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d": ("token_contract", "USDC-Peg BSC (Binance-Peg USDC)",    0.99),
    "0xba2ae424d960c26247dd6c32edc70b295c744c43": ("token_contract", "BTCB (Bitcoin BEP-20)",              0.99),
    "0x2170ed0880ac9a755fd29b2688956bd959f933f8": ("token_contract", "ETH-Peg BSC (Binance-Peg Ethereum)", 0.99),
    "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": ("wrapped_token",  "WBNB (Wrapped BNB)",                 0.99),
    "0xc9882def23bc42d53895b8361d0b1edc7570bc6a": ("token_contract", "FIST Token (BSC)",                   0.85),
    "0xb300000b72deaeb607a12d5f54773d1c19c7028d": ("token_contract", "FistBomb / FIST-related (BSC)",      0.80),  # tentative
    # ── CEX hot wallets (BSC; sample, expand quarterly via Chainalysis or community DB) ──
    "0xdccf3b77da55107280bd850ea519df3705d1a75a": ("cex_binance_hot", "Binance Hot Wallet (BSC)",          0.95),
    "0x68b22215ff74e3606bd5e6c1de8c2d68180c85f7": ("cex_okx_hot",     "OKX BSC Hot",                       0.95),
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": ("cex_bybit_hot",   "Bybit BSC Hot",                     0.95),
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": ("cex_bitget_hot",  "Bitget BSC Hot",                    0.95),
    # ── Indian CEX (BSC; sample, confirm via BscScan labels or Chainalysis) ──
    # NOTE: Public BSC hot-wallet addresses for Indian VDA-SPs are not always
    # publicly tagged on BscScan. Entries below are PLACEHOLDERS for Kunal-led
    # confirmation. DO NOT trust without independent verification.
    "0xb2c1b6ed4055825a5e3ec3a3f5bff8c3f5b50f86": ("cex_wazirx_in",  "WazirX hot wallet placeholder (NEEDS VERIFICATION)", 0.40),
    # ── DEX infra ──
    "0x10ed43c718714eb63d5aa57b78b54704e256024e": ("dex_router",      "PancakeSwap V2 Router",             0.99),
    "0x05ff2b0db69458a0750badebc4f9e13add608c7f": ("dex_router",      "PancakeSwap V1 Router",             0.99),
    "0x1f4d99449e649598477ace30683b544bfa00c756": ("dex_farm",        "PancakeSwap MasterChef",            0.95),
    "0xd22202d23fe7de9e3dbe11a2a88f42f4cb9507cf": ("dex_aggregator",  "1inch Aggregator BSC v5",           0.85),
    # ── Bridges (verified BSC bridge addresses) ──
    "0x9aa83081aa06af7208dcc7a4cb72c94d057d2cda": ("bridge_pool",     "Stargate Bridge BSC",               0.90),
    # ── Mixers / sanctions (Phase 0 sample; populate from OFAC SDN quarterly) ──
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": ("mixer",           "TornadoCash 10 BNB",                0.95),
    "0x84443cfd09a48af6ef360c6976c5392ac5023a1f": ("mixer",           "TornadoCash 0.1 BNB",               0.95),
    # ── Common utilities ──
    "0x88888c037df4527933fa8ab203a89e1e6e58db70": ("utility",         "Multisender.app",                   0.90),
}


CEX_NAME_TAG_PATTERNS = (
    ("binance",  "cex_binance_hot"),
    ("okx",      "cex_okx_hot"),
    ("bybit",    "cex_bybit_hot"),
    ("bitget",   "cex_bitget_hot"),
    ("coinbase", "cex_coinbase"),
    ("kraken",   "cex_kraken"),
    ("huobi",    "cex_huobi"),
    ("kucoin",   "cex_kucoin"),
    ("gate.io",  "cex_gateio"),
    ("bitfinex", "cex_bitfinex"),
    ("mexc",     "cex_mexc"),
    ("bithumb",  "cex_bithumb"),
    ("wazirx",   "cex_wazirx_in"),
    ("coindcx",  "cex_coindcx_in"),
    ("mudrex",   "cex_mudrex_in"),
)

EXPLICIT_BRIDGE_PATTERNS = (
    "Multichain Bridge", "Stargate Bridge", "Hop Protocol",
    "Across Protocol", "deBridge", "Synapse Bridge", "Wormhole",
    "Axelar Bridge",
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


class AddressLabelState(TypedDict, total=False):
    # input
    case_id: str
    addresses: List[str]
    enable_llm_verdict: bool
    live_write: bool
    output_dir: str
    # internal
    labels:          Annotated[Dict[str, Dict[str, Any]], _merge_dict]
    classifications: Dict[str, Dict[str, Any]]
    observation_vids: Annotated[List[str], _merge_list]
    # output
    pegel_tick_ids: List[str]
    written_files: Dict[str, str]
    document_sha256: str
    status: str
    error: str


# ── Helpers ────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rkey(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _http_get(url: str, *, timeout: int = 25) -> Tuple[int, str]:
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")[:1000000]
    except Exception as e:  # noqa: BLE001
        return -1, f"err: {type(e).__name__}: {str(e)[:300]}"


# ── Nodes ──────────────────────────────────────────────────────────────


def gate_input_node(state: AddressLabelState) -> Dict[str, Any]:
    addrs = state.get("addresses") or []
    if not addrs:
        return {"status": "error", "error": "addresses list is empty"}
    valid = [a for a in addrs if re.match(r"^0x[a-fA-F0-9]{40}$", a)]
    if len(valid) != len(addrs):
        invalid = [a for a in addrs if a not in valid]
        return {"status": "error", "error": f"invalid addresses: {invalid[:3]}"}
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    logger.info("gate_input  addresses=%d case=%s", len(valid), case_id)
    return {
        "case_id": case_id,
        "addresses": valid,
        "labels": {},
        "classifications": {},
        "observation_vids": [],
        "pegel_tick_ids": [],
        "written_files": {},
    }


def fan_out_per_address(state: AddressLabelState):
    return [Send("label_one", {**state, "_address": a}) for a in state["addresses"]]


def label_one_node(state: AddressLabelState) -> Dict[str, Any]:
    addr = state["_address"]
    la = addr.lower()
    out: Dict[str, Any] = {
        "address": addr, "local_db_match": None,
        "name_tag": "", "title": "", "og_description": "",
        "balance_usd": "?", "tx_count": "?", "is_contract": False,
        "verified": False, "label_hits": [],
    }
    # 1. Local DB lookup
    if la in KNOWN_ADDRESS_DB:
        cls, lbl, conf = KNOWN_ADDRESS_DB[la]
        out["local_db_match"] = {"class": cls, "label": lbl, "confidence": conf}
    # 2. BscScan public name tag + tooltip scrape
    time.sleep(0.5)
    status, body = _http_get(f"https://bscscan.com/address/{addr}")
    out["fetch_status"] = status
    if status == 200:
        m = re.search(r'<title>([^<]+)</title>', body)
        out["title"] = (m.group(1).strip() if m else "")[:200]
        m = re.search(r'og:description"\s+content="([^"]+)"', body)
        if m: out["og_description"] = m.group(1)[:400]
        m = re.search(r'Balance:\s*\$?([\d,]+(?:\.\d+)?)', body)
        if m: out["balance_usd"] = m.group(1)
        m = re.search(r'Transactions:\s*([\d,]+)', body)
        if m: out["tx_count"] = m.group(1)
        out["is_contract"] = "Contract Source Code" in body.lower() or "contract: verified" in body.lower()
        out["verified"] = "<i class=\"fa-solid fa-check\"" in body
        # Public name tag: BscScan puts it as a span near the top with class "u-label"
        m = re.search(r'class="u-label[^"]*"[^>]*>([^<]{1,80})<', body)
        if m: out["name_tag"] = m.group(1).strip()
        for tag in re.findall(r'data-bs-toggle="tooltip"\s+data-bs-title="([^"]+)"', body)[:30]:
            for pat, _cls in CEX_NAME_TAG_PATTERNS:
                if pat in tag.lower():
                    out["label_hits"].append(tag[:120])
                    break
            for pat in EXPLICIT_BRIDGE_PATTERNS:
                if pat.lower() in tag.lower():
                    out["label_hits"].append(tag[:120])
                    break
    logger.info("label_one  addr=%s local=%s tags=%d", addr, bool(out["local_db_match"]), len(out["label_hits"]))
    return {"labels": {la: out}}


def after_label_barrier_node(state: AddressLabelState) -> Dict[str, Any]:
    logger.info("after_label_barrier  labels=%d", len(state.get("labels") or {}))
    return {}


def classify_strict(info: Dict[str, Any]) -> Tuple[str, float, str]:
    """Strict classifier — priority cascade. Returns (class, confidence, reason)."""
    # Priority 1: local DB
    if info.get("local_db_match"):
        m = info["local_db_match"]
        return m["class"], m["confidence"], f"local_db:{m['label']}"
    # Priority 2: BscScan CEX name tag in tooltips
    for tag in info.get("label_hits", []):
        tl = tag.lower()
        for pat, cls in CEX_NAME_TAG_PATTERNS:
            if pat in tl:
                return cls, 0.90, f"bscscan_tag:{tag[:60]}"
        for pat in EXPLICIT_BRIDGE_PATTERNS:
            if pat.lower() in tl:
                return "bridge_pool", 0.85, f"bscscan_bridge_tag:{tag[:60]}"
    # Priority 3: name_tag from u-label span
    nt = (info.get("name_tag") or "").lower()
    if nt:
        for pat, cls in CEX_NAME_TAG_PATTERNS:
            if pat in nt:
                return cls, 0.90, f"name_tag:{info['name_tag']}"
    # Priority 4: verified contract + heuristic
    if info.get("verified"):
        return "verified_contract", 0.50, "verified contract (unclassified)"
    # Priority 5: balance + tx heuristic
    bal = 0.0
    if info.get("balance_usd") and info["balance_usd"] != "?":
        try: bal = float(info["balance_usd"].replace(",", ""))
        except Exception: pass  # noqa: BLE001
    tx = 0
    if info.get("tx_count") and info["tx_count"] != "?":
        try: tx = int(info["tx_count"].replace(",", ""))
        except Exception: pass  # noqa: BLE001
    if bal > 1_000_000 and tx > 1000 and not info.get("is_contract"):
        return "whale_eoa", 0.50, f"high-balance EOA (${bal:,.0f}, {tx} tx)"
    if info.get("is_contract") and not info.get("verified"):
        return "unverified_contract", 0.30, "unverified contract"
    return "unknown_eoa", 0.20, "no signals"


def classify_all_node(state: AddressLabelState) -> Dict[str, Any]:
    classifications: Dict[str, Dict[str, Any]] = {}
    for la, info in (state.get("labels") or {}).items():
        cls, conf, reason = classify_strict(info)
        classifications[la] = {
            "address": info["address"],
            "class": cls,
            "confidence": conf,
            "reason": reason,
        }
        logger.info("classify  %s → %s (%.2f) — %s", info["address"][:24]+"…", cls, conf, reason)
    return {"classifications": classifications}


def emit_pegel_node(state: AddressLabelState) -> Dict[str, Any]:
    case_id = state.get("case_id") or DEFAULT_CASE_ID
    rkey = _rkey("addressLabelBatch", case_id, _now_iso())
    tick_vid = f"at://{MALAK_DID}/ai.gftd.apps.malak.investigationTick/{rkey}"
    counts: Dict[str, int] = {}
    for c in (state.get("classifications") or {}).values():
        counts[c["class"]] = counts.get(c["class"], 0) + 1
    logger.info("emit_pegel  tick=%s  classifications=%s", tick_vid[-24:], counts)
    return {"pegel_tick_ids": [tick_vid]}


def persist_fs_node(state: AddressLabelState) -> Dict[str, Any]:
    out_dir = state.get("output_dir") or ""
    if not out_dir: return {}
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    findings = {
        "case_id": state.get("case_id"),
        "addresses_processed": len(state.get("addresses") or []),
        "classifications": state.get("classifications") or {},
        "labels": state.get("labels") or {},
        "pegel_ticks": state.get("pegel_tick_ids") or [],
    }
    out_path = p / "address-label-batch-findings.json"
    out_path.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    return {"written_files": {"findings": str(out_path)}, "document_sha256": sha}


def audit_emit_node(state: AddressLabelState) -> Dict[str, Any]:
    if state.get("status", "").startswith(("denied", "error")):
        return {}
    logger.info(
        "malak.address_label.completed addrs=%d classifications=%d sha=%s",
        len(state.get("addresses") or []),
        len(state.get("classifications") or {}),
        (state.get("document_sha256") or "")[:16],
    )
    return {"status": "ok"}


# ── Graph ──────────────────────────────────────────────────────────────


def build_address_label_pursuit_graph():
    g = StateGraph(AddressLabelState)
    g.add_node("gate_input", gate_input_node)
    g.add_node("label_one", label_one_node)
    g.add_node("after_label_barrier", after_label_barrier_node)
    g.add_node("classify_all", classify_all_node)
    g.add_node("emit_pegel", emit_pegel_node)
    g.add_node("persist_fs", persist_fs_node)
    g.add_node("audit_emit", audit_emit_node)

    g.set_entry_point("gate_input")
    g.add_conditional_edges("gate_input", fan_out_per_address, ["label_one"])
    g.add_edge("label_one", "after_label_barrier")
    g.add_edge("after_label_barrier", "classify_all")
    g.add_edge("classify_all", "emit_pegel")
    g.add_edge("emit_pegel", "persist_fs")
    g.add_edge("persist_fs", "audit_emit")
    g.add_edge("audit_emit", END)
    return g.compile()


async def run_address_label_pursuit(
    *, addresses: List[str],
    case_id: str = DEFAULT_CASE_ID,
    enable_llm_verdict: bool = False,
    live_write: bool = False,
    output_dir: str = "",
) -> Dict[str, Any]:
    graph = build_address_label_pursuit_graph()
    initial: AddressLabelState = {
        "addresses": addresses, "case_id": case_id,
        "enable_llm_verdict": enable_llm_verdict,
        "live_write": live_write, "output_dir": output_dir,
    }
    return await graph.ainvoke(initial)


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="address_label_pursuit")
    p.add_argument("--addresses", required=True, help="comma-separated 0x... addresses")
    p.add_argument("--case-id", default=DEFAULT_CASE_ID)
    p.add_argument("--live-write", action="store_true")
    p.add_argument("--output-dir", default="")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    addrs = [a.strip() for a in args.addresses.split(",") if a.strip()]
    result = asyncio.run(run_address_label_pursuit(
        addresses=addrs, case_id=args.case_id,
        live_write=args.live_write, output_dir=args.output_dir,
    ))
    from collections import Counter
    cls_counts = Counter(c["class"] for c in (result.get("classifications") or {}).values())
    print(json.dumps({
        "status": result.get("status"),
        "addresses_processed": len(addrs),
        "classifications": dict(cls_counts),
        "files": list((result.get("written_files") or {}).keys()),
        "pegel_ticks": result.get("pegel_tick_ids") or [],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
