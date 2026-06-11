---
id: adr-2606063000-session-close-ooyake-world-model-reconcile
title: "ADR-2606063000: Session close — ooyake↔tsumugi world-model reconcile layer (self-paced /loop maturation)"
status: active
doc_type: adr
topic: ooyake-world-model-reconcile
authoritative: true
last_verified: 2026-06-06
priority: 5.0
axis: architecture
weight: 0.5
depends_on:
  - adr-2606021600-ooyake-world-government-atlas
  - adr-2606011800-tsumugi-spirit-intel-power-graph
  - adr-2606011000-engi-organism-ontology
related:
  - 90-docs/adr/2606023200-session-close-ooyake-world-government-atlas.md
---

# Context

Question that opened the session: *「いまの全世界政府の actor で 情報の ingest と kotoba での永続化は
それぞれのアクターごとに設計されているか? また world model として reconcile する設計になっているか?」*

Answer at the time: per-actor ingest + kotoba persistence WAS designed (ooyake catalogs structure;
danjo/kanae/toritsugi/himotoki each consume it), but the **world-model reconcile** — joining ooyake's
structural atlas to tsumugi's karma graph over the `:gov.unit/organism` ref named in ADR-2606021600 §3 —
was **design-only**: the attr was populated by no unit and joined by no code. This session built that
missing layer over a self-paced `/loop` (10 iterations, 30-min cadence), then closed.

# Decision

Built `20-actors/ooyake/cells/world_model/` — the cross-actor reconcile of structure (ooyake `:gov.unit/*`)
and karma (tsumugi `:organism/* + :en/*`), offline + deterministic + read-side (G9), with ZERO invariant
amendments. Design recorded in **ADR-2606021600 § "World-Model Reconcile Layer"** (the canonical home).

# Consequences

**Landed (all offline, `bash 20-actors/ooyake/deploy/run_tests.sh` ALL GREEN):**

- **Reconcile cell** (`reconcile_world_model`) — confirmed / derived / dangling / proposed classification of
  every power-bearing unit; civic surface (窓口/ward/division) excluded by construction (G1/G10); proposals
  written to `out/world-model.kotoba.edn`, never to a committed seed.
- **9 confirmed links**, every one a publicly-documented regulator→entity tie wired across BOTH graphs
  (ooyake `:gov.unit/organism` + tsumugi `:organism` node + `:tends`/`:custodies` 縁): METI, FSA, BOJ,
  **US SEC** (a genuine atlas gap — `gov.usa.finreg` was the CFTC; added `gov.usa.sec`, Q827960), US Fed,
  EU, UK CMA, US DOJ Antitrust, JFTC. reconciled 0.03% → 0.26% (9/3,506 power-bearing units); the remainder
  honestly `:proposed`/`:representative` (no fabrication, G5). Taiwan NDF→TSMC deliberately deferred (the
  atlas carries no Taiwan units; a contested-status country addition needs an explicit human decision, G11).
- **Government-stewardship join** (20 paths) — reconciled gov-unit → organism → 縁 → entity; the queryable
  payload (`gov.eu --:tends--> Apple`, `gov.usa.sec --:tends--> NVIDIA`, …).
- **Bidirectional query** — `regulators_of` / `stewarded_entities_of`, consumed by tsumugi/danjo/kanae via
  `deploy/consumers_example.py`; CLI `scripts/world_model.py --entity <org>`.
- **kotoba persistence** — `deploy/ingest_world_model.py` → named graph `world-model-v1` (`world.gov`
  entities; `world/organism` + `world/stewards`); dry-run default, live operator-gated, never auto-seals.
- **Hardening** — `world_model_coverage.py` gate (7 invariants) + `test_consistency.py` SSoT drift-lock
  (6 checks) + 16-test cell suite incl. EDN round-trip; registered as ooyake's 7th cell (manifest).
- **Verified zero repo drift** — `test_actor_registry_parity` + `manifest-lexicon-drift` PASS; ooyake seed
  integrity PASS.

**Honest pending / not done (gated or out-of-scope):**

- Coverage is near-saturated against tsumugi's ~16-corp seed; further confirmed links need either the Taiwan
  go-ahead, tsumugi corp-seed expansion, or new direction — flagged, not pursued autonomously.
- `live` reconcile + `:gov.unit/organism` write-back to committed seeds = Council Lv6+ + operator gated.
- Pre-existing env issue surfaced (NOT introduced here): `pydantic-core 2.46.4` vs required `2.41.5` blocks
  ~22 repo audit tests; left for an explicit operator decision (global-env mutation).
- Nothing committed at close; the `/loop` cron was cancelled after value saturated.

# Alternatives Considered

1. **Inflate `confirmed` with derived/auto-proposed links** — rejected: would claim reconciliation the system
   generated itself; the confirmed/proposed split exists precisely to keep coverage honest (G5).
2. **Add Taiwan autonomously for the NDF→TSMC link** — rejected in an unattended loop: contested-status
   country addition is a deliberate, human-gated decision (G11 neutrality).
3. **A separate world-model actor** — rejected: ooyake owns `:gov.unit/organism` and is the structural SSoT;
   the join belongs in ooyake, consumed by the siblings.

# References

- ADR-2606021600 (ooyake world government atlas — § "World-Model Reconcile Layer" is the design home)
- ADR-2606011800 (tsumugi) · ADR-2606011000 (engi-organism) · ADR-2605262130 + 2605312345 (kotoba)
- ADR-2605215000 (Murakumo-only) · ADR-2605192100 (§1.12 Transparent Force) · ADR-2605192200 (Charter Rider)
- `20-actors/ooyake/cells/world_model/` · `scripts/world_model{,_coverage}.py` · `deploy/ingest_world_model.py`
- `20-actors/ooyake/MATURITY.md` (per-iteration build log) · `20-actors/tsumugi/data/seed-power-graph.kotoba.edn`
