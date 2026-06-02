# com.etzhayyim.mizuho.* — mizuho (水穂) Lexicons

**Owner actor**: `did:web:mizuho.etzhayyim.com` (`20-actors/mizuho/`)
**ADR**: ADR-2605263100 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas at R1+.

## 5 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `waterQualityAttestation` | all supply cells | Per-source / per-period quality test (WHO Drinking Water Guidelines: microbiological + chemical + radiological + physical) |
| L2 | `wastewaterDischargeAttestation` | wastewater_treatment | Per-discharge attestation; G9 jurisdictional permit compliance |
| L3 | `waterSupplySourceRegistry` | all supply cells | Per-source registry (well/spring/captured rainwater/partner feed); G11 Land Registry waqf cross-link |
| L4 | `waterContaminationIncident` | any cell | Anomaly / contamination; severity enum; critical = halt cell + chigiri.disputeMediation escalation |
| L5 | `silenMizuhoReview` | (Council attestation scope) | Quarterly Wellbecoming + closed-loop ratio + multi-gen consumption review |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level;
- `required` list covering constitutionally-relevant fields;
- L3 `waterSupplySourceRegistry.landRegistryCid` REQUIRED (G11 structural);
- L1 + L2 + L3 use **`$ref` pattern** for nested object types (per
  Lexicon spec; see linter-applied pattern in chigiri / toritate / iyashi);
- Integer units (e.g., `volumeLiters` rather than `volumeKiloLiters: number`;
  follows squareCentimeters / usdMillicents convention).

## R0 Status

Schemas at R0 are skeleton-level; full structural enforcement at R1.

## Related Files

- `/20-actors/mizuho/manifest.jsonld`
- `/20-actors/mizuho/README.md`
- `/20-actors/mizuho/CLAUDE.md`
- `/90-docs/adr/2605263100-mizuho-water-sanitation-tier-b-actor-r0.md`
