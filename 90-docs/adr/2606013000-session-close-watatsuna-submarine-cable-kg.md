---
id: adr-2606013000-session-close-watatsuna-submarine-cable-kg
title: "ADR-2606013000: Session close — watatsuna 綿津綱 world submarine-cable knowledge graph (R0+R1+R2) + watatsumi cable-laying robotics"
status: active
doc_type: adr
topic: session-close-watatsuna-submarine-cable-kg
authoritative: false
last_verified: 2026-06-01
priority: 4.0
axis: process
weight: 0.40
priority_note: "Documentation-only session-close record; authoritative design = ADR-2606012600"
authoritative_for: []
depends_on:
  - adr-2606012600-watatsuna-submarine-cable-knowledge-graph-and-watatsumi-cable-laying-robotics
related:
  - adr-2606011800-tsumugi-spirit-intel-power-graph
  - adr-2605252200-watatsumi-civilian-submersible-r0
supersedes: []
superseded_by: []
---

# ADR-2606013000: Session close — watatsuna 綿津綱 submarine-cable KG (R0+R1+R2)

**Status**: active (documentation-only)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Documentation-only closure for the 2026-06-01 session answering the founder ask
*「海底ケーブルのデータベースは kotoba server / actor として設計されているか? etzhayyim.com に actor
として表示できるか? 必要なら敷設 robotics も設計」* and the follow-ups *a + c + 敷設 robotics* →
*next step* → *next step*. Authoritative design = **ADR-2606012600**; this record only
narrates what shipped.

Audit verdict: only legacy `etzhayyim` cable lexicons existed (RisingWave-era record schemas) —
no actor, no kotoba dataset, no ADR. This session built the full stack to R2, design-only.

# Decision (what shipped)

**R0 — knowledge-graph actor + lexicon migration + robotics design**
- New Tier-B observation actor `20-actors/watatsuna/` (manifest, README, CLAUDE), same-root
  sibling of watatsumi 綿津見 (observation face ↔ operation face).
- Vocabulary `00-contracts/schemas/submarine-cable-ontology.kotoba.edn` (`:cable/* :station/*`
  + `:chokepoint` · `:cable.link/* :cable.seg/*` + `:traverses` · `:cable.fault/*` as-of history).
- Seed `data/seed-cable-graph.kotoba.edn` = 14 real public systems · 22 stations · 43 links ·
  11 chokepoint segments · 2 fault bulletins (all `:representative`).
- `methods/analyze.py` (stdlib) → aggregate-first `out/intel-report.md` +
  `out/cable-criticality.kotoba.edn`. Top chokepoints (seed): Malacca 490 / Luzon 455 /
  Gibraltar 324 / Suez 250 / S-China-Sea 191 Tbps.
- kotoba-native lexicons `00-contracts/lexicons/com/etzhayyim/cable/*` (registerCableSystem /
  registerLandingStation / registerSegment / flagCableFault) + `MIGRATION-NOTES.md` mapping
  all 7 legacy `etzhayyim` lexicons; **`flagSubseaCableTamper` RETIRED, not ported** (intent
  adjudication → violates G4).
- watatsumi cable-laying robotics fleet `20-actors/watatsumi/data/cable-laying-fleet.kotoba.edn`
  (Tsuna-suki 綱鋤 / Horinuki 掘抜 / Tsugite 接手 / Tedori 手繰 REPAIR-ONLY / Kikimimi 聞耳 DAS),
  N8-bound; manifest + README + CLAUDE updated.
- Display: registered in `INFRA_ACTORS` → `did:web:etzhayyim.com:actor:watatsuna` at
  `/actor/watatsuna/did.json`.

**R1 — ingest + visualization**
- `methods/ingest.py` TeleGeography-bridge (public submarinecablemap-shaped JSON → kotoba
  EAVT; offline default, live fetch G7-gated + refused R0 scaffold). Merges seed →
  **18 cables / 26 stations / 2234 Tbps** (Malacca 940 / Luzon 681 Tbps).
- `viz/` self-contained canvas 2D resilience map (`cable-resilience.htm`), data inlined.

**R2 — fleet planner + 3D globe**
- `methods/plan.py` watatsuna→watatsumi resilience fleet plan (`out/resilience-plan.{md,kotoba.edn}`):
  **20 recommendations** (9 lay-diverse-route / 4 pre-stage-repair / 7 monitor), each tasking
  named watatsumi robot classes. **Redundancy + repair + monitor ONLY — 0 interdiction/cut
  recommendations possible by construction** (verified).
- `viz/cable-globe.htm` self-contained canvas orthographic 3D globe (drag-rotate, auto-spin,
  great-circle arcs), cross-linked with the 2D map.

**Verification**: full chain `ingest → analyze → plan → viz` runs clean; 4 lexicons + 2
manifests valid JSON; EDN round-trips; both viewers self-contained (no external fetch);
plan EDN has 0 cut/interdiction recommendations. `tsc` not installed locally — the
`INFRA_ACTORS.watatsuna` entry mirrors the `dataset-pinner` libp2p pattern + uses the
in-scope `SIMEON_PEER_ID`.

# Consequences

- A kotoba-native, on-chain-resolvable submarine-cable knowledge graph as a first-class
  etzhayyim actor, with a concrete observation→operation link to watatsumi's N8-bound fleet.
- Dual-use risk handled structurally: G1 public-only, G2 resilience-not-interdiction, G4 no
  intent adjudication, tamper-flag lexicon retired, planner cannot emit interdiction.

# Honest limitations

- All design-only (R0–R2). Bounded `:representative` seed (not exhaustive); coordinates
  rounded to landing town; robotics no-hardware.
- kami-engine WASM 3D globe integration (shared kanae/shibuya renderer) **deferred to R3**;
  current globe is standalone canvas. Live TeleGeography/AIS/fault-bulletin ingest and real
  fleet tasking remain **G7 Council + operator gated**. Per-feed ODbL attribution to confirm
  before any live ingest.
- **Working tree uncommitted at session close** — commit/PR on a feature branch pending
  operator action (no commit hashes to record yet).

# References

- ADR-2606012600 (authoritative design) · `20-actors/watatsuna/` · `20-actors/watatsumi/` ·
  `00-contracts/schemas/submarine-cable-ontology.kotoba.edn` ·
  `00-contracts/lexicons/com/etzhayyim/cable/` ·
  `50-infra/etzhayyim-did-web/src/registry/infra-actors.ts`
