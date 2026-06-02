# 20-actors/himawari — CLAUDE.md

## Identity

- **Name**: himawari (向日葵 — "sunflower / sun-turning"; heliotropic echo of solar trackers + the manufacture of light-capturing surfaces; deliberate sibling resonance with hikari 光)
- **DID**: `did:web:etzhayyim.com:himawari`
- **ADR**: ADR-2606021200 (R0 scaffold, 2026-06-02)
- **Parent ADR**: ADR-2605261000 (Liberation Ladder — feeds L2 Sustenance via hikari)
- **Tightest sibling**: hikari (ADR-2605261100 — generation/install)
- **Status**: R0 scaffold — all cells import-time RuntimeError

## What himawari is (and is not)

himawari **manufactures** the solar PV modules that hikari **installs**. It is the manufacturing half of the energy chain:

```
製造 (himawari) → 積込 (sarutahiko F10) → 輸送 (kami-autodrive) → 設置 (hikari)
```

- It is **NOT** the silicon iwakura/fuigo/tsukuru track (that is logic/compute ASIC fab, ADR-2605242500). himawari is **solar-grade** c-Si only (N1).
- It does **NOT** re-implement loading/transport robotics — it **composes** the already-landed, tests-green sarutahiko F10 LoaderRobot + kami-autodrive GNC + giemon AGV.

## Architecture

7 Pregel cells, manufacture → loading → outbound, fed by procurement:

```
supply_procurement (調達) ──feedstock──┐
                                       ▼
polysilicon_refine → ingot_wafer → cell_process → module_assembly
                                                        │
                                                        ▼
                                                 panel_loading (積込)
                                                        │
                                                        ▼
                                                 outbound_logistics (輸送) ──→ hikari install
```

Each cell = 1 Pregel graph. R0: every cell raises RuntimeError on `.solve()`.

## Structural anchors (CRITICAL gates)

### G2: Feedstock provenance on-chain — closes hikari §G2
- NO XUAR / forced-labor polysilicon, EVER. No conflict-mineral In/Ga.
- Full polysilicon→module chain-of-custody CID-anchored per lot.
- This is the *structural* fix for hikari §G2 (which otherwise relies on vendor self-attestation of purchased modules). Vertical integration is the point of this actor.

### G4: Renewable-only process heat (inherits hikari G4/G5)
- Fab process heat + power from hikari renewable only. NO fossil, NO nuclear, at any tier.
- Net-positive lifecycle energy: EPBT < module service life with margin.
- Couples himawari R2 throughput to hikari R2 energy budget — a PV fab is ~MW-scale; mitigation is batch / lower-duty-cycle operation (mirrors silicon Wave 2 mitigation in hikari ADR).

### G7: Labor-liberation transparency
- Every human task removed by automation is logged to the Liberation Metric (ADR-2605261000).
- PV manufacture is highly automatable; this gate makes the automation **accounted 労働解放**, never opaque displacement. This is the mission tie-in — automation here is the *point*, but it must be measured and transparent.

### G12: No external commercial PV sale
- Modules are for **internal hikari install only** (SBT↔SBT internal carve-out, ADR-2605192115 §3). Surplus → community-benefit, never market.

## Robotics Fleet (compose, do not re-implement)

| Robot | Class | Function | Lineage | Status |
|---|---|---|---|---|
| F10 LoaderRobot | straddle loader | `panel_loading` 積込 | sarutahiko (ADR-2606013100) | 🟢 14 tests |
| AGV | floating-base cart | intra-fab transport | giemon (ADR-2606010030) | 🟢 13 tests |
| GNC | autonomy layer | `outbound_logistics` truck/ship | kami-autodrive (ADR-2606010600) | 🟢 9 tests |
| Otete | precision arm | cell handling / stringing / framing | kuni-umi | inherited |
| Mimi | metrology | flash IV + EL imaging + thermal-IR | kuni-umi | inherited |
| Hinata (日向) (R2+) | lamination-press + stringer | autonomous module assembly | new class | separate mech-design ADR |

## Lexicon Namespace

**App lexicon root**: `app.etzhayyim.himawari`

7 records (R0 stubs; full schemas R1+):

1. `polysiliconProvenanceAttestation` — feedstock lot provenance (XUAR-exclusion + §2(g) audit, on-chain)
2. `waferBatchRecord` — ingot/wafer batch + kerf recovery + yield
3. `cellBatchRecord` — cell process params (open) + flash IV + bin
4. `moduleAttestation` — finished-module BOM + flash + EL image CID + EPBT block
5. `loadingRecord` — 積込 robot cycle + pallet + carrier (F10 lineage)
6. `outboundManifest` — transport handoff (carrier DID, route, kami-autodrive class)
7. `silenHimawariReview` — Council attestation scope (provenance + chemistry + circularity + liberation-metric)

## Pregel Cells (R0 stub bodies)

All R0 cells raise `RuntimeError("himawari R0 scaffold: ... not activated. ...")` on `.solve()`.

### R1 activation triggers
1. ADR-2606021200 Council Lv6+ ratify
2. ≥1 PV-process engineer on Council technical advisory
3. ≥1 LANDS.md brownfield/existing-industrial parcel registered
4. G2 feedstock provenance audit framework operational (on-chain chain-of-custody)
5. G3 high-GWP gas abatement framework Council-ratified

## Build & Deploy

**R0 status**: Scaffold only. All cells RuntimeError on `.solve()`.

**Smoke test**:
```bash
cd 20-actors/himawari
for c in polysilicon_refine ingot_wafer cell_process module_assembly panel_loading outbound_logistics supply_procurement; do
  python -c "from himawari.cells.$c.cell import *" && echo "import ok: $c"
done
```
(Cells import cleanly; `.solve()` raises the R0 RuntimeError.)

## Related Files

- `/20-actors/himawari/manifest.jsonld`
- `/90-docs/adr/2606021200-himawari-solar-pv-manufacturing-r0.md` — Master ADR
- `/90-docs/adr/2605261100-hikari-energy-tier-b-actor-r0.md` — Sibling (generation/install)
- `/90-docs/adr/2606013100-sarutahiko-truck-factory-full-robotics-and-loader.md` — F10 LoaderRobot
- `/90-docs/adr/2606010600-kami-autodrive-gnc-autonomy-layer.md` — outbound transport
- `/90-docs/adr/2605312330-giemon-part-graph-sbom-kotoba-fleet-cve-svelte.md` — SBOM procurement
- `/20-actors/kuni-umi/README.md` — Otete/Mimi class lineage
- `/CLAUDE.md` — Religious-corp status table
