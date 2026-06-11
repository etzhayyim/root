---
id: adr-2606022400
title: "ADR-2606022400: Session close — himawari R1 future-ADR + cell coverage maturation (88→146, ≥96%)"
status: active
doc_type: adr
topic: session-close-himawari-r1-adr-and-coverage-maturation
authoritative: false
last_verified: 2026-06-02
priority: 4.0
axis: process
weight: 0.40
priority_note: "session-close record; authoritative design lives in ADR-2606022300 + ADR-2606021200"
authoritative_for: []
related:
  - adr-2606022300-himawari-solar-pv-r1-benchtop-module-assembly-poc
  - adr-2606021200-himawari-solar-pv-manufacturing-r0
  - adr-2605261000-labor-liberation-transition-mechanism
  - adr-2605192300-etzhayyim-bootstrap-council-five
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606022300 (himawari R1 future-ADR — the design authored this session)
  - ADR-2606021200 (himawari R0/R0.1 — the actor matured this session)
---

# ADR-2606022400: Session close — himawari R1 future-ADR + cell coverage maturation (88→146, ≥96%)

**Date**: 2026-06-02
**Status**: ACTIVE (documentation-only session closure)
**Deciders**: Jun Kawasaki

## Context

Documentation-only closure for the session that began by asking to **topologically
sort the next steps from the README**, then proceeded `do it` → `do it` → a `/loop
30min 成熟度とcoverage を高めて` self-paced maturation loop. The work is entirely on
the himawari (向日葵) solar-PV actor on the active dev branch (a concurrent
background /loop migrated the working branch from `feat/himawari-solar-pv-manufacturing`
to `feat/ooyake-world-gov-atlas` mid-session; all commits land on the shared dev
chain, consistent with that process's operation).

## Decision (what shipped)

1. **Topological sort of README next-steps.** Extracted the active-inference axes
   "Next active-inference action" column + governance pipeline into a dependency DAG;
   identified **Bootstrap Council Seats 2–5 confirmation (RFP 〆 2026-06-19)** as the
   critical-path root gating `testnet → mainnet`, TitheRouter (Metabolism), and
   himawari R1. Layer-0 (Council-independent) work is the only himawari task
   actionable now → executed it.

2. **ADR-2606022300 — himawari R1 future-ADR (proposed).** Authored the "future ADR"
   that ADR-2606021200's R1 roadmap row named, so R1 execution needs no design
   round-trip once activation holds. Defines: **Activation Gate A1∧A2∧A3** (Council
   confirmed / PV-process-engineer steward enrolled / LANDS brownfield parcel donated
   — all pending 2026-06-02, R1 fully blocked today); **R1 scope** = lowest-capex
   benchtop module-assembly line first (bought-in §2(g)-audited cells; cell-fab is R2,
   §G2 closure is R3) + real F10 palletize + one domestic kami-autodrive leg + first
   real G7 Liberation Metric data point; **Parcel Requirement Spec P1–P5** (brownfield
   G9/N8, 4-layer Land Trust). Committed `5ef0ce2d5`.

3. **himawari cell coverage maturation (two /loop ticks), 88 → 146 tests, cell.py ≥96%.**
   R0.1 tests only exercised `solve()` with `datalog=None`, leaving the substrate-boundary
   write paths and the constitutional-gate refusal branches uncovered.
   - **Tick #1 (`b3c2836fa`, 88→129):** 6 new files (20 tests) injecting fake kotoba
     hosts / fake StateGraph to cover every cell's kotoba write path (3 branches each:
     host-present real datoms + attribute namespace, host-absent no-op never faking
     success, host-raises swallowed) + the cell_process LangGraph DAG-topology branch.
   - **Tick #2 (`7feb764c6`, 129→146, all cells ≥96%):** 4 new files (17 tests) pinning
     G2/G11/G12 refusal + normalization branches — polysilicon G2 refusals + robot-sig
     auto-fill (96→99%); module_assembly G12 external/empty destination + flash-bin +
     **G11 `_lot_exists` live-host provenance query** confirm/empty/fail-closed (93→99%);
     panel_loading pallet/robot edges (94→100%); outbound_logistics bare-DID +
     placeholder + VehicleClass parser fallback (95→100%).

   Full himawari suite now **17 files / 146 tests green**; cell.py line-coverage:
   polysilicon/module/supply 99%, panel/outbound 100%, ingot 98%, cell_process 96%.
   Remaining misses are defensive-unreachable guards. README + CLAUDE.md test-count and
   coverage claims updated to match.

## Consequences

- himawari R1 design is on disk and indexed; only physical activation (A1∧A2∧A3) waits.
- The actor's substrate-boundary write contracts (EAVT datom shape, fail-closed
  provenance, minItems-1 witness arrays) and constitutional-gate refusals are now
  regression-locked, not merely asserted in prose.
- No code behavior changed (tests + docs only); actor remains R0.1, R1 Council-gated.
- **Honest caveats**: coverage measured via a local `coverage` venv (not committed);
  the 6 kotoba-write tests use fake hosts (no live kotoba binding exists pre-R1);
  remaining ~1–4% per cell is defensive guards left intentionally uncovered.

## Alternatives Considered

- **Chase 100% on every cell.** Rejected — the residual lines are defensive-unreachable
  guards (e.g. polysilicon `chainOfCustody < 1`, which the synthesizer makes impossible);
  contorting inputs to hit them would test the test, not the actor.
- **Move to a different actor for the coverage ticks.** Deferred — himawari is the active
  branch context and had the clearest, highest-leverage gaps; sibling-actor maturation is
  the natural next /loop target.

## References

- `/90-docs/adr/2606022300-himawari-solar-pv-r1-benchtop-module-assembly-poc.md` — R1 design (authoritative)
- `/90-docs/adr/2606021200-himawari-solar-pv-manufacturing-r0.md` — R0/R0.1 master charter
- `/20-actors/himawari/README.md` + `/20-actors/himawari/CLAUDE.md` — actor docs (test counts updated)
- Commits: `5ef0ce2d5` (R1 ADR) · `b3c2836fa` (coverage tick #1) · `7feb764c6` (coverage tick #2)
