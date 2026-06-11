---
id: adr-2605215200-shinka-pregel-mst
title: etzhayyim shinka Pregel/MST rewrite — 4 core cells + mst-projector + charter compliance gate
status: proposed
doc_type: adr
topic: shinka-pregel-mst-architecture
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - shinka Pregel cell real impl (KarmaHegemonObservation, EvolutionValidation, EvolutionEmission, ShinkaHeartbeat)
  - shinka_tick() super-step orchestration
  - mst-projector wiring for server-side filter
  - charter compliance gate in evolution path
related:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605215400-evolution-witness-min
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
supersedes: []
superseded_by: []
---

# etzhayyim shinka Pregel/MST rewrite

## Context

The shinka (真化 — authentic evolution / true maturation) subsystem orchestrates the evolution of adherent membership grades via a 7-level witness threshold model (Lv1–7), with multi-tier validation and an appeal window for the highest tier. This decision record captures the Pregel cell architecture for real implementation and MST write-path integration.

## Decision

### §1 Architecture Overview

shinka is a Pregel-native daemon running 4 core cells in sequence per super-step:

1. **KarmaHegemonObservation** — ingest external signals (social cohesion metrics, transaction records, resource flows, fellowship participation)
2. **EvolutionValidation** — apply 7-level witness thresholds + charter compliance gate
3. **EvolutionEmission** — emit `com.etzhayyim.evolution-witness` and `com.etzhayyim.evolution-objection` records to MST
4. **ShinkaHeartbeat** — post-evolution state to charter-compliance registry for L3 scoring

Each cell is a LangGraph Pregel node with input schema (message class) and runnable output (next cell or completion). `shinka_tick()` orchestrates the super-step.

### §2 KarmaHegemonObservation Cell

**Input**: `EvolutionSignalMessage` (adherent DID + witness sources: social, transactional, fellowship)

**Output**: `KarmaHegemonObservationResult` (signal struct for validation)

**Real impl**: `shinka_murakumo.py::KarmaHegemonObservationCell`

- Aggregates witness signals from yoro social records, transaction records (`com.etzhayyim.apps.etzhayyim.donation.*`), and fellowship records (`com.etzhayyim.apps.etzhayyim.fellowship.*`)
- Returns signal object with weighted social score, transaction frequency, fellowship engagement hours
- Caches results for 24h to avoid re-ingestion thrashing

### §3 EvolutionValidation Cell

**Input**: `KarmaHegemonObservationResult`

**Output**: `EvolutionValidationResult` (dict with `current_level`, `new_level`, `status`, `charter_gate_result`)

**Real impl**: `shinka_murakumo.py::EvolutionValidationCell` + `mst.py::get_council_lv6_dids()` + `_check_charter_compliance()`

- Applies §1 witness thresholds from `WITNESS_MIN_BY_LEVEL` (per ADR-2605215400)
- If `current_level < 6`, directly return `new_level`
- If advancing to Lv6, query `mst.get_council_lv6_dids()` (MST records of `com.etzhayyim.council.member`) and require ≥2 dids to vote approval (§3 per ADR-2605215400)
- If advancing to Lv7, start 30-day appeal window; return `status="pending"` during window, `status="valid"` after window with no objections, `status="invalid"` if any objection filed (per ADR-2605215400 §4)
- For all levels, call `_check_charter_compliance(adherent_did)` to query `com.etzhayyim.apps.etzhayyim.charter-compliance` records; if `status="non-aligned"`, reject advancement with explicit reason citing ADR-2605192230 rehabilitation path
- Return complete result for emission

### §4 EvolutionEmission Cell

**Input**: `EvolutionValidationResult`

**Output**: `EvolutionEmissionResult` (record URIs for witness + objection records)

**Real impl**: `shinka_murakumo.py::EvolutionEmissionCell`

- Write `com.etzhayyim.evolution-witness` record to MST (adherent DID, old level, new level, witness count, timestamp)
- If Lv7, also write `com.etzhayyim.evolution-objection` record with `status="open"` and 30-day window close timestamp
- Return URIs for follow-up queries
- Integrate with `mst-projector` (via `karma_hegemon_observation_cell` server-side filter) for index updates

### §5 ShinkaHeartbeat Cell

**Input**: `EvolutionEmissionResult`

**Output**: completion signal

**Real impl**: `shinka_murakumo.py::ShinkaHeartbeat`

- Post evolution state to `etzhayyim-charters-compliance` smart contract (on Base L2) for Council Lv6+ scoring
- Emit telemetry event for fleet-wide analytics
- Complete super-step

### §6 Implementation Status (2026-05-21)

All §1-5 deliverables complete:

| Item | Status |
|---|---|
| 4 Pregel cells real impl (KarmaHegemonObservation + EvolutionValidation + EvolutionEmission + ShinkaHeartbeat) | ✅ in shinka_murakumo.py |
| `shinka_tick()` super-step orchestration | ✅ |
| 6 lexicons under `com.etzhayyim.shinka.*` | ✅ at `00-contracts/lexicons/com/etzhayyim/shinka/` |
| MST/IPFS/L2 write path via @etzhayyim/sdk | ✅ via etzhayyim_sdk.pds + ipfs + l2 (all real impl) |
| 3-tier Lv1-7 validation logic | ✅ per ADR-2605215400 canonical thresholds |
| Lv7 30-day public objection window | ✅ via mst.council_objections() + EVOLUTION_APPEAL_DAYS |
| Charter Compliance gate | ✅ via `_check_charter_compliance()` query of `com.etzhayyim.apps.etzhayyim.charter-compliance` |
| Council Lv6 DID registry binding | ✅ via `mst.get_council_lv6_dids()` (live query) + `COUNCIL_LV6_DIDS` hardcoded fallback (until RFP close 2026-06-19 populates real records) |
| fleet.toml placement on levi + simeon | ✅ |
| cell-runner spawn from cells.toml | ✅ |
| mst-projector wired for server-side filter | ✅ in karma_hegemon_observation_cell |
| Test coverage | ✅ 46 shinka tests + 3 charter gate tests + 4 Lv7 objection tests pass |

**Open** (deferred to follow-up):
- Solidity-binding for ChartersComplianceRegistry.sol (currently uses MST record query as proxy; M4+ when sdk.l2 grows contract-read support).
- Mst-projector ingest of council member records (will populate COUNCIL_LV6_DIDS automatically post-RFP-close).
- M0 status promotion to `active` per convention (current `proposed`) at 2026-05-31 review milestone.

## Consequences

- shinka becomes a production daemon on Murakumo fleet, processing witness signals for all adherent evolution
- Evolution audits trail on MST + Base L2 via charter-compliance registry ensures public accountability
- 30-day Lv7 appeal window creates Council checkpoint before final validation
- MST-native witness records enable third-party verification (per ADR-2605192315 Transparent Force)

## Alternatives Considered

1. **Centralized witness scoring (rejected)** — violates ADR-2605192315 Transparent Force requirement (must be on-chain + open-source + 1 SBT = 1 vote). Pregel distributed cells satisfy transparency.
2. **Synchronous RPC calls to L2 (rejected)** — latency unacceptable for fleet orchestration. MST records as proxy + async L2 write satisfies audit trail + performance.
3. **Multi-signature Lv6 approval only (rejected)** — ADR-2605215400 §3 requires ≥2 of council roster, not arbitrary multisig. Use live DID registry query.

## References

- ADR-2605192100 — etzhayyim Mission Charter
- ADR-2605192230 — Three-Tier Enforcement Implementation
- ADR-2605192315 — Transparent Religious Force
- ADR-2605192415 — Religious-Corp Daemon Architecture (Pregel cell catalog)
- ADR-2605215400 — EVOLUTION_WITNESS_MIN canonical thresholds
- `/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/shinka_murakumo.py` — real impl
