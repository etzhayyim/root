# com.etzhayyim.himawari.* — Lexicons

Per ADR-2606021200. R0 stubs; full schemas R1+.

himawari (向日葵) manufactures the solar PV modules that **hikari** (光) installs.

**STRUCTURAL ANCHOR GATES**:
- **G2**: feedstock provenance on-chain per lot — NO XUAR/forced-labor polysilicon ever (closes hikari §G2 structurally)
- **G4**: fab process heat + power from hikari renewable only — NO fossil/nuclear (inherits hikari G4/G5)
- **G7**: labor-liberation transparency — every automated-away human task logged to the Liberation Metric (ADR-2605261000)
- **G12**: NO external commercial PV sale — modules for internal hikari install only (SBT↔SBT carve-out)

| Lexicon | Purpose |
|---|---|
| `polysiliconProvenanceAttestation` | Feedstock lot provenance (G2 XUAR-exclusion + §2(g) audit, on-chain) |
| `waferBatchRecord` | Ingot/wafer batch + kerf-Si recovery + yield (G5 circular) |
| `cellBatchRecord` | Cell process (PERC/TOPCon/HJT) + flash IV + bin (G3 gas abatement + G6 Ag→Cu) |
| `moduleAttestation` | Finished module BOM + flash + EL image + EPBT; serial↔lot traceable (G11 + G4 + G12) |
| `loadingRecord` | 積込 robot cycle + pallet + carrier (sarutahiko F10 lineage; G7 coupling) |
| `outboundManifest` | Transport handoff → hikari site (kami-autodrive; G13 bound) |
| `silenHimawariReview` | Council attestation scope (provenance + chemistry + circularity + liberation-metric) |

## Related ADRs

- ADR-2606021200 — himawari master ADR
- ADR-2605261100 — hikari (sibling; himawari closes its §G2)
- ADR-2606013100 — sarutahiko F10 LoaderRobot (`panel_loading`)
- ADR-2606010600 — kami-autodrive GNC (`outbound_logistics`)
- ADR-2605312330 — SBOM↔kotoba (`supply_procurement`)
- ADR-2605261000 — Liberation Ladder L2 gate + G7 coupling
