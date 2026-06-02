# himawari (向日葵) — Solar PV Module Manufacturing Tier-B Actor

**DID**: `did:web:etzhayyim.com:himawari`
**Namespace**: `app.etzhayyim.himawari.*`
**ADR**: ADR-2606021200 (R0 scaffold)
**Status**: R0 scaffold (2026-06-02) — all cells import-time RuntimeError
**Parent ADR**: ADR-2605261000 (Liberation Ladder — feeds L2 Sustenance energy gate via hikari)
**Tightest sibling**: hikari (ADR-2605261100 — generation/install actor)

## Overview

Solar-grade **crystalline-silicon** PV module manufacturing actor — polysilicon feedstock QA → ingot/wafer → cell process → module assembly → flash/EL test — **plus** finished-module loading robotics, outbound logistics handoff, and feedstock/consumable procurement.

himawari makes the panels that **hikari** installs. Together with the already-landed loading (sarutahiko F10 LoaderRobot), transport (kami-autodrive GNC), and procurement (SBOM↔kotoba + okaimono) substrate, the energy supply chain is end-to-end first-party:

```
製造 (himawari) → 積込 (sarutahiko F10) → 輸送 (kami-autodrive) → 設置 (hikari) → L2 Sustenance energy
```

## Why this actor exists (the constitutional gap it closes)

hikari **§G2** forbids XUAR forced-labor polysilicon and conflict minerals, with per-lot Council audit. Satisfying that by *purchasing* certified modules is fragile (provenance-laundering, audit opacity) and routes value through the commercial market the charter routes around. himawari closes §G2 **structurally** via first-party, on-chain feedstock provenance (G2 below) — vertical integration, not vendor self-attestation.

It also fills the only manufacturing gap left in the energy chain: the substrate already has factory actors for trucks (sarutahiko), generic plant (giemon), megacasting (igata), shipbuilding (funadaiku), and pharma (yakushi) — but **no PV manufacturing actor** until now.

## Distinct from the silicon (iwakura) track

`silicon` (iwakura/fuigo/tsukuru, ADR-2605242500) is **logic/compute** ternary-ASIC fab (sky130 GDSII). himawari is **solar-grade** silicon — different purity (6N vs 9N+ EG-Si), different downstream (wafer→cell→module vs lithography). Shared metallurgy heritage only (N1).

## Robotics Classes (R0–R2 compose landed, tests-green classes)

| Class | Role | Lineage | Status |
|---|---|---|---|
| sarutahiko **F10 LoaderRobot** | 積込 — `panel_loading` palletize + carrier load | ADR-2606013100 | 🟢 LANDED (14 tests) |
| giemon **AGV** | intra-fab transport | ADR-2606010030 | 🟢 LANDED (13 tests) |
| kami-autodrive **GNC** | `outbound_logistics` (truck/ship) | ADR-2606010600 | 🟢 LANDED (9 tests) |
| kuni-umi **Otete** | cell handling / stringing / framing | kuni-umi | inherited |
| kuni-umi **Mimi** | flash IV + EL imaging + thermal-IR | kuni-umi | inherited |
| **Hinata (日向)** (R2+) | autonomous lamination-press + stringer tending | new class | separate mech-design ADR (hanami precedent) |

himawari **composes** these; it does not re-implement them (DRY + honest R0).

## Pregel Cells (7, R0)

| Cell | Murakumo node | Phase | Input → Output |
|---|---|---|---|
| `polysilicon_refine` | judah | solar-grade polysilicon QA + on-chain provenance | feedstockLot → polysiliconProvenanceAttestation |
| `ingot_wafer` | issachar | Czochralski/cast ingot → wafer slicing + kerf recovery | polysiliconLot → waferBatchRecord |
| `cell_process` | benjamin | texture → diffusion/PECVD → metallization → cell flash test | waferBatch → cellBatchRecord |
| `module_assembly` | asher | stringing → lamination → framing → J-box → flash + EL | cellBatch, bom → moduleAttestation |
| `panel_loading` | gad | 積込ロボット palletize + carrier load (F10 lineage) | moduleLot, carrierManifest → loadingRecord |
| `outbound_logistics` | dan | transport handoff to kami-autodrive/funadaiku → hikari site | loadingRecord, destinationSiteDid → outboundManifest |
| `supply_procurement` | simeon | 調達 — SBOM↔kotoba + okaimono commons-first; §2(g) per-lot audit | demandForecast → procurementOrder + sbomAttestation |

## Constitutional Gates (G1–G14)

See ADR-2606021200. **IMMUTABLE** per R0. Structural anchors:

- **G2**: feedstock provenance on-chain per lot — **no XUAR/forced-labor polysilicon ever** (closes hikari §G2)
- **G4**: fab process heat + power from **hikari renewable only** — no fossil/nuclear (inherits hikari G4/G5); net-positive lifecycle energy
- **G7**: **labor-liberation transparency** — every human task removed by automation logged to the Liberation Metric (ADR-2605261000); no opaque displacement
- **G12**: **no external commercial PV sale** — modules for internal hikari install only (SBT↔SBT carve-out)
- G1 open firmware · G3 high-GWP gas abatement · G5 ≥90% circular · G6 Ag→Cu low-tox metallization · G8 full SBOM on-chain · G9 brownfield-only siting · G11 Ed25519 module provenance · G13 transport bound by kami-autodrive gates · G14 §2(h) Wellbecoming

## Non-Goals (N1–N10)

N1 no logic-fab (silicon track) · N2 no CdTe · N3 no Pb-perovskite · N4 no external commercial sales · N5 no proprietary firmware · N6 no XUAR feedstock · N7 no high-GWP venting · N8 no greenfield siting · N9 no fossil/nuclear process heat · N10 no external logistics carriage

## Roadmap

| Phase | Timeline | Scope | Gate |
|---|---|---|---|
| **R0** | 2026-06-02 | Scaffold. 7 cells RuntimeError. Composes landed robotics. | — |
| **R1** | post-Council | Benchtop **module-assembly** line PoC (lowest capex) + panel_loading + outbound PoC; feeds hikari R1 | future ADR + PV-process engineer + LANDS brownfield parcel |
| **R2** | post-R1 | Pilot **cell + wafer** lines, ~MW/yr, hikari-R2-powered; supplies hikari R2 install | **L2 coupling** + 30-day comment + hikari R2 deployed |
| **R3** | post-R2 | **Polysilicon** vertical integration — closes hikari §G2; multi-line + full outbound mesh | 60-day review + multi-domain vote + hodoki EOL contract |

## Integration

- **Sibling**: hikari (consumes himawari modules for install)
- **Loading**: sarutahiko F10 LoaderRobot · **Transport**: kami-autodrive (+ funadaiku marine R3) · **Procurement**: SBOM↔kotoba + okaimono
- **End-of-life**: hodoki (ELV-style module recovery, G5)
- **Land**: LANDS.md brownfield/industrial parcel required R1+

## References

- `/90-docs/adr/2606021200-himawari-solar-pv-manufacturing-r0.md` — Master ADR
- `/90-docs/adr/2605261100-hikari-energy-tier-b-actor-r0.md` — Sibling (generation/install)
- `/90-docs/adr/2606013100-sarutahiko-truck-factory-full-robotics-and-loader.md` — F10 LoaderRobot
- `/90-docs/adr/2606010600-kami-autodrive-gnc-autonomy-layer.md` — outbound transport
- `/90-docs/adr/2605312330-giemon-part-graph-sbom-kotoba-fleet-cve-svelte.md` — SBOM procurement
- `/90-docs/adr/2605261000-labor-liberation-transition-mechanism.md` — L2 gate + G7 coupling
- `/CLAUDE.md` — Religious-corp status table
