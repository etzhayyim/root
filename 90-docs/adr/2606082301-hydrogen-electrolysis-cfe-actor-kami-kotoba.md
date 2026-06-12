---
id: adr-2606082301-hydrogen-electrolysis-cfe-actor-kami-kotoba
renumbered_from: "2606082300"
title: "ADR-2606082301: hydrogen electrolysis CFE efficiency actor — actor logic, kami simulation, kotoba deploy"
status: active
doc_type: adr
topic: hydrogen-electrolysis-cfe-actor-kami-kotoba
authoritative: true
last_verified: 2026-06-08
priority: 5.0
axis: architecture
weight: 0.40
priority_note: "Records the placement and deploy boundary for the Hysata-style capillary-fed electrolysis efficiency actor: actor-specific decision logic lives under 20-actors, physics simulation under kami-engine, and KG deployment under kotoba."
authoritative_for:
  - hydrogen_electrolysis actor placement
  - kami-hydrogen-electrolysis-sim package placement
  - hydrogen electrolysis efficiency kotoba deploy boundary
depends_on:
  - "2606074500"
  - "2606074000"
related:
  - "2605262130"
supersedes: []
superseded_by: []
---

# ADR-2606082301: hydrogen electrolysis CFE efficiency actor — actor logic, kami simulation, kotoba deploy

**Status**: active
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki

## Context

The working question was how to turn the Hysata Capillary-fed Electrolysis
(CFE) idea into an Etz Hayyim actor that can compare next-generation water
electrolysis designs for efficiency:

- commercial alkaline electrolysis as a baseline;
- Hysata-like CFE, focused on bubble-loss removal;
- CFE combined with zero-gap geometry, AEM assumptions, and high-pressure
  operation;
- SOEC as a useful-heat comparison case.

The placement was corrected during the session:

- the actor itself belongs under `20-actors`;
- the physics / engineering simulation belongs under `kami-engine`;
- deploy and query exposure belongs under `kotoba`;
- the simulation runtime is the kami engine, not Isaac Sim.

The user also required the active kotoba node and `KOTOBA_TOKEN` handling to be
compatible with the Murakumo fleet session.

## Decision

Create a narrow three-layer implementation:

1. **Actor layer**:
   `20-actors/hydrogen_electrolysis/` owns the domain decision surface. It
   runs the comparison, emits a Markdown report, and produces datom-style rows
   for kotoba ingestion.
2. **Simulation layer**:
   `40-engine/kami-engine/kami-hydrogen-electrolysis-sim/` owns the deterministic
   kami simulation package. It models electrical energy, heat-inclusive energy,
   efficiency, bubble penalty, membrane / ionic resistance, activation loss,
   water-transport penalty, balance-of-plant loss, pressure handling, and
   stack-level summaries.
3. **Kotoba layer**:
   `40-engine/kotoba/crates/kotoba-kotodama/cells/hydrogen_electrolysis_efficiency/`
   exposes the cell surface, while
   `20-actors/hydrogen_electrolysis/kotoba/` owns the deploy script and KG ingest
   adapter for the actor's graph.

The canonical low-temperature recommendation is
`cfe-zero-gap-aem-high-pressure`: it combines CFE's bubble-loss reduction with
zero-gap ionic distance reduction, AEM-compatible low-cost catalyst assumptions,
and high-pressure output to reduce downstream compression burden.

SOEC remains modeled as a separate high-temperature option. It can show lower
electrical demand when useful heat is available, but it is not collapsed into the
same low-temperature ranking because its system boundary includes high-grade
heat.

## Live deploy note

The running kotoba node was available via launchd as `com.etzhayyim.kotoba` on
`http://127.0.0.1:8077`, with the health endpoint returning `200 OK`.

No `KOTOBA_TOKEN` was present in the shell environment during the session. The
deploy adapter therefore derives a local JWT-shaped bearer token from
`kotoba whoami`'s Keychain-backed DID when `KOTOBA_TOKEN` is absent. The token is
not printed. This keeps the deploy compatible with the active Murakumo / kotoba
node without writing secrets to the repository.

The live KG ingest succeeded with 5 entities / 68 quads. Readback confirmed the
four modeled cases and the recommendation
`cfe-zero-gap-aem-high-pressure`. Debug deploys created duplicate graph rows;
the distinct case set and recommendation are correct. Replacement deploy is
available through `KOTOBA_REPLACE=1`, but default deploy avoids deletion because
`kg.delete` timed out on the active node during the session.

## Consequences

- The actor is no longer a standalone experiment outside the tree; it is placed
  in the actor layer and deploys into kotoba.
- The simulation remains deterministic, stdlib-only, and testable without a GPU
  or Isaac Sim install.
- The kotoba cell can be tested in-process, while live deploy remains an
  explicit actor operation.
- Generic `kotoba commit` is not part of the deploy path because KG ingest
  already commits distributed datoms; the generic commit path hit an unrelated
  existing WASM `program_type` issue on the active node.

## Verification

- `python3 tests/test_model.py` in `kami-hydrogen-electrolysis-sim`: pass.
- `python3 test_electrolysis.py` in the actor methods directory: pass.
- `python3 -m cells.hydrogen_electrolysis_efficiency.test_cell` in
  `kotoba-kotodama`: pass.
- `KOTOBA_URL=http://127.0.0.1:8077 ./deploy.sh`: live ingest pass.

## References

- `20-actors/hydrogen_electrolysis/`
- `40-engine/kami-engine/kami-hydrogen-electrolysis-sim/`
- `40-engine/kotoba/crates/kotoba-kotodama/cells/hydrogen_electrolysis_efficiency/`
- ADR-2606074500 — kotoba Python sibling placement taxonomy
- ADR-2606074000 — kotoba submodule placement mechanics
