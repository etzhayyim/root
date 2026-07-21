# com.etzhayyim.shidemori.* — shidemori (死出守) Lexicons (FINAL gap-closure)

**Owner actor**: `did:web:shidemori.etzhayyim.com` ([`com-etzhayyim-shidemori`](https://github.com/etzhayyim/com-etzhayyim-shidemori))
**ADR**: ADR-2605263800 (R0 scaffold; **FINAL gap-closure** of 10-actor 30min-loop wave)
**Status**: R0 schema skeletons. Full schemas at R1+.

## 5 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `memorialNftAttestation` | memorial_nft_mint | G3 STRUCTURAL: afterlifeDoctrineImposed const false (Charter §1.15 non-eschatological); musubi funeral + chigiri inheritance cross-link |
| L2 | `cemeteryLandAttestation` | cemetery_land_registry | G10 STRUCTURAL: landRegistryCid REQUIRED + waqfInalienabilityAttested const true (mizuho G11 pattern shared) |
| L3 | `chinkonRemembranceAttestation` | chinkon_annual_remembrance | G4 cross-doctrinal accommodation tracking; Charter §1.7 multi-gen cohort mix |
| L4 | `externalMortuaryEngagement` | external_mortuary_engagement | UPL-equivalent pattern (chigiri G14 + iyashi N9 + kokoro G3 + shidemori G5 = 4-actor maturity); Public Fund Safe + Council Lv6+ ≥4 attestations |
| L5 | `silenShidemoriReview` | silen_shidemori_review | G3/G4/G5/G6/G7/G8/G9/G10/G11/G12 const-field structural enforcement |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level;
- `required` list covering constitutionally-relevant fields;
- L1 STRUCTURAL: `afterlifeDoctrineImposed` const false (G3);
- L2 STRUCTURAL: `landRegistryCid` REQUIRED + `waqfInalienabilityAttested` const true (G10);
- L3 STRUCTURAL: cohort mix multi-gen tracking + cross-doctrinal accommodation array;
- L4 STRUCTURAL: `publicFundSafeContractCid` REQUIRED + `councilAttestations` minLength 4;
- L5 STRUCTURAL multiple const-field enforcement:
  - `eschatologicalContentEventsCount` const 0 (G3)
  - `commercialMemorialSoftwarePenetrationPct` const 0 (G6)
  - `embalmingChemicalUsageEventsCount` const 0 (G7)
  - `mortuarySurveillanceEventsCount` const 0 (G8)
  - `stateLicensedMortuaryFirstPartyPct` const 0 (G5)
  - `mandatoryBurialEventsCount` const 0 (G9)
  - `cemeteryLandWaqfInalienabilityCompliantRatioPctIntegerHundredths` const 10000 (G10)
  - `guardianVocationFlowCompliantRatioPctIntegerHundredths` const 10000 (G11)
  - `singleDoctrinalAfterlifeMonopolyEventsCount` const 0 (G4)
  - `commercialMemorialAiUsageCount` const 0 (G12)

## R0 Status

Schemas at R0 are skeleton-level; full structural enforcement at R1.

## Related Files

- `orgs/etzhayyim/com-etzhayyim-shidemori/manifest.edn` (canonical)
- `orgs/etzhayyim/com-etzhayyim-shidemori/README.md`
- `orgs/etzhayyim/com-etzhayyim-shidemori/CLAUDE.md`
- `/90-docs/adr/2605263800-shidemori-memorial-cemetery-tier-b-actor-r0.md`
