---
id: adr-2605171200-chain-freeze-request-pregel-and-recursive-trace
title: "chain_freeze_request Pregel + recursive wallet-trace depth-budget methodology"
status: active
doc_type: adr
topic: malak-pursuit-pregel-family-freeze
authoritative: true
last_verified: 2026-05-17
authoritative_for:
  - chain_freeze_request_pursuit Pregel design (6 packet kinds, Phase 1 schedule_review)
  - recursive wallet_deep_inspect_pursuit depth-budget exhaustion criterion
  - multi-CEX LECR scope expansion (Binance + Bitget + future)
  - bsc_operator_walk vs address_label_pursuit role separation
priority: 8.2
axis: malak-orchestration
weight: 0.82
priority_note: "Closes the recovery loop. bitnest_exit_pursuit + pursuit_loop + wallet_deep_inspect + address_label produce evidence; chain_freeze_request renders the human-facing legal packets."
depends_on:
  - adr-2605151500-bitnest-exit-pursuit-pregel-link-back-pattern
  - adr-2605152000-wallet-deep-inspect-and-address-label-pregels
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
  - adr-2605080600-langgraph-server-granian-l3-runtime
related:
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-15 → 2026-05-17 produced the chain_freeze_request Pregel
  (6 packets per case) plus a recursive depth-2 → depth-6 trace on a
  high-balance counterparty ($21.8M whale 0x06f3fffe...). The recursive
  trace exhausted with no operator-exit pattern, validating a generalizable
  "depth-budget" exhaustion criterion that other case investigations can
  reuse. The Bitget BSC Hot wallet was discovered as a 2nd-tier CEX target
  during depth-3 trace, expanding the LECR Tier-1 scope from Binance-only
  to Binance + Bitget.
---

# Context

ADR-2605151500 established the case-anchored pursuit Pregel pattern.
ADR-2605152000 added wallet_deep_inspect_pursuit (whale classifier) and
address_label_pursuit (multi-source label batch). What was still missing:

1. **A Pregel that generates human-facing legal packets** from the
   accumulated graph evidence (BSC trace results, victim case data, yabai
   anchors). Manual rendering of LECR-EN-v1/v2, JC3 referral, INTERPOL IPSG
   referral, etc. is repetitive and case-non-portable.
2. **A methodology for terminating recursive wallet inspection**. When
   discovering a high-balance counterparty (e.g. $21.8M), the investigator
   needs a deterministic rule for "when to stop deep-inspecting and
   conclude it's not an operator-exit". Without such a rule, recursive
   trace can balloon to thousands of fetches with no actionable result.
3. **Multi-CEX LECR scope expansion**. The initial LECR-EN-v2 only
   targeted Binance. As recursive trace surfaced additional CEX-active
   wallets (Bitget BSC Hot), the LECR format must accommodate per-CEX
   variants.

# Decision

## 1. New Pregel: `chain_freeze_request_pursuit`

Module: `20-actors/magatama/py/src/pymagatama/malak/langgraph/chain_freeze_request_pursuit.py`
NSID: `com.etzhayyim.apps.malak.chainFreezeRequest`
LangServer route: `POST /invoke/chainFreezeRequest`

### Topology (6 super-steps; ADR-2605152000 family)

```
gate_input (case_id + packet_kinds[])
  ↓ (1) sequential
load_case_evidence (Phase 0 reads embedded CASE_EVIDENCE; Phase 1 reads live RW)
  ↓
fan_out_per_packet ──────────────────────────────────────────────────┐
  │ (2) BSP parallel — Send × N packet kinds                        │
  ├─► render_packet_one  (kind-specific template)                   │
                                                                    ▼
  │ (3) implicit barrier
  ▼
collect_and_sign (sequential — sha256 manifest + chain-of-custody)
  ↓
persist_fs (write 1 md per packet + MANIFEST.md)
  ↓
emit_pegel
  ↓
schedule_review (Phase 1 live_write: write vertex_malak_pursuit_target rows
                  with kind='packet_review', priority=14, status='queued'
                  for human reviewer queue pickup)
  ↓
audit_emit → END
```

### Packet kinds (6 in ALL_PACKET_KINDS tuple; per-kind renderer functions in PACKET_RENDERERS dict)

| Kind | Audience | Routing | Language |
|---|---|---|---|
| `binance_lecr` | Binance Compliance Investigations Unit | NPA International Cooperation Division → INTERPOL Tokyo NCB → Binance | EN |
| `jc3_referral` | Japan Cybercrime Control Center | direct | JP |
| `npa_intl_cover` | 警察庁 国際協力推進室 | 都道府県警 → 警察庁本部 | JP |
| `interpol_ipsg` | INTERPOL IPSG Lyon | INTERPOL Tokyo NCB → IPSG | EN |
| `fiu_ind_pmla` | FIU-IND (India) | Kunal Bakshi (BCI) → FIU-IND | EN |
| `kanagawa_escalation` | 神奈川県警 磯子警察署 松村刑事 | direct | JP |

Adding a new packet kind = add (kind, renderer_function) entry to PACKET_RENDERERS and update ALL_PACKET_KINDS tuple. Each renderer takes `(case_id, evidence)` and returns markdown.

### Phase 0 / Phase 1 contract

| State | Behavior |
|---|---|
| `live_write=False` (default) | Filesystem packet artifacts only. Phase 0 dry-run. |
| `live_write=True` + `KOTOBA_URL` set | `schedule_review` node writes 1 vertex_malak_pursuit_target row per packet (kind='packet_review', priority=14, status='queued') so a human reviewer queue picks them up |
| `live_write=True` + `KOTOBA_URL` unset | Logs warning; filesystem-only fallback |

Pattern matches ADR-2605151500 + ADR-2605152000 Phase contract.

## 2. Recursive wallet-trace depth-budget exhaustion criterion

When `wallet_deep_inspect_pursuit` classifies a target as `whale_eoa`,
`unverified_contract`, or `dex_router`, the investigator may want to
recursively inspect the target's top counterparties (depth-2 trace).
The depth budget must be bounded.

### Exhaustion criterion (recommended; reusable for any case)

Stop recursive inspection when **all three** are true:

1. **Depth ≥ 3** super-step from the originating case anchor. (`0x06f3fffe...`
   $21.8M whale = depth 2 from operator wallet; its 8 unverified contracts
   investigated at depth 3.)
2. **All top counterparties classify as one of**: token_contract,
   wrapped_token, dex_router, dex_aggregator, dex_farm, mev_bot
   (high-tx + low-balance pattern), or unknown_eoa with no CEX/sanction signals.
3. **No CEX (Binance/Bitget/etc.) hot wallet appears** in any of the
   target's top 15 counterparties.

If any condition fails (e.g. a CEX hot wallet appears in the counterparty
graph), continue one more depth level. Practical experience shows that
depth-6 is the maximum useful budget; beyond that, false-positive rates
on the strict classifier dominate signal.

### Verdict outputs

| Verdict | Meaning | Recovery action |
|---|---|---|
| `operator_exit_likely` | CEX hot wallet appears in top-3 counterparties at depth ≤ 2; tx flow matches concentrated-withdrawal pattern | LECR Tier 1 target |
| `circumstantial_association` | Counterparty graph touches operator wallet but no concentrated outflow; ambiguous | hold for follow-up |
| `dex_trading_unrelated` | Standard DEX trader / MEV bot pattern; no operator linkage | downgrade freeze priority |
| `exhausted_no_signal` | Depth budget hit + criterion 1-3 all satisfied | document and stop |

The Takahashi case `0x06f3fffe...` $21.8M whale received verdict
`dex_trading_unrelated` after depth-6 trace, validating the criterion.

## 3. Multi-CEX LECR scope expansion

The `binance_lecr` packet renderer in chain_freeze_request_pursuit is a
template; the same pattern applies to other CEXs. As recursive trace
discovers additional CEX-active wallets in the operator's depth-N
counterparty graph, the freeze request scope expands:

| CEX | Discovery method | Evidence ref |
|---|---|---|
| Binance | depth-1 from operator wallet (3 hits found) | LECR-EN-v2 §IV.1-3 |
| Bitget | depth-3 from `0x06f3fffe...` whale (1 hit `0x9d173e6c`, 28 tx with Bitget Hot) | (extension) |
| OKX / Bybit / etc. | future depth-N trace | (per-discovery) |

Renderer design pattern: parameterize the existing `_render_binance_lecr`
function as `_render_cex_lecr(cex_name, cex_hot_wallets, counterparties)`
in a future refactor. For Phase 0, dedicated renderers per CEX (cloned
from binance_lecr) work adequately.

## 4. bsc_operator_walk vs address_label_pursuit role separation

| Module | Purpose | Strictness |
|---|---|---|
| `bsc_operator_walk.py` (standalone script) | First-pass discovery of operator wallet's direct counterparties from BscScan /txs + /tokentxns scrape; quick label via pattern match | loose (catches more, may have false positives) |
| `address_label_pursuit` Pregel | Strict re-classification of a known address set with multi-source aggregation (KNOWN_ADDRESS_DB + BscScan + pattern); guards against bridge-keyword false positives | strict (per ADR-2605152000) |

Use both in sequence: walk → unknown set → strict re-label. Different label
results between the two = candidate for KNOWN_ADDRESS_DB expansion.

# Consequences

## Positive

- All major legal-packet renderings (Binance + JC3 + NPA + INTERPOL + FIU-IND + Kanagawa local) now in one Pregel with deterministic sha256 chain-of-custody
- Recursive trace has an explicit termination rule, preventing investigator from drowning in tx pagination forever
- Multi-CEX LECR pattern documented for future CEX additions (Bitget already identified as Tier-1+ target)
- bsc_operator_walk + address_label_pursuit role separation prevents accidentally substituting one for the other

## Negative

- chain_freeze_request CASE_EVIDENCE table is currently embedded in module code (not loaded from RW). Phase 1 should swap for live RW query so packets always reflect latest evidence.
- Multi-CEX packet rendering currently requires copy-paste per CEX. The promised `_render_cex_lecr(cex_name, ...)` refactor is deferred.
- Recursive depth-budget criterion is heuristic; doesn't replace human-expert judgment when classifier confidence is low (0.50).

## Migration

- `00-contracts/lexicons/com/etzhayyim/apps/malak/chainFreezeRequest.json` lexicon SSoT: pending (Phase 1 chore).
- `bsc_unknown_deep_label.py` standalone is now legacy; new investigations use `address_label_pursuit` Pregel.
- KNOWN_ADDRESS_DB quarterly refresh process: pending automation (Phase 2 chore).

# Alternatives Considered

## Alt-1: Render all 6 packets in a single mega-function instead of fan-out

Rejected. Each renderer has different language (JP/EN), routing audience,
and information-density requirements. Fan-out keeps each renderer focused
and testable independently. The Pregel parallel fan-out cost is negligible
because rendering is in-process Python string formatting.

## Alt-2: Use BPMN flow per packet (per ADR-0056 legacy pattern)

Rejected. ADR-2605131600 already pivoted malak orchestration to LangGraph.
BPMN would require pyzeebe handler + Zeebe broker deploy per packet kind.
The in-process LangGraph fan-out is simpler and matches the existing pursuit
Pregel family pattern.

## Alt-3: Skip the recursive depth-budget rule and inspect everything

Rejected. The recursive trace on `0x06f3fffe...` $21.8M whale visited
≈ 134 + 8×~150 + 3×~200 = ≈ 1,930 unique counterparty addresses across 6
super-steps. Without the depth-budget rule, the investigation would
continue indefinitely without producing a freeze target. The exhaustion
criterion provides closure.

# References

- `20-actors/magatama/py/src/pymagatama/malak/langgraph/chain_freeze_request_pursuit.py`
- `_working/malak/freeze-request-takahashi-20260515/` (Phase 0 packet outputs)
- `_working/malak/freeze-request-takahashi-20260515-phase1live/` (Phase 1 live_write run)
- `_working/malak/whale-recursive-20260516/` (8 unverified-contract recursive inspect)
- `_working/malak/whale-recursive-20260517/` (3 second-tier whale + MEV bot inspect)
- THREAT-LEDGER #15795 (chain_freeze_request first run), #15798 (Phase 1 schedule_review), #15800-#15806 (recursive trace conclusion + Bitget discovery)
- ADR-2605151500 (bitnest_exit_pursuit pattern)
- ADR-2605152000 (wallet_deep_inspect + address_label Pregels)
