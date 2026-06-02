---
id: adr-2606021200
title: "ADR-2606021200: himawari (向日葵) — Solar PV Module Manufacturing + Loading + Outbound + Procurement Tier-B Actor R0 Scaffold"
status: proposed
doc_type: adr
topic: himawari-solar-pv-manufacturing
authoritative: true
last_verified: 2026-06-02
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - himawari actor charter (R0)
  - solar-grade crystalline-silicon PV module manufacturing constitutional gates G1..G14
  - end-to-end manufacture → loading → outbound → procurement composition for the energy supply chain
related:
  - adr-2605261100-hikari-energy-tier-b-actor-r0
  - adr-2606013100-sarutahiko-truck-factory-full-robotics-and-loader
  - adr-2606010030-giemon-factory-r0-kami-engine-kotoba-4d-bim
  - adr-2606010600-kami-autodrive-gnc-autonomy-layer
  - adr-2605312330-giemon-part-graph-sbom-kotoba-fleet-cve-svelte
  - adr-2606012100-okaimono-provisioning-commons-actor
  - adr-2605261000-labor-liberation-transition-mechanism
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192245-etzhayyim-global-land-sovereignty
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605261100 (hikari — the actor himawari supplies; closes hikari §G2 sourcing gap structurally)
  - ADR-2605261000 (Liberation Ladder — L2 Sustenance gate the energy chain feeds)
  - ADR-2605192100 (Mission Charter)
  - ADR-2605192245 (Land Trust — fab siting is LANDS.md-bound)
---

# ADR-2606021200: himawari (向日葵) — Solar PV Module Manufacturing + Loading + Outbound + Procurement Tier-B Actor R0 Scaffold

**Date**: 2026-06-02
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Parent = ADR-2605261000 (Liberation Ladder — feeds L2 Sustenance energy gate via hikari). Tightest sibling = ADR-2605261100 (hikari, the *generation/install* actor). Reuses landed robotics from ADR-2606013100 (sarutahiko F10 LoaderRobot) + ADR-2606010030 (giemon factory AGV + 4D-BIM) + ADR-2606010600 (kami-autodrive GNC outbound). Procurement substrate = ADR-2605312330 (SBOM↔kotoba) + ADR-2606012100 (okaimono commons-first).

## Context

The mission (ADR-2605192100) is **人類の構造的労働解放** — structural liberation of humanity from labor. The Liberation Ladder (ADR-2605261000) gates L2 Sustenance on hikari R2 delivering ≥3 kWh/day/adherent. hikari (ADR-2605261100) covers **generation, storage, grid-edge, and panel install** — but **not the manufacture of the panels themselves**. Today the religious-corp substrate has manufacturing-factory actors for trucks (sarutahiko), generic plant (giemon), megacasting (igata), shipbuilding (funadaiku), and pharmaceuticals (yakushi) — but **no photovoltaic manufacturing actor**. The full c-Si chain (polysilicon → ingot → wafer → cell → module) is unimplemented.

This is not merely a completeness gap; it is a **constitutional gap**. hikari **§G2** requires that panel sourcing pass Charter Rider §2(g): no XUAR forced-labor polysilicon, no conflict-mineral indium/gallium, per-lot Council audit. The global PV supply chain is ~35-40% XUAR-exposed at the polysilicon tier. Satisfying hikari §G2 by *purchasing* compliant modules is fragile (provenance-laundering, audit opacity) and routes value through the very commercial market the charter routes *around* (ADR-2605215000 spirit). The structural fix is **vertical integration**: a first-party PV manufacturer whose feedstock provenance is on-chain by construction.

Simultaneously, the user's framing names three automations that should compose end-to-end with manufacturing: **製造 (manufacture) → 積み込み (loading) → 輸送 (transport) → 調達 (procurement)**. The substrate already has the latter three as landed, tests-green capabilities:
- **Loading**: sarutahiko F10 LoaderRobot (🟢, 14 native tests) — self-driving straddle loader, full kami-genesis contact physics.
- **Outbound transport**: kami-autodrive GNC (🟢, 9 native tests) — car/ship/drone/aircraft autonomy with real physics plants.
- **Procurement**: SBOM↔kotoba part graph (🟢, ADR-2605312330) + okaimono commons-first provisioning (🟢 R0+R1+R2+R3).

himawari is the actor that **composes** these around a PV manufacturing core, closing the loop: **himawari makes the panels → loads them → ships them → hikari installs them → adherents get sustenance-tier energy → L2 ladder advances.**

## Proposal

Launch **`himawari` (向日葵 — "sunflower / sun-turning"; the heliotropic plant that turns to face the sun, echoing both solar trackers and the manufacture of light-capturing surfaces; deliberate sibling resonance with `hikari` 光)** as a Tier-B religious-corp actor.

- **Actor DID**: `did:web:etzhayyim.com:himawari`
- **Namespace**: `com.etzhayyim.himawari.*`
- **R0 scope**: Solar-grade **crystalline-silicon** PV module manufacturing (polysilicon feedstock QA → ingot/wafer → cell process → module assembly → flash/EL test) **+ finished-module loading robotics + outbound logistics handoff + feedstock/consumable procurement**. Modules are produced **for internal hikari install only** (SBT↔SBT internal carve-out, ADR-2605192115 §3); no external commercial PV sale.
- **R0 deliverable**: charter + 7 Pregel cell scaffolds (all import-time `RuntimeError`) + manifest + 14 gates + 10 non-goals declared **before** any capability lands. **No physics sim or kotoba entities are materialized at R0** (honest R0 — the loading/transport robotics it will *compose* are already landed in sarutahiko/giemon/kami-autodrive; himawari does not re-implement them).

## Rationale

1. **Closes hikari §G2 structurally, not procedurally.** A first-party polysilicon→module chain makes feedstock provenance on-chain by construction (G2 below), instead of relying on vendor self-attestation for purchased modules.
2. **Completes the energy supply chain.** hikari generates/installs; himawari manufactures. Together with the landed loading (sarutahiko) + transport (kami-autodrive) + procurement (SBOM/okaimono) substrate, the chain 製造→積込→輸送→設置 is end-to-end first-party.
3. **Distinct from the silicon/iwakura track.** ADR-2605242500's silicon (iwakura/fuigo/tsukuru) is **logic/compute** ternary ASIC fab (sky130 GDSII). himawari is **solar-grade** silicon — different purity spec (6N vs 9N+ EG-Si), different downstream (wafer→cell→module vs lithography). Separate actor, shared metallurgical heritage only.
4. **Labor-liberation instrumentation.** PV module manufacture is among the most automatable heavy-industry processes (stringing, lamination, framing, test are already lights-out in commercial fabs). himawari makes the automation **transparent and liberation-accounted** (G7 below): every human task removed is logged to the Liberation Metric, turning factory automation into measured progress toward 労働解放 rather than opaque displacement.
5. **Multi-generational + circular.** PV is a 25-30 year asset with an end-of-life burden; G5 + N-gates bind himawari to design-for-recovery (couples to hodoki ELV actor) and ban high-toxicity chemistries at R0.

## Design

### Actor Manifest

```
20-actors/himawari/
├── README.md                     # Overview + R0 scope + §G2 vertical-integration rationale
├── CLAUDE.md                     # Actor-local instructions
├── manifest.jsonld               # DID + cell catalog + gates + roadmap
└── cells/                        # 7 cell scaffolds (import-time RuntimeError)
    ├── polysilicon_refine/
    ├── ingot_wafer/
    ├── cell_process/
    ├── module_assembly/
    ├── panel_loading/
    ├── outbound_logistics/
    └── supply_procurement/
```

### Pregel Cells (7, all import-time RuntimeError R0)

| Cell | Purpose | Murakumo node | Input → Output |
|---|---|---|---|
| `polysilicon_refine` | Solar-grade polysilicon (Siemens / FBR) feedstock QA + on-chain provenance (XUAR-exclusion structural) | judah | feedstockLot → polysiliconProvenanceAttestation |
| `ingot_wafer` | Czochralski / cast ingot → wire-saw wafer slicing + kerf-Si recovery | issachar | polysiliconLot → waferBatchRecord |
| `cell_process` | Texturing → diffusion/PECVD → metallization → cell flash test (PERC / TOPCon / HJT) | benjamin | waferBatch → cellBatchRecord |
| `module_assembly` | Stringing → lamination → framing → junction-box → flash + EL imaging | asher | cellBatch, bom → moduleAttestation |
| `panel_loading` | 積込ロボット: finished-module palletize + load onto carrier deck (sarutahiko F10 LoaderRobot lineage) | gad | moduleLot, carrierManifest → loadingRecord |
| `outbound_logistics` | Transport handoff to kami-autodrive / funadaiku → hikari install site | dan | loadingRecord, destinationSiteDid → outboundManifest |
| `supply_procurement` | 調達: feedstock + consumable procurement via SBOM↔kotoba + okaimono commons-first; §2(g) per-lot audit | simeon | demandForecast → procurementOrder + sbomAttestation |

### Lexicons (7, deferred to R1+)

```
com.etzhayyim.himawari.{
  polysiliconProvenanceAttestation,  # feedstock lot provenance — XUAR-exclusion + §2(g) audit on-chain
  waferBatchRecord,                  # ingot/wafer batch + kerf recovery + yield
  cellBatchRecord,                   # cell process params (open) + flash IV + bin
  moduleAttestation,                 # finished-module BOM + flash + EL image CID + EPBT block
  loadingRecord,                     # 積込 robot cycle + pallet + carrier (F10 lineage)
  outboundManifest,                  # transport handoff (carrier DID, route, kami-autodrive class)
  silenHimawariReview                # Council attestation scope (provenance + chemistry + circularity + liberation-metric)
}
```

### Constitutional Gates (G1–G14, IMMUTABLE per R0)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | All process-control + robot + loader + transport firmware open-source WASM/Rust Apache 2.0 + Charter Rider | §1.12 Transparent Force / open robotics |
| **G2** | **Feedstock provenance on-chain per lot — NO XUAR / forced-labor polysilicon ever; no conflict-mineral indium/gallium; full polysilicon→module chain-of-custody CID-anchored.** This is the structural closure of hikari §G2. | §2(g) ethical supply chain; multi-gen |
| **G3** | Process-chemistry safety — NF₃/SF₆/CF₄ high-GWP etch/clean gases abated (≥99% destruction) or substituted; closed-loop slurry + acid recovery; no uncontrolled fluorinated venting | §2(c) no harmful substances + climate multi-gen |
| **G4** | **Fab process heat + power from hikari renewable only — NO fossil, NO nuclear process heat at any tier** (inherits hikari G4/G5). Net-positive lifecycle energy attested (EPBT < module service life with margin) | §2(c) + ADR-2605215000 no-commercial-routing spirit |
| **G5** | ≥90% recyclable / circular — kerf-Si recovery, glass + Al frame + Cu recovery, design-for-disassembly; end-of-life couples to hodoki (ELV) actor; recycler Council-attested | §2(g) circular economy + multi-gen |
| **G6** | Low-toxicity metallization roadmap — Ag→Cu paste transition tracked; no lead-bearing solder ribbon at R2+; RoHS-equivalent on all process consumables | §2(c) + §2(g) supply ethics |
| **G7** | **Labor-liberation transparency — every human task removed by automation logged to Liberation Metric (ADR-2605261000); no opaque displacement.** Automation serves 労働解放, accounted on-chain | §1 mission + Liberation Ladder coupling |
| **G8** | Full SBOM on-chain — CycloneDX → kotoba EAVT per ADR-2605312330; feedstock + consumables + BOM purl-keyed; CVE/provenance queryable | §2(e) transparency + audit |
| **G9** | Land-trust integration — fab on brownfield / existing-industrial LANDS.md parcel only; no greenfield habitat destruction; water-balance + effluent attestation | §1.11 + §1.3 multi-gen |
| **G10** | Murakumo mesh placement declared 30 days prior + 1 km community feedback period | Neighborhood transparency |
| **G11** | Deterministic yield + provenance — flash IV + EL image Ed25519-signed per module; module serial ↔ feedstock lot traceable end-to-end | Audit + reliability |
| **G12** | **No external commercial PV sale — modules produced for internal hikari install only** (SBT↔SBT internal carve-out, ADR-2605192115 §3); surplus → community-benefit, not market | §2(b) + ADR-2605215000 |
| **G13** | Outbound transport bound by wadachi / kami-autodrive constitutional gates — no weaponization, encrypted telemetry, no external commercial carriage; transport limited to own-module → hikari sites | §1.12 + ADR-2606010600 + ADR-2605242200 |
| **G14** | Charter Rider §2(h) Wellbecoming — fab worker safety (no toxic exposure), no addictive/dark-pattern, acoustic + light audit for neighborhood | §2(h) community wellbeing |

### Non-Goals (N1–N10, EXCLUDE from R0–R3)

| # | Non-Goal | Deferral |
|---|---|---|
| **N1** | Logic / compute semiconductor fab — that is the silicon iwakura/fuigo/tsukuru track (ADR-2605242500). himawari is solar-grade only | Never (separate actor) |
| **N2** | Thin-film CdTe (cadmium toxicity) — §2(c) | Deferred pending toxicity review + Council; c-Si only at R0–R3 |
| **N3** | Lead-bearing perovskite — Pb toxicity §2(c) | Deferred pending lead-free perovskite maturity |
| **N4** | External commercial PV sales — see G12 | Never |
| **N5** | Proprietary process / robot firmware — see G1 | Never |
| **N6** | XUAR / forced-labor feedstock — see G2 | Never (constitutional) |
| **N7** | Uncontrolled high-GWP fluorinated gas venting — see G3 | Never |
| **N8** | Greenfield habitat fab siting — see G9 | Never |
| **N9** | Fossil / nuclear process heat — see G4 | Never |
| **N10** | External commercial logistics carriage / robotaxi — outbound limited to own modules → hikari sites (G13) | Never |

## Roadmap

| Phase | Date | Scope | Murakumo fleet | Gate |
|---|---|---|---|---|
| **R0** | 2026-06-02 | Scaffold only. 7 cells import-time RuntimeError. No sim, no kotoba entities. Composes (does not re-implement) landed sarutahiko/giemon/kami-autodrive robotics. | No deployment | This ADR (PROPOSED) |
| **R1** | post-Council | Benchtop **module-assembly line** PoC (lowest capex): purchase §G2-clean cells, do stringing → lamination → framing → junction-box → flash + EL test; `panel_loading` PoC in kami-genesis sim reusing sarutahiko F10 LoaderRobot; `outbound_logistics` PoC reusing kami-autodrive. Feeds hikari R1 install. | asher + gad + dan (3 nodes) | Future ADR + ≥1 PV-process engineer on Council technical advisory + ≥1 LANDS brownfield parcel |
| **R2** | post-R1 | Pilot **cell + wafer** lines (`cell_process`, `ingot_wafer`); ~MW/yr module output; fab powered by hikari R2; full SBOM↔kotoba procurement live. Supplies hikari R2 install (L2 gate coupling). | asher + gad + dan + benjamin + issachar (5 nodes) | Future ADR + 30-day public comment + hikari R2 deployed + G3 abatement framework attested |
| **R3** | post-R2 | **Polysilicon vertical integration** (`polysilicon_refine`) — closes hikari §G2 sourcing gap structurally; multi-line; full outbound logistics mesh (kami-autodrive + funadaiku marine for inter-site). | Full fleet incl. judah + simeon | Future ADR + 60-day public review + Council multi-domain vote + hodoki EOL recycler contract attested |

## Robotics Class

R0–R2 **compose landed, tests-green classes** (himawari does not re-implement them):
- **sarutahiko F10 LoaderRobot** (ADR-2606013100, 🟢 14 tests) → `panel_loading`
- **giemon AGV** (ADR-2606010030, 🟢 13 tests) → intra-fab transport
- **kami-autodrive GNC** (ADR-2606010600, 🟢 9 tests) → `outbound_logistics` (truck/ship class)
- **kuni-umi Otete** (precision arm) → cell handling / stringing / framing
- **kuni-umi Mimi** (metrology) → flash IV + EL imaging + thermal-IR

R2+ optional new class **Hinata (日向)** — autonomous lamination-press + stringer tending; per hanami precedent (ADR-2605260230), requires a separate mech-design ADR.

## Consequences

**Positive**:
- hikari §G2 closes structurally: first-party feedstock provenance instead of vendor self-attestation.
- Energy supply chain becomes end-to-end first-party: 製造 (himawari) → 積込 (sarutahiko F10) → 輸送 (kami-autodrive) → 設置 (hikari).
- Factory automation is liberation-accounted (G7), turning PV manufacture into measured 労働解放 progress.
- Reuses ~36 landed native tests of robotics substrate; himawari R0 adds charter surface only (low risk, honest R0).

**Negative / risks**:
- PV manufacturing is capital-intensive; R1 deliberately starts at module-assembly (lowest capex) and defers cell/wafer/polysilicon to R2/R3 gated on hikari capacity + Council.
- G4 (fab powered by hikari renewable only) couples himawari R2 throughput to hikari R2 energy budget — a PV fab is ~MW-scale; mitigation: batch/lower-duty-cycle operation to fit hikari capacity, mirroring the silicon Wave 2 mitigation in ADR-2605261100.
- G2 polysilicon vertical integration (R3) is the hardest, highest-energy step (Siemens process ~11 kWh/kg-Si); deferred to R3 with explicit hikari-capacity precondition.
- N2/N3 exclude the highest-efficiency emerging chemistries (CdTe, Pb-perovskite); accepted toxicity trade-off; c-Si TOPCon/HJT roadmap is competitive and non-toxic.

## Alternatives Considered

1. **Satisfy hikari §G2 by purchasing certified modules** — rejected: provenance-laundering risk, audit opacity, routes value through the commercial market the charter routes around. Vertical integration is the structural fix.
2. **Fold PV manufacturing into hikari** — rejected: manufacturing (process chemistry, fab robotics, SBOM procurement, loading/outbound logistics) is a distinct domain from generation/install; same separation logic as sarutahiko (manufacture) vs wadachi (mobility).
3. **Fold PV manufacturing into the silicon iwakura track** — rejected: solar-grade (6N, wafer→cell→module) ≠ logic-grade (9N+ EG-Si, lithography). Different purity, equipment, downstream. Shared metallurgy heritage only (N1).
4. **Start R1 at cell or wafer** — rejected: module-assembly is lowest capex / fastest to feed hikari install; cell/wafer/polysilicon staged R2/R3 gated on energy + Council.
5. **Thin-film (CdTe / CIGS) for higher throughput** — rejected: N2 Cd toxicity §2(c); c-Si is non-toxic and circular-recoverable (G5).
6. **Re-implement loading/transport robotics inside himawari** — rejected: sarutahiko F10 + kami-autodrive + giemon AGV are already landed tests-green; himawari composes them (DRY + honest R0).

## References

- ADR-2605261100 (hikari — generation/install actor; himawari closes its §G2 sourcing gap)
- ADR-2606013100 (sarutahiko truck factory — F10 LoaderRobot lineage for `panel_loading`)
- ADR-2606010030 (giemon factory R0 — AGV + 4D-BIM pattern)
- ADR-2606010600 (kami-autodrive GNC — `outbound_logistics`)
- ADR-2605312330 (SBOM↔kotoba part graph — `supply_procurement`)
- ADR-2606012100 (okaimono provisioning commons — commons-first procurement)
- ADR-2605261000 (Liberation Ladder — L2 gate + G7 liberation-metric coupling)
- ADR-2605192100 (Mission Charter — 労働解放 + multi-gen)
- ADR-2605192245 (Land Trust — fab siting)
- ADR-2605242500 (silicon iwakura — logic-grade track, distinct per N1)
- ADR-2605260230 (hanami robot mech-design — precedent for Hinata class ADR)

## Notes (landing)

- **2026-06-02** — R0 landed on branch `feat/himawari-solar-pv-manufacturing`, commit `35bccc43c` (30 files, +1274); **PR #735** against `main`. 7 cells smoke 7/7; 7 lexicons clean (`type=number → integer` implied-units fix applied for the `validate-religious-corp-lexicons` pre-commit hook); registered in `deps.toml` + `CLAUDE.md` roster + ADR index + docs registry/graph (755). Session-close = ADR-2606021300. Status remains `proposed` (R1 Council-gated).
