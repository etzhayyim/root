---
id: adr-2606023800
title: "ADR-2606023800: Session close — tsutae raised to sarutahiko-class substrate (cells + factory + device BOM + toolchain + viewer)"
status: active
doc_type: adr
topic: session-close-tsutae-sarutahiko-parity-uplift
authoritative: false
last_verified: 2026-06-02
priority: 4.0
axis: process
weight: 0.40
priority_note: "session-close record; authoritative design lives in ADR-2606023600 + ADR-2605261300"
authoritative_for: []
related:
  - adr-2606023600-tsutae-handheld-cleanroom-factory-and-device-bom-supply-chain
  - adr-2605261300-tsutae-handheld-communication-tier-b-actor-r0
  - adr-2606013100-sarutahiko-truck-factory-full-robotics-and-loader
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606023600 (tsutae factory + device BOM — the design authored this session)
  - ADR-2605261300 (tsutae R0 master — the actor matured this session)
---

# ADR-2606023800: Session close — tsutae raised to sarutahiko-class substrate

**Date**: 2026-06-02
**Status**: ACTIVE (documentation-only session closure)
**Deciders**: Jun Kawasaki

# What shipped this session

Driven by a `/loop` ("raise tsutae to sarutahiko parity") across three iterations,
tsutae went from declaration-only (8 named-but-absent RuntimeError cells, no BOM,
no factory) to a sarutahiko-class substrate. Authoritative design = ADR-2606023600.

**Actor (`20-actors/tsutae/`, 57 files)**
- 8 Pregel cells implemented (`state_machine.py` + `cell.py` + `__init__.py` each),
  with 7 constitutional-gate guards in-code (G9/G6/G3/G2/G7/G8/G4/G10).
- `cells/test_state_machines.py` → **8/8 green**.
- `manifest.edn` (G1–G18), 10 cell `.edn`, `device-order` + `production-ledger`.
- `py/agent.py` + `test_agent.py` → **11/11 green**; `requirements.txt`.
- `kotoba/schema.edn` (38 attrs) + `seed.edn` + `deploy.sh`.
- 10 `lex/*.edn` lexicons.

**Factory scene (`70-tools/e7m-sim/scenes/tsutae-factory-r0/`, 29 files)**
- `building.edn` — 63 parts incl. a **20-part device BOM** (the smartphone supply
  chain) with internal/`:representative` provenance + per-part gate.
- `factory.scene.json` (48×30 m Class-100k cleanroom), `construction.edn` (15-step
  4D), `robots.edn` (6 build robots), `production.edn` (12 stations → 8 cells).
- 6 toolchain scripts (kotoba_gen / production_gen / procurement / engineering /
  ifc_export / process_gen) adapted; generate **63-part SBOM, 189 kotoba entities,
  15-step 4D order, IFC 763 STEP, 81 robot ops** (drainage-sizing NG honestly
  flagged).
- `viz_gen.py` → `tsutae-factory.htm` self-contained viewer (build + produce anim).
- `KAMI_APP_SPEC.md` — spec for the deferred Rust crate.

# Verification

```
cell state-machine tests   8/8 passed
agent tests               11/11 passed
tsutae EDN (24 files)      all parse (real EDN reader)
scene toolchain            kotoba_gen / production_gen / viz_gen all OK
scene cross-refs           all resolve (consumes/reveals/depends-on/robot)
```

# Known blocker (carried forward)

`kami-app-tsutae-factory` Rust WASM physics crate is **not built**: the kami-engine
submodule has no Rust source in this checkout (only `pkg/` artifacts) and cannot be
repopulated non-destructively. Standalone `tsutae-factory.htm` ships the user-facing
visualization in the interim; the crate is fully specced (KAMI_APP_SPEC.md) and the
JSON/entry-name data contract is fixed, ready to drop in once the submodule source
is restored.

# Honest scope

Design + data-model + state-machine + standalone-viz only. No real cleanroom, no
電波法/技適 cert, no real robots, no live USDC broadcast (intent-only). Cells remain
Council-gated (`.solve()` → RuntimeError until ADR-2605261315). R1 benchtop and R3
community-scale gated.

# References

- ADR-2606023600 — tsutae factory + device-BOM supply chain (authoritative design)
- ADR-2605261300 — tsutae R0 master
- `deps.toml [[adrs]]` — both ADRs registered
