# com.etzhayyim.silicon — silicon attestation lexicons

Per **ADR-2605242500** (silicon charter) and **ADR-2605242545** (8 fab
equipment + Pregel cell catalog).

| Lexicon | Role |
|---|---|
| `chipManufacturingAttestation` | Per-die shipment attestation (lot/die-XY/peer-ID/bin/leased-to DID) |
| `silenForceReview` | Council Lv6+ ≥ 3 multisig §2(a)(c) review record (REQUIRED to ship silicon) |
| `fabEquipmentTelemetry` | Down-sampled audit telemetry from fab equipment |
| `waferLotAttestation` | Per-step (per super-step) append-only attestation for a wafer lot |

## Hard rules

1. **No `chipManufacturingAttestation` can ship without a passing
   `silenForceReview`** for the relevant lot or design baseline.

2. **`waferLotAttestation` is append-only.** Steps cannot be retroactively
   rewritten; rework / scrap is recorded as new step entries with
   `outcome != 'ok'`.

3. **HIGH-risk steps** (`litho`, `implant`) require an attached
   `silenForceReviewUri` on every `waferLotAttestation` of that step.

4. **High-rate telemetry** (kHz / MHz raw sensor stream) does NOT go
   into `fabEquipmentTelemetry`. That goes over libp2p direct stream.
   `fabEquipmentTelemetry` is the audit-trail down-sample only.

## Pregel cell pairing

| Lexicon | Cells that write |
|---|---|
| `chipManufacturingAttestation` | `silicon_test` (after bin), `silicon_packaging` (after final packaging) |
| `silenForceReview` | NOT cell-written; written by Council members directly via XRPC |
| `fabEquipmentTelemetry` | All 8 `silicon_*` cells (down-sample their libp2p subscription) |
| `waferLotAttestation` | All 8 `silicon_*` cells (one per super-step) |

## Lexicon graph projection (kotoba-datomic L1)

These 4 lexicons are intentionally "narrow surface" — the per-lot history
chain (`waferLotAttestation` ordered by `stepIndex`) and the per-chip
shipment record (`chipManufacturingAttestation`) are designed to project
cleanly into a graph view (`kotoba-datomic-projection`, per ADR-2605231500),
should that be needed for fab analytics. Projection is Phase 2 work; the
write SoT is MST as always.
