# ADR-2605250715: Tatekata (建方) — Construction Tier-B Actor R0 Scaffold

**Date**: 2026-05-25
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Parent = ADR-2605201400 (kuni-umi Phase S1–S3 infrastructure)

## Context

Per ADR-2605201400 §1 (kuni-umi actor topology), Phase 3 "multi-utility integrated" requires coordinating construction site logistics, material flow, and multi-skilled robotics (Giemon + Otete + future Hitogata humanoid). Current implementation places `construction_orchestration` Pregel cell on `kuni-umi` as a sub-phase driver, but **construction as an independent domain (architecture standards, safety governance, BIM integration, permit compliance) has no top-level actor**.

This ADR uses reserved ID **ADR-2605250715** (not 2605250700, which is assigned to Oka × MMSheaf).

Similarly, `yakushi` (pharmaceutical, ADR-2605250500) and `wadachi` (autonomous mobility, ADR-2605242000) are Tier-B actors with dedicated R0 scaffolds, 14 constitutional gates, and 10 non-goals. **Construction engineering warrants equivalent standing.**

## Proposal

Launch **`tatekata` (建方 — construction method / general construction practice)** as a Tier-B religious-corp actor, mirroring `yakushi` Wave 1 + `wadachi` R0 patterns:

- **Actor DID**: `did:web:etzhayyim.com:tatekata`
- **Namespace**: `com.etzhayyim.tatekata.*`
- **R0 scope**: Infrastructure construction (≤2 story, ≤5000m², civil + MEP) — excludes housing (residential R+X), high-rise (>12 stories), nuclear, hazmat manufacture
- **R0 robotics**: kuni-umi Giemon (crawler + arm), Otete (chem-resist arm), Hitogata (future class-A clean), Mimi (metrology)
- **14 gates + 10 non-goals** declared before capability lands
- **5 Pregel cells** (foundation, structure, MEP, finishing, commissioning) — all import-time RuntimeError in R0

## Rationale

1. **Domain separation**: Construction domain knowledge (BPMN site workflows, material routing, Japanese Ministry of Land/Infrastructure/Transport permit taxonomy, ISO 19650 BIM metadata) belongs in a dedicated actor, not scattered across kuni-umi sub-phases.
2. **Multi-phase roadmap**: R0 (scaffold only) → R1 (PoC benchtop site survey) → R2 (SME + prefab assembly on confined site ≤100m²) → R3 (community scale + 60-day public review).
3. **Constitutional alignment**: §2(a) (no weapons) clearance trivial; §2(e) (anti-gatekeeping) applies to **open-source construction documentation** (energy codes, permit PDFs). §2(g) (no rare-earth constraint) applies to MEP robotics (Otete chem-resist arm uses commodity steels, no RE).
4. **Witness quorum**: Per ADR-2605191524 (swarm broadcast), site progress records require ≥2 robot Ed25519 signatures + ≥1 human engineer attestation.

## Design

### Actor Manifest

```
20-actors/tatekata/
├── README.md                     # Overview + R0 scope boundary
├── CLAUDE.md                     # Actor-local instructions
├── manifest.jsonld               # DID + cell catalog
└── cells/                        # 5 cell scaffolds (import-time RuntimeError)
    ├── foundation_excavation/
    ├── structural_assembly/
    ├── mep_installation/
    ├── finishing_handoff/
    └── commissioning/
```

### Pregel Cells (5, all import-time RuntimeError R0)

| Cell | Purpose | Murakumo node | Input | Output |
|---|---|---|---|---|
| `foundation_excavation` | Site survey → soil auth + excavation plan | naphtali (earth-moving) | siteId, boM | foundationAuthorized |
| `structural_assembly` | Giemon + Otete + temporary shoring plan | joseph (structural) | foundationAuthorized | structuralAuthRecord |
| `mep_installation` | MEP ductwork/conduit/pipe + Otete arm | zebulun (utilities) | structuralAuthRecord | mepSignoffRecord |
| `finishing_handoff` | Drywall/paint/trim + Hitogata (future) | simeon (finishing) | mepSignoffRecord | finishingRecord |
| `commissioning` | Final testing + defect log + project closeout | levi (verification) | finishingRecord | projectClosure |

### Lexicons (4 new, all deferred to R1+)

```
com.etzhayyim.tatekata.{
  siteAttestation,         # Site survey findings (soil, utilities, hazards)
  materialAttestaton,      # Material delivery + QA
  constructionProgressRecord,  # Phase transition + photo/video CID
  safetyIncidentReport     # On-site incident logging (falls, electrical, etc)
}
```

### Constitutional Gates (G1–G14, IMMUTABLE per R0)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | All robotics firmware **open-source** (WASM or Rust crates, Apache 2.0) | ADR-2605192100 §1.12 (Transparent Force) |
| **G2** | Site photos + depth maps IPFS-pinned **before** human equipment entry | Audit trail + immutable BoM |
| **G3** | ≥2 distinct robot signers per progress record (Ed25519, DID-bound) | ADR-2605191524 witness quorum |
| **G4** | All permit PDFs (土地利用計画, 建築許可, 労働安全) **English + JA bilingual** approved scans | Anti-gatekeeping (§2(e)) |
| **G5** | Material sourcing **Charter Rider §2(g) compliant** (no conflict minerals, no rare-earth for standard construction) | Ethical supply chain |
| **G6** | Giemon arm trajectory **deterministic + re-playable** (joint angles logged @ 10 Hz, WASM state-machine sealed) | Safety + audit |
| **G7** | No on-site chemical processes (spray foam, epoxy mixing, solvent curing) in R0 (deferred to R2) | Hazmat gate for later phase |
| **G8** | Site DEM + CAD `.dwg` sourced from **vendor-free** tools (Open CASCADE, FreeCAD, OpenSCAD) | Anti-proprietary design lock |
| **G9** | Murakumo mesh placement **declared 30 days prior**, public feedback period | Neighborhood transparency (ADR-2605242000 wadachi precedent) |
| **G10** | All subcontractor drones + robots **pre-registered** in `TatekataRoboticsRegistry` + background-checked operator DID | Personnel + equipment safety |
| **G11** | Accident rate **≤ sector baseline × 0.5** (per OSHA data for comparable scope). Waive to R1+ via Council vote | Performance bar |
| **G12** | Energy consumption **≤ 150 kWh per 100m³ excavation** (giemon + lighting). Exceed = immediate halt + review | Sustainability cap |
| **G13** | Completion schedule **public calendar** on IPFS — reschedule >14d = trigger community comment period | Accountability |
| **G14** | Final project metadata (`projectClosure` record) **includes material waste log** (% reused / recycled / landfill). Chart Rider §2(h) assessment | Circular economy |

### Non-Goals (N1–N10, EXCLUDE from R0–R3)

| Non-Goal | Scope | Deferral |
|---|---|---|
| **N1** | High-rise (>12 stories) construction — complexity + structural dynamics > scope | ADR post-R3 (Level-4 complexity gate) |
| **N2** | Residential housing (R occupancy, Article 7 Japanese Building Code) — implies `MiyadaikuHousingActor` separate gate | ADR separate |
| **N3** | Nuclear site prep / hazmat decontamination — requires radiological training + sealed facility | Never (constitutional carve-out) |
| **N4** | Chemical manufacturing plant construction (batch reactors, distillation columns) — overlap with kuni-umi-S6 chemistry | Never (carve-out to kuni-umi) |
| **N5** | Tunnel / deep underground (>30m depth) — requires different robotics class (boring machines) | ADR post-R3 |
| **N6** | Bridge main-span (>500m unsupported) — requires cable-stayed / suspension specialist | ADR post-R3 |
| **N7** | Seismic retrofitting of historical buildings — requires preservation specialist actor | ADR separate (cultural heritage gate) |
| **N8** | Deep-sea platform construction — requires marine robotics (Funamori class) | Never (scope = onshore / near-shore ≤100m depth) |
| **N9** | Architectural design (aesthetics, style, master planning) — design ≠ construction | Never (design = external input, tatekata = execution only) |
| **N10** | Cost estimation / budgeting (CNY/USD/JPY forecasting) — finance domain (capital:*) | Never (tatekata = physical execution only) |

## Roadmap (R0 → R3)

| Phase | Scope | Murakumo fleet | Trigger |
|---|---|---|---|
| **R0** (this ADR) | Scaffold only. No live construction. 5 cell import-time RuntimeError. | No deployment | Immediate |
| **R1** | Benchtop site survey PoC (0.5 m × 0.5 m test excavation, depth ≤1m). BoM survey only. Giemon arm trajectory log + replay. | naphtali node (earth-moving) | ADR-2605250715 (R1 activation, Council Lv6+ vote) + SME (civil engineer) onboarded |
| **R2** | Pilot on confined site (≤100m², ≤2 stories, prefab assembly). Giemon + Otete + manual subcontractors. Incident <baseline. Material waste logged. | naphtali + joseph + zebulun | ADR-2605250730 (R2 expansion) + site permit + 3-week public comment + Annex-1 facility parallel (pharma parity) |
| **R3** | Community scale (≤5000m², multi-building campus, open-source permits). Hitogata humanoid integration (future). 60-day public review. | Full 10-node fleet | ADR-2605250745 (R3 governance) + Council multi-domain (silicon + pharma + tatekata) vote |

## Implementation

### Files to commit

1. **`90-docs/adr/2605250715-tatekata-construction-tier-b-actor-r0.md`** ← this file
2. **`20-actors/tatekata/README.md`** — Scope + R0 R1 R2 R3 phase gates
3. **`20-actors/tatekata/CLAUDE.md`** — Local instructions (manifest loading, cell architecture)
4. **`20-actors/tatekata/manifest.jsonld`** — `did:web:etzhayyim.com:tatekata`, 5 cell URIs, 4 lexicon namespaces
5. **`20-actors/tatekata/cells/{foundation_excavation, structural_assembly, mep_installation, finishing_handoff, commissioning}/`** — 5 × (\_\_init\_\_.py, cell.py, README.md) with RuntimeError scaffolds
6. **`00-contracts/lexicons/com/etzhayyim/tatekata/{siteAttestation, materialAttestation, constructionProgressRecord, safetyIncidentReport}.json`** — 4 lexicons
7. **`deps.toml`** — Add `[[migrations]]` entry for tatekata + ADR ID + 5 cell module entries
8. **`90-docs/adr/README.md`** — Register ADR-2605250715 + phase ADRs (2605250730, 2605250745, 2605250760 reserved)
9. **`CLAUDE.md` Status table** — Row 43 (tatekata Wave R0) between yakushi Wave 1c and next row

### Design Decision: `tatekata` (vs `miyadaiku` or `kensetsu`)

- **`tatekata` (建方)** = general construction method / practice (used in modern construction contexts, less regional bias)
- `miyadaiku` (宮大工) = shrine-specific carpentry (too narrow for Tier-B scope)
- `kensetsu` (建設) = construction (generic, but vague; used in ministry names)

**Choice: `tatekata`** for modern generality + echo of traditional craft.

## Acceptance Criteria

- [ ] ADR file merged
- [ ] Actor scaffold committed with 5 Pregel cells (all RuntimeError)
- [ ] manifest.jsonld registered; `did:web:etzhayyim.com:tatekata` resolvable
- [ ] 4 lexicons created (stub only, no versioning yet)
- [ ] `deps.toml` synchronized
- [ ] CLAUDE.md Status row added (row 43)
- [ ] `/90-docs/adr/README.md` index updated
- [ ] R1 ADR (2605250730) authored as placeholder → scheduled for Council review post-R0

## Related

- ADR-2605201400: kuni-umi Phase S1–S3 (parent)
- ADR-2605191524: Swarm broadcast witness quorum (gate G3)
- ADR-2605250500: yakushi pharmaceutical (Wave 1 pattern precedent)
- ADR-2605242000: wadachi autonomous mobility R0 (R0 scaffold + gates pattern precedent)
- ADR-2605250730: tatekata Wave R1 (placeholder, reserved)
- ADR-2605250745: tatekata Wave R2 (placeholder, reserved)
- ADR-2605250800: tatekata Wave R3 (placeholder, reserved)

---

**Co-Authored-By**: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
