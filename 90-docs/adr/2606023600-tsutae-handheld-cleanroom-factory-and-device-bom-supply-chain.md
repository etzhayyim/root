---
id: adr-2606023600-tsutae-handheld-cleanroom-factory-and-device-bom-supply-chain
title: "ADR-2606023600: tsutae (伝え) — handheld cleanroom factory + device-BOM supply chain + 8-cell substrate (sarutahiko-parity uplift)"
status: proposed
doc_type: adr
topic: tsutae/factory/supply-chain
authoritative: true
last_verified: 2026-06-02
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "raises tsutae from declaration-only R0 to sarutahiko-class substrate (cells + factory + BOM + toolchain + viewer)"
authoritative_for:
  - 20-actors/tsutae/cells
  - 70-tools/e7m-sim/scenes/tsutae-factory-r0
related:
  - adr-2605261300-tsutae-handheld-communication-tier-b-actor-r0
  - adr-2606013100-sarutahiko-truck-factory-full-robotics-and-loader
  - adr-2606010030-giemon-factory-r0-kami-engine-kotoba-4d-bim
  - adr-2606011500-kami-engine-reusable-vs-repo-specific-separation-plan
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
supersedes: []
superseded_by: []
depends_on:
  - 2605261300-tsutae-handheld-communication-tier-b-actor-r0
  - 2606013100-sarutahiko-truck-factory-full-robotics-and-loader
  - 2605262130-kotoba-storage-substrate-unification
  - 2605215000-etzhayyim-inference-murakumo-only-no-runpod
---

# ADR-2606023600: tsutae handheld cleanroom factory + device-BOM supply chain + 8-cell substrate

**Status**: proposed
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

ADR-2605261300 scaffolded tsutae 伝え as a Tier-B handheld-device actor, but left it
**declaration-only**: the 8 Pregel cells were named in the manifest yet had no source
(`20-actors/tsutae/cells/` did not exist; importing any cell raised `RuntimeError`),
there was no device BOM, no factory, and no toolchain. A coverage audit framed the
gap bluntly: *"a smartphone cannot be built end-to-end; the battery/display/camera/
modem/PCB supplier components are entirely absent; all 8 assembly cells are import-
time RuntimeError."* Meanwhile two sibling manufacturing actors — sarutahiko (truck,
ADR-2606013100) and giemon (robot factory, ADR-2606010030) — had reached a mature
R0 pattern: 8–9 implemented cells + state-machine tests, a `*-factory-r0` scene
(`building.edn` BOM + `factory.scene.json` + 4D `construction.edn` + `robots.edn` +
`production.edn`), a shared Python toolchain (SBOM / kotoba-ingest / IFC / engineering /
procurement / production), and a kami-engine WASM sim crate + `.htm` viewer.

This ADR records raising tsutae to that same bar.

# Decision

Implement the full sarutahiko-class substrate for tsutae, adapted to handheld
electronics and its 14 constitutional gates (ADR-2605261300):

1. **8 Pregel cells implemented** (`20-actors/tsutae/cells/`) — `pcb_smt`,
   `chassis_assembly`, `display_attachment`, `firmware_load`, `final_qc`,
   `packaging`, `device_attestation`, `recycling_intake`. Each has a
   langgraph-free `state_machine.py` (pure transitions) + a `cell.py` LangGraph
   wrapper whose `.solve()` retains the R0 Council gate (`RuntimeError` until
   ADR-2605261315). **Constitutional gates are enforced in-code as transition
   guards**: G9 open-SoC (proprietary SoC rejected, N1), G6 mic hardware kill
   switch, G3 repair-modularity (adhesive ≤5 g / no parts-pairing), G2 bootloader
   unlock, G7 blob ratio ≤5%, G8 anti-addiction UX, G4 ≥2-robot witness quorum,
   G10 ≥80% take-back recovery. `cells/test_state_machines.py` exercises all 8 +
   7 gate guards → **8/8 green**.

2. **Actor substrate** — `manifest.edn` (G1–G18 + 10 cells + lex), 10 cell `.edn`
   descriptors, `device-order` + `production-ledger` datalog cells, `py/agent.py`
   (lifecycle handlers + G9 SoC gate, Murakumo-only G16) with `test_agent.py`
   **11/11 green**, `kotoba/schema.edn` (38 EAVT attrs) + `seed.edn` + `deploy.sh`,
   and 10 `lex/*.edn` lexicons.

3. **`tsutae-factory-r0` scene** (`70-tools/e7m-sim/scenes/tsutae-factory-r0/`) —
   a **48 × 30 m Class-100k cleanroom** (NOT a heavy steel plant; anti-mass-
   production G12, ≤200 devices / 8-hr line). `building.edn` carries **63 parts**:
   43 plant parts (shell + cleanroom HVAC + SMT/assembly/test equipment) **plus a
   20-part group-P device BOM — the smartphone supply chain that was missing**
   (SoC, PMIC, DRAM, storage, 8-layer PCB, passives, LFP battery, display, touch,
   camera, USB-C, removable cellular, Wi-Fi/BT, speaker, MEMS mic + kill switch,
   Al chassis, fasteners, antenna, haptic, IMU). Each device part carries
   `:supplier-did` (internal: silicon/igata/hikari = the vendor-independence
   chain) or honest external `:representative`, plus the gate it satisfies.
   `factory.scene.json` + 15-step `construction.edn` + `robots.edn` +
   12-station `production.edn` complete the scene; **all cross-references resolve**
   (consumes→parts, reveals→scene ids, depends-on→steps, robot→registry).

4. **Shared toolchain** — the 6 sarutahiko/giemon scripts are reused, with
   `production_gen.py` adapted to handheld ops (SMT→筐体→display→FW→QC→pack→attest→
   EOL, 43 mfg-ops) and `procurement.py` extended with an `:internal` actor branch
   + electronics suppliers. `kotoba_gen.py` (real EDN reader) emits the
   **63-component CycloneDX SBOM, 189 kotoba entities, 15-step 4D order, IFC
   (763 STEP entities), engineering check (81 robot ops)** — and honestly flags a
   drainage-sizing NG, mirroring sarutahiko's real-deficiency detection.

5. **Self-contained viewer** — `viz_gen.py` → `tsutae-factory.htm`, a no-build,
   no-WASM, no-network canvas viewer (data inlined) animating both the 4D build
   and the device production flow. Mirrors the documented self-contained-viz
   pattern (watatsuna / shibuya).

6. **kami-app crate deferred (documented blocker)** — the Rust
   `kami-app-tsutae-factory` (`run_tsutae_factory_{produce,build}_v1` WASM physics
   sim) belongs in the kami-engine submodule (ADR-2606011500 §4). In the current
   checkout that submodule has **no Rust source** (0 `Cargo.toml` / `.rs`; only
   built `pkg/` artifacts) and cannot be repopulated non-destructively, so the
   crate cannot be compiled here. The data contract (JSON orders + `.edn` entry
   names) is fixed; the spec is captured in
   `70-tools/e7m-sim/scenes/tsutae-factory-r0/KAMI_APP_SPEC.md`.

# Consequences

- The original audit verdict is partially overturned: tsutae now has an explicit,
  machine-validated **smartphone supply chain** (group-P BOM with provenance), an
  executable 8-stage assembly process (cells + production line), and a buildable
  factory model. Internal vs external sourcing is stated honestly — only SoC/PMIC
  (silicon), battery (hikari), and chassis (igata) are internal today; display,
  camera, modem, PCB, passives remain external `:representative` (not yet sourced).
- No constitutional invariant is touched: Murakumo-only (G16), kotoba-EAVT-native
  (G17), USDC + TitheRouter (G18), no-server-key (G15), open-SoC-only (G9/N1),
  SBT↔SBT internal only (N9). Cells stay Council-gated (`.solve()` → RuntimeError).
- **Honest scope**: design + data-model + state-machine + standalone-viz only. No
  real cleanroom, no 電波法/技適 certification, no real robots, no live USDC
  broadcast (intent-only). The kami-genesis WASM physics sim is not built (blocked).
  R1 benchtop (ADR-2605261315) and R3 community-scale remain Council + LANDS.md
  gated.

# Alternatives Considered

- **Force-clone the kami-engine submodule to build the crate** — rejected;
  destructive to committed `pkg/` artifacts and unauthorized. Deferred via spec.
- **Skip the device BOM, only do the factory shell** — rejected; the device BOM
  *is* the supply-chain answer the audit demanded.

# References

- ADR-2605261300 — tsutae R0 master (cells/gates/non-goals)
- ADR-2606013100 — sarutahiko truck factory (pattern source)
- ADR-2606010030 — giemon factory 4D-BIM (toolchain origin)
- ADR-2606011500 — kami-engine reusable-vs-repo-specific separation (submodule rule)
- `70-tools/e7m-sim/scenes/tsutae-factory-r0/KAMI_APP_SPEC.md` — deferred crate spec
