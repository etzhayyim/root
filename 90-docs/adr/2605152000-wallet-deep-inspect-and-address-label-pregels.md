---
id: adr-2605152000-wallet-deep-inspect-and-address-label-pregels
title: "Two new malak Pregels: wallet_deep_inspect_pursuit + address_label_pursuit"
status: active
doc_type: adr
topic: malak-pursuit-pregel-family
authoritative: true
last_verified: 2026-05-15
authoritative_for:
  - new malak pursuit Pregel `wallet_deep_inspect_pursuit` (whale + protocol classifier)
  - new malak pursuit Pregel `address_label_pursuit` (multi-source address labelling)
  - refactor of bsc_unknown_deep_label.py into a graph-native Pregel module
  - case-anchor reuse pattern across the malak.bitnest-exit-pursuit family
priority: 8.3
axis: malak-orchestration
weight: 0.83
depends_on:
  - adr-2605151500-bitnest-exit-pursuit-pregel-link-back-pattern
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
  - adr-2605082000-langgraph-graph-definition-as-data
related: []
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-15: deep-label of operator-wallet counterparties found a
  third Binance hit + a $21.8M-balance unlabeled wallet. Standalone scripts
  (bsc_unknown_deep_label.py, bsc_operator_tx_detail.py) demonstrated the
  workflow but lack: (1) parallel super-step fan-out for pagination, (2)
  graph-native observation IDs, (3) case-anchor reuse across cases. This
  ADR formalises both as Pregels.
---

# Context

The `bitnest_exit_pursuit` Pregel (ADR-2605151500) anchored a case (case_id =
`case:takahashi-hiroyuki-20260512`) and discovered 7 entity / 42 case-edge
rows. Two follow-on investigations emerged that should be reusable patterns
for any case:

1. **Whale / high-balance wallet deep-inspect**: a target address has $21M
   balance and 10k+ transactions — is it (a) a Binance cold wallet, (b) a
   major DEX/router contract, (c) a bridge with concentrated TVL, or (d) an
   unrelated whale? Answering requires fetching paginated tx history,
   labelling top counterparties, and classifying.

2. **Address label batch refinement**: the existing `bsc_unknown_deep_label.py`
   used a single-pass BscScan tooltip scrape with a heuristic classifier.
   This produced known false positives (15 of 17 unknown addresses
   classified as "bridge" because BscScan tooltips mention "Bridge" in
   generic page contexts). A multi-source label aggregator (BscScan + local
   KNOWN_ADDRESS_DB + on-chain ABI signature + tx-pattern heuristics +
   optional LLM-classifier) is needed.

# Decision

Adopt two new Pregels following the ADR-2605151500 template (7 super-steps,
3 fan-outs, Annotated reducers, case-anchored link-back, Phase 0 dry-run).

## Pregel 1: `wallet_deep_inspect_pursuit`

### Purpose
Given a target address (typically a high-balance or high-tx counterparty
discovered by an upstream Pregel), determine: classification, beneficial
ownership signals, top counterparties, and risk score.

### Topology (7 super-steps)

```
gate_input (case_id + target_address)
  ↓ (1) sequential
fetch_address_meta (BscScan /address/<addr> single fetch)
  ↓
fan_out_fetch_pages ────────────────────────────────────────────┐
  │ (2) BSP parallel — Send × N pages of /txs?a=<addr>          │
  ├─► fetch_page_one                                            │
                                                                ▼
  │ (3) implicit barrier
  ▼
collect_and_dedupe (sequential; aggregate paginated tx rows)
  ↓
fan_out_label_top_K ────────────────────────────────────────────┐
  │ (4) BSP parallel — Send × top K (default 20) counterparties │
  ├─► label_counterparty_one                                    │
                                                                ▼
  │ (5) implicit barrier
  ▼
classify (sequential rule + optional LLM verdict)
  ↓
link_back_to_case (case-anchor edges)
  ↓
emit_pegel + persist_fs + audit_emit → END
```

### State channels

| Channel | Reducer | Purpose |
|---|---|---|
| `pages: Dict[int, dict]` | `_merge_dict` | One page per parallel fetcher (page_num → rows) |
| `counterparties: Dict[str, dict]` | `_merge_dict` | Per-counterparty aggregated stats |
| `labels: Dict[str, dict]` | `_merge_dict` | Per-counterparty label fetch result |
| `observation_vids: List[str]` | `_merge_list` | Accumulated observation IDs |

### Output classifications

| Class | Definition | Confidence rule |
|---|---|---|
| `cex_cold` | Binance/OKX/etc. cold wallet — high balance, low tx fraction (<5%), explicit BscScan label | 0.95 |
| `cex_hot` | CEX hot wallet — high tx (>1000/yr), label match, balance regularly cycling | 0.90 |
| `dex_router` | PancakeSwap/Uniswap router/farm/MasterChef — verified contract, high tx | 0.95 |
| `bridge_pool` | Bridge contract — strict signature: tx pattern + cross-chain ABI + known bridge address DB | 0.85 |
| `protocol_pool` | DeFi pool (lending, staking) — verified contract, high TVL | 0.80 |
| `whale_eoa` | Externally-owned wallet with $1M+ balance and no public label | 0.60 |
| `mixer` | Tornado Cash / similar — explicit DB match or sanctioned-list | 0.95 |
| `unknown_eoa` | Externally-owned wallet, low confidence | 0.30 |

### Defense-in-depth gates
- `gate_input`: case_id present, target_address checksum-valid, target_address ≠ operator (no self-loops)
- `route_classify`: skip LLM if `llm_disabled` or `serial_llm` env override
- `link_back`: requires `live_write=True` AND case-anchor list non-empty

### Phase 0 vs 1
Same contract as ADR-2605151500. Default Phase 0 dry-run. Phase 1 live_write
emits pursuit_target + edge_malak_target_extends + yabai_entity (for
high-confidence CEX/mixer classifications only).

---

## Pregel 2: `address_label_pursuit`

### Purpose
Given a list of N addresses (typically the unlabeled counterparties produced
by an upstream Pregel), aggregate labels from K sources, run a strict
classifier, and produce per-address verdicts. Replaces the
`bsc_unknown_deep_label.py` standalone script.

### Topology (5 super-steps; simpler than #1)

```
gate_input (case_id + address_list[])
  ↓ (1) sequential
fan_out_per_address ────────────────────────────────────────────┐
  │ (2) BSP parallel — Send × N addresses                       │
  ├─► label_one (multi-source: BscScan + DB + ABI + sanctions)  │
                                                                ▼
  │ (3) implicit barrier
  ▼
classify_all (sequential; consensus from multi-source)
  ↓
emit_pegel + persist_fs + audit_emit → END
```

### State channels

| Channel | Reducer | Purpose |
|---|---|---|
| `labels: Dict[str, dict]` | `_merge_dict` | Per-address multi-source label result |
| `classifications: Dict[str, str]` | `_merge_dict` | Per-address final classification verdict |
| `observation_vids: List[str]` | `_merge_list` | |

### Multi-source label aggregation strategy

Each `label_one` worker queries (in order):

1. **Local `KNOWN_ADDRESS_DB`** (curated CEX/bridge/mixer addresses) — instant, highest confidence
2. **BscScan public name tag** — via og:description + data-bs-title tooltip scraping (current method)
3. **On-chain ABI signature** — bytecode of address (if contract); pattern-match against known router/farm/bridge interfaces
4. **OFAC SDN crypto list** — local cached copy of sanctioned addresses
5. **TornadoCash address list** — local cached copy
6. **Chainalysis OSS or paid label** — feature-flagged behind env var; skipped if unavailable
7. **LLM verdict** (last-resort) — feature-flagged; uses raw BscScan page body

Aggregation: priority highest → lowest; each higher-confidence source overrides lower. Final classification = aggregated label + confidence score.

### Stricter classification heuristic (fixes the v1 false-positive)

Replace the v1 `classify()` function with:

```python
def classify_strict(info: dict) -> tuple[str, float]:
    # Priority 1: local DB exact match
    if info["local_db_match"]:
        return parse_local_db_class(info["local_db_match"]), 0.95
    # Priority 2: BscScan explicit name tag (e.g., "Binance:", "OKX:")
    cex_match = match_cex_pattern(info["public_name_tag"])
    if cex_match:
        return f"cex_{cex_match}", 0.90
    # Priority 3: contract verified + ABI signature
    if info["verified"]:
        abi_class = abi_classify(info["address"])
        if abi_class:
            return abi_class, 0.85
    # Priority 4: sanctions / mixer
    if info["address"].lower() in OFAC_LIST or info["address"].lower() in TORNADO_LIST:
        return "sanctioned", 0.95
    # Priority 5: balance + tx pattern heuristic (strict)
    bal = parse_balance(info["balance_usd"])
    tx = parse_count(info["tx_count"])
    if bal > 1_000_000 and tx > 1_000 and not info["is_contract"]:
        return "whale_eoa", 0.50  # low confidence — needs human review
    if info["is_contract"] and not info["verified"]:
        return "unverified_contract", 0.30
    return "unlabeled_eoa", 0.20
```

Key change: **never classify as "bridge" without explicit bridge address DB hit or ABI signature match.** The v1 implementation matched the keyword "Bridge" anywhere in BscScan tooltips, producing 15/17 false-positive bridge classifications.

# Consequences

## Positive

- Two reusable Pregels for any future malak case (not Takahashi-specific)
- Strict bridge classification eliminates the v1 false-positive rate
- Multi-source label aggregation gives a confidence score (not just a single classification), enabling downstream filtering
- Whale-eoa detection surfaces high-value unlabeled wallets (e.g., `0x06f3fffe...` $21.8M) for follow-up
- Both modules expose via LangServer `/invoke/{name}` endpoint per ADR-2605131600

## Negative

- `wallet_deep_inspect_pursuit` runtime: each /txs page is ~5s rate-limited, 10-page operator wallet = 50s + 20 counterparty label fetches = 10s = total ~60-90s
- `address_label_pursuit` runtime: O(N × source_count); 20 addresses × 5 sources = ~100 fetches at 0.5s/each = 50s
- LLM verdict path adds 60-240s cold-start latency (Ollama gemma4:e4b); use sparingly
- OFAC SDN list staleness: must be refreshed quarterly or via FATF / OFAC bulk update API

## Migration

- `_working/malak/bitnest-exit-20260515-phase1-live/bsc_unknown_deep_label.py` retained as historical artifact. Deep-label workflow migrates to `address_label_pursuit` Pregel.
- `bsc_operator_tx_detail.py` retained as historical artifact. Tx-detail workflow migrates to `wallet_deep_inspect_pursuit` Pregel.
- New module paths:
  - `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/malak/langgraph/wallet_deep_inspect_pursuit.py`
  - `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/malak/langgraph/address_label_pursuit.py`
- New XRPC lexicons:
  - `00-contracts/lexicons/com/etzhayyim/apps/malak/walletDeepInspect.json`
  - `00-contracts/lexicons/com/etzhayyim/apps/malak/addressLabelBatch.json`
- LangServer `CHAINS` extended in `server.py`.

# Alternatives Considered

## Alt-1: Single mega-Pregel covering both

Rejected. Wallet deep-inspect requires pagination + tx-pattern analysis;
address label batch requires multi-source aggregation per address. Mixing
them in one graph muddies the state channels and adds super-step count
(8-10 vs 7+5). Two focused modules with clear contracts win on Shannon η.

## Alt-2: Direct extension of bitnest_exit_pursuit Pregel

Rejected. bitnest_exit_pursuit is case-anchored to a specific narrative
(BitNest exit-fraud) with a specific seed-source list. A wallet deep-inspect
is case-agnostic — should be reusable for ANY case where a high-value
counterparty is found. Decoupling at the Pregel level preserves reusability.

## Alt-3: Use Chainalysis Reactor / Allium / Elliptic Lens API directly

Rejected for Phase 0. These paid tools provide superior classification but:
- $50-200k/yr subscription
- Each API call billed
- Not budget-approved for initial Phase 0
Phase 1 follow-up: add a feature-flagged Chainalysis source to `label_one`
multi-source aggregator. The Pregel architecture supports this without
topology change.

# References

- ADR-2605151500 (bitnest_exit_pursuit pattern)
- ADR-2605131600 (LangGraph + Pregel + LangServe orchestration)
- `bsc_unknown_deep_label.py` (Pregel 2 v0 predecessor)
- `bsc_operator_tx_detail.py` (Pregel 1 v0 predecessor)
- THREAT-LEDGER #15784-#15792
