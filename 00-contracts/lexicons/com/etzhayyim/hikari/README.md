# com.etzhayyim.hikari.* — Lexicons

Per ADR-2605261100. R0 stubs; full schemas R1+.

**CONSTITUTIONAL INVARIANTS** (Lv7 unanimity to amend):
- G4: NO nuclear (fission/fusion/RTG) at any tier ever
- G5: NO fossil fuel at any tier ever
- G8: NO rare-earth permanent magnets (NdFeB ban)

| Lexicon | Purpose |
|---|---|
| `parcelEnergyAttestation` | Resource baseline + biodiversity-no-harm + G9 land-trust class |
| `installAttestation` | Per-install record (G2 sourcing + G3 chemistry + G8 magnet attestation) |
| `generationRecord` | Per-period generation (G11 Ed25519 per-inverter 15-min) |
| `consumptionAuditRecord` | G6 anti-surveillance aggregate consumption |
| `silenEnergyReview` | Council attestation scope (G4/G5/G8 Lv7-unanimity flagged) |

## Related ADRs

- ADR-2605261100 — hikari master ADR
- ADR-2605261000 — Liberation Ladder L2 gate
- ADR-2605192245 — Land Trust
- ADR-2605242500 — silicon Wave 1 (fab load consumer R3)
