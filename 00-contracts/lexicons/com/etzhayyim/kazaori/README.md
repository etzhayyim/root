# com.etzhayyim.kazaori.* — kazaori (風折) Lexicons

**Owner actor**: `did:web:kazaori.etzhayyim.com` (`orgs/etzhayyim/com-etzhayyim-kazaori/`)
**ADR**: ADR-2605263200 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas at R1+.

## 6 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `emergencyDeclarationAttestation` | emergency_declaration | Council Lv6+ ≥4/7 declaration; G10 structural; duration enum; declaredScope |
| L2 | `damageAssessmentReport` | damage_assessment | Per-area / per-asset damage; cross-actor data fusion sources via $ref |
| L3 | `emergencySupplyDispatch` | emergency_water_supply + emergency_food_supply | Per-dispatch event; cross-actor mizuho/mitsuho; carve-out cite via $ref |
| L4 | `evacuationCheckIn` | mass_evacuation | OPT-IN self-attestation; encryptedPayloadCid REQUIRED; G6 structural (no surveillance) |
| L5 | `emergencyCarveOutLog` | any cell | Per-carve-out activation log; gate carved + Council attestation + auto-revoke timestamp; G8 structural |
| L6 | `silenKazaoriReview` | (Council attestation scope) | Post-emergency review; Sphere Standards compliance + carve-out audit + Wellbecoming preservation |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level;
- `required` list covering constitutionally-relevant fields;
- L1 `councilAttestations` minLength 4 (G10 structural);
- L4 `encryptedPayloadCid` REQUIRED + G6 structural (opt-in self-check-in only; no surveillance fields);
- L5 `autoRevokeAtUtc` REQUIRED + G8 structural (auto-revoke on lifting; no carry-over to normal ops);
- Cross-actor data fusion via $ref pattern (parameterResult / crossActorSource / carveOutCitation etc.)

## R0 Status

Schemas at R0 are skeleton-level; full structural enforcement at R1.

## Related Files

- `/orgs/etzhayyim/com-etzhayyim-kazaori/manifest.jsonld`
- `/orgs/etzhayyim/com-etzhayyim-kazaori/README.md`
- `/orgs/etzhayyim/com-etzhayyim-kazaori/CLAUDE.md`
- `/90-docs/adr/2605263200-kazaori-disaster-response-tier-b-actor-r0.md`
