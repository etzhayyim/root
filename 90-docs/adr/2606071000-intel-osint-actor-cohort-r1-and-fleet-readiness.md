# 2606071000 — intel/OSINT actor cohort: R1 forecast pipeline + cross-actor synthesis + Murakumo fleet-readiness

- **Status**: accepted
- **Date**: 2026-06-07 (JST)
- **Deciders**: founder seat (intel-loop wave)
- **Supersedes / amends**: none — ZERO invariant amendments
- **Related**: 2606051800 (mitooshi), 2606041827 (watari), 2606012600 (watatsuna), 2606022000 (kabuto), 2606032000 (kanjo), 2605301400 (tadori), 2605301600 (danjo), 2605302130 (himotoki), 2605262130 (kotoba canonical state), 2605312345 (Datom-first), 2605231525 (no-server-key), 2605215000 (Murakumo-only), 2605192415 (Murakumo fleet placement)

## Context

The intel/OSINT actor cohort (mitooshi, watari, watatsuna, kabuto, kanjo, tadori, danjo,
himotoki) existed in a mix of states: some had implemented analyzers but **zero tests**
(watari/watatsuna/kabuto = 0; tadori/kanjo = thin), and two were **pure design** with no
executable methods at all (danjo, himotoki). mitooshi shipped a forecasting *core*
(score.py + cells) but had no path from a persisted observation trail to a scored,
gate-decided forecast.

The recurring operational ask was *"raise coverage + maturity, build, deploy to the
Murakumo Mac-mini fleet, persist intel"*. Live deploy/ingest/publish/promotion for every
one of these actors is, by constitutional design, **outward-gated** (per-actor G7/G10/G14 =
Council Lv6+ + operator). So "deploy to the fleet" cannot be executed by an agent; the
reachable goal is **deploy-readiness** — every actor built, tested, and with its canonical
Datom artifacts materialised, such that the only remaining step is a human gate flip.

## Decision

Bring the whole cohort to **8/8 deploy-ready** (suite green + ≥1 persisted Datom artifact),
additively and with ZERO invariant amendments.

1. **mitooshi — full R1 forecasting pipeline** over the kotoba Datom log, every stage
   leak-free and emitting a persisted artifact:
   `observe (watari/watatsuna) → bridge → persist (append-only as-of trail) → forecast
   (leak-free Gaussian distributions, G1 distribution-only) → rolling-origin backtest +
   method scorecard (G12 skill vs baseline) → online recalibration (cells/online_update,
   leak-free) → calibration_gate promotion decision (G7/G9/G12) → cross-actor chokepoint
   resilience composite`. Both ends proven empirically: the real two-regime trail is
   honestly **REFUSED** on G7 (miscalibrated), while a single-regime fixture **CLEARS**
   when calibrated + member-signed. Live promotion stays G10-gated.

2. **watari / watatsuna / kabuto / kanjo / tadori — test + runner integration.** Added the
   missing standalone test suites + `run_tests.sh` for the already-implemented analyzers,
   pinning each actor's structural charter invariants in code (G2 resilience-not-targeting,
   G4 non-adjudication / no-person-tracking, G5 sourcing-honesty, G6/G7 PII + outward
   gates, the watatsuna plan's no-interdiction-representable property).

3. **danjo / himotoki — R0→R1** (first executable methods):
   - danjo: a `single-bidder-streak` discrepancy-observation analyzer over a public
     procurement corpus — FACTUAL cross-reference only, never a verdict (G4
     nonAdjudicatingNotice + no verdict field representable; G5 ≥2 sourceRecordCids; G6
     methodNoteCid; knownFalsePositiveModes carried).
   - himotoki: a DSAR/FOIA request-draft generator — own-data-only (G3), true-requester /
     no-pretext (G4), PII-as-encrypted-envelope never plaintext (G6), no mass-filing (G8),
     verify-before-dispatch (G14), outbound-gated (G10).

4. **intel-fleet-readiness tool** (`70-tools/intel-fleet-readiness/`) — the Murakumo deploy
   **pre-flight checklist**: runs each actor's own suite, counts tests, lists materialised
   Datom artifacts, and reports the per-actor blocking outward gate, emitting a
   READY-PENDING-GATE verdict. It **never deploys**. Running it surfaced and closed three
   missing-artifact gaps (kabuto/tadori/kanjo).

## Consequences

- **227 tests green** across the cohort; **8/8 actors READY-PENDING-GATE**.
- **15 persisted kotoba Datom artifacts** materialised in-repo — each the byte-for-byte
  record a live kotoba ingest would append once its gate opens.
- The constitutional boundary is unchanged and explicit: no live deploy/ingest/publish/
  promotion happened or can happen without the human gate; every artifact and report states
  its blocking gate. All inference Murakumo-only; all state kotoba Datom EDN (no SQL/RW).
- mitooshi now demonstrates the honest dual outcome — a real miscalibrated model is refused,
  a calibrated+signed one clears — so the calibration_gate is shown to work, not asserted.
- Future work: live operator-attestation flow to flip the gates (per-actor); kanae
  Rust/WASM fiscal-flow visualization (separate toolchain); placing the ready actors into
  `50-infra/murakumo/fleet.toml` once Council-ratified.

## Alternatives Considered

- **Execute the live fleet deploy directly.** Rejected: constitutionally impossible without
  Council Lv6+ + operator; an agent flipping an outward gate would violate the actors'
  G7/G10/G14 and the no-server-key invariant (2605231525).
- **Persist intel via live kotoba-server ingest instead of in-repo EDN artifacts.**
  Rejected for the same gate reason; in-repo append-only EDN is the charter-clean
  materialisation (identical Datoms, replayable, gate-deferred).
- **Skip per-actor tests, only build the readiness tool.** Rejected: readiness is meaningful
  only if each actor's invariants are actually pinned by a green suite — the tool reports
  test counts precisely so an empty suite cannot read as "ready".

## Honesty (R1)

Design + offline analysis only. Seeds are `:representative` (bounded, illustrative — not
live coverage). mitooshi's non-trivial calibrated-clears result uses a synthetic
single-regime fixture; the real two-regime `:representative` trail remains honestly
G7-refused. No foundry/live-link/live-actuation/live-ingest occurred; all such steps remain
Council Lv6+ + operator gated.
