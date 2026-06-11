---
id: adr-2605051430-drive-cad-jbeam-sbom-pipeline
title: "ADR-2605051430: drive CAD to JBeam to SBOM pipeline"
status: proposed
doc_type: adr
topic: drive-cad-jbeam-sbom-pipeline
authoritative: true
last_verified: 2026-05-05
authoritative_for:
  - driver.etzhayyim.com CAD to JBeam import architecture
  - kami-cad-import crate scope
  - vehicle part graph and CycloneDX SBOM emission
  - physical component recall and supplier-quality SBOM flow
related:
  - adr-0056-bpmn-as-actor
  - adr-2604251830-shannon-optimal-layered-architecture
---

# ADR 2605051430 — drive (driver.etzhayyim.com) CAD → JBeam → SBOM pipeline

Status: proposed
Date: 2026-05-05
Owner: kami-engine
Supersedes: —
Superseded by: —

## Context

`driver.etzhayyim.com` (`kami-app-car-sim` + `kami-vehicle`) currently runs a hand-written parametric sedan: 86 nodes / 220 beams / 48 flat-shaded triangles, no CAD source, no part-level provenance, no SBOM.

The roadmap to BeamNG.drive-grade fidelity needs:
1. real CAD ingestion (STEP / glTF / OpenSCAD) → part graph with mass + inertia + hardpoints
2. JBeam topology auto-emission from the part graph (so 6 garage cars → 6 part-graphs, not 6 hand-written beam tables)
3. per-vehicle SBOM with full part lineage so `sbom.etzhayyim.com` can do CVE-style recall / supplier-quality alerts on physical parts (e.g. Takata airbag-style recalls) the same way it does on Rust crates
4. Software SBOM for the Rust crates is already covered by `cargo-cyclonedx` (see `60-apps/etzhayyim-project-watashi/native/watashi-host/sbom.cdx.json`); this ADR adds **vehicle BOM** in the same CycloneDX format so both flow through `sbom.etzhayyim.com`'s existing CVE pipeline.

## Decision

Add one new crate `kami-cad-import` between `kami-cad` (BREP kernel + assembly) and `kami-vehicle` (soft-body sim).

```
                     ┌───────────────────────────────────────┐
                     │ External CAD source                   │
                     │   STEP / IGES (FreeCAD CLI → glTF)    │
                     │   OpenSCAD (kami-scad parametric)     │
                     │   glTF mesh (decimated)               │
                     └────────────────┬──────────────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │ kami-cad::assembly::Assembly │  (existing)
                       │  PartInstance + transforms   │
                       │  AssemblyConstraint          │
                       └────────────┬─────────────────┘
                                    │
                                    ▼
                  ┌────────────────────────────────────┐
                  │ kami-cad-import::VehicleAssembly   │  (NEW)
                  │  VehiclePart {                     │
                  │    mass, inertia,                  │
                  │    aabb, hardpoints,               │
                  │    parent, break_group,            │
                  │    source { uri, sha256, license }, │
                  │    supplier { name, cpe, purl }    │
                  │  }                                 │
                  └────────────┬───────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                 ▼
     ┌──────────────────┐              ┌──────────────────┐
     │ jbeam_emit::emit │              │ sbom::cyclonedx  │
     │   → JBeam JSON   │              │   → CDX 1.5 JSON │
     │   nodes/beams/   │              │   type: device   │
     │   wheels/parts   │              │   per VehiclePart│
     └────────┬─────────┘              └────────┬─────────┘
              │                                 │
              ▼                                 ▼
     kami-vehicle::jbeam::load_*    sbom.etzhayyim.com register-sbom
     → simulated soft-body car      → SbomComponent graph → CVE match
```

### What lives where

| Concern | Crate / Module | Notes |
|---|---|---|
| BREP kernel + features + Assembly + BOM count | `kami-cad` (existing, unchanged) | already has `assembly::Assembly::get_bom()` |
| OpenSCAD parametric source | `kami-scad` (existing, unchanged) | feeds `kami-cad-import` for license-safe PoC vehicles |
| **Part graph data model** | `kami-cad-import::part` (NEW) | `VehiclePart`, `Hardpoint`, `VehicleAssembly`, `MaterialDensity` |
| **STEP / glTF → VehicleAssembly adapter** | `kami-cad-import::ingest::{step, gltf, scad}` (NEW) | Phase 1 PoC ships `scad` only; STEP / glTF stubs in Phase 1.1 |
| **VehicleAssembly → JBeam JSON** | `kami-cad-import::jbeam_emit` (NEW) | AABB-corner sampling + hardpoint-driven beam topology |
| **VehicleAssembly → CycloneDX 1.5** | `kami-cad-import::sbom` (NEW) | CDX `type: "device"` per part, `purl`, `cpe`, `evidence`, etzhayyim `properties` |
| Soft-body sim consumer | `kami-vehicle::jbeam::load` (existing, unchanged) | reads JSON output of `jbeam_emit` |
| SBOM consumer | `sbom.etzhayyim.com` (existing) | already ingests CycloneDX → `SbomComponent` graph → CVE match |

### CycloneDX choice (CDX 1.5)

Match the existing `sbom.etzhayyim.com` default (CLAUDE.md `60-apps/etzhayyim-project-sbom/CLAUDE.md` line 48). CDX 1.5 supports `type: "device"` for physical components — exactly the right primitive for an alternator, a brake disc, or a chassis subframe. No new format. No new pipeline. The vehicle BOM lands in the same `SbomArtifact` graph as software SBOMs and gets the same CVE / recall / supplier-quality treatment that already exists.

`type: "device"` carries:
- `manufacturer.name` (supplier)
- `cpe` (when manufacturer publishes a CPE — most don't, falls back to `purl`)
- `purl` (synthesized: `pkg:etzhayyim-vehicle/{vehicleId}/part/{partId}@{revision}?supplier=...`)
- `swid` (we leave empty — physical parts have no SWID)
- `evidence.identity` (sha256 of source CAD file, license, fetch URI)
- `properties[]`:
  - `cdx:etzhayyim:vehicle:break_group` (1..5, BeamNG-style detach group)
  - `cdx:etzhayyim:vehicle:mass_kg`
  - `cdx:etzhayyim:vehicle:material`
  - `cdx:etzhayyim:vehicle:parent` (`bom-ref` of parent in assembly tree)

This keeps every SBOM clause in the public CycloneDX schema — `sbom.etzhayyim.com` continues to validate cleanly.

### Auto-emitted JBeam topology (Phase 1 baseline)

Each `VehiclePart` is sampled as:
- 8 nodes at AABB corners (mass = `part.mass / 8`, group from `kind`)
- 12 edge beams (cube edges) + 4 face-diagonal beams (X-bracing) per part
- inter-part beams emitted from declared `Hardpoint` pairs (bolt / weld / hinge / latch → beam type bounded / normal / bounded / bounded with break threshold from material)

This yields ~30 parts × ~12 nodes ≈ 360 nodes / ~580 beams for the PoC sedan — already 4× the current hand-written 86 / 220, and Phase 2 enriches by surface-sampling visible faces.

### Provenance / SBOM is mandatory, not optional

Every `VehiclePart` MUST declare `source { uri, sha256, license }`. The crate refuses to emit JBeam without it. This is the same posture `sbom.etzhayyim.com` already enforces on software components — physical parts get the same governance.

## Consequences

Positive:
- One source of truth (`VehicleAssembly`) drives both physics and SBOM — no drift.
- Existing `sbom.etzhayyim.com` CVE / recall / supplier-quality machinery applies immediately to physical parts (zero new infrastructure).
- License clearance is forced at ingest (`source.license` required).
- Per-part mass / inertia from CAD volume × material density beats hand-tuned numbers.
- New Rust crate is additive — no `kami-vehicle` / `kami-cad` / `kami-app-car-sim` API change.

Negative:
- AABB-corner sampling is coarse — visible body panels need surface sampling (Phase 2).
- CycloneDX 1.5 has no first-class "physical part" type; we use `device`, which works but is loose. A future bump to CDX 1.6+ doesn't change the API.
- STEP / IGES ingestion is not in PoC (uses OpenSCAD via `kami-scad`); STEP/glTF lands in Phase 1.1.

Neutral:
- 16-week roadmap unchanged; this ADR covers Phase 0 + the foundation of Phase 1.

## Migration

Tracked in `deps.toml` under `[[migrations]] drive-cad-import-pipeline-2026-05`.

## References

- `60-apps/etzhayyim-project-sbom/CLAUDE.md` — existing SBOM platform (CDX 1.5 default + CVE pipeline)
- `40-engine/kami-engine/kami-cad/src/lib.rs` — BREP + assembly + `get_bom()`
- `40-engine/kami-engine/kami-vehicle/src/jbeam.rs` — JBeam consumer
- `40-engine/kami-engine/kami-vehicle/README.md` — current 86 / 220 baseline
- BeamNG JBeam reference: <https://documentation.beamng.com/modding/jbeam/>
- CycloneDX 1.5 spec: <https://cyclonedx.org/docs/1.5/json/>
