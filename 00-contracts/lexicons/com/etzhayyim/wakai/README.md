# com.etzhayyim.wakai.* — wakai (和会) Lexicons

**Owner actor**: `did:web:wakai.etzhayyim.com` ([`com-etzhayyim-wakai`](https://github.com/etzhayyim/com-etzhayyim-wakai))
**ADR**: ADR-2605263500 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas at R1+.

## 5 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `mutualAidContributionAttestation` | mutual_aid_pool_contribution | G6 STRUCTURAL: investmentReturnPromised const false; G8 voluntary + ability-scaled |
| L2 | `mutualAidDistributionAttestation` | mutual_aid_distribution + emergency + health_event | G9 STRUCTURAL: communityDiscernmentAttestations minLength 3 + Council Lv6+ ≥3 attestations; G7 noPreExistingConditionExclusion const true |
| L3 | `mutualAidPoolStateReport` | pool_state_reporting | Per-period aggregate state; NO individual member-contribution amounts public |
| L4 | `publicFundBackstopRequest` | public_fund_backstop_request | Council Lv6+ ≥4/7 + toritate ledgerEntry cross-link |
| L5 | `silenWakaiReview` | (Council attestation scope) | Quarterly Council review; G3/G4/G5/G6/G7/G9/G11 const-field structural enforcement |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level;
- `required` list covering constitutionally-relevant fields;
- L1 `investmentReturnPromised` const `false` (G6 STRUCTURAL);
- L2 `noPreExistingConditionExclusion` const `true` (G7 STRUCTURAL);
- L2 `communityDiscernmentAttestations` minLength 3 + `councilAttestations` minLength 3 (G9 STRUCTURAL);
- L5 const-field structural enforcement:
  - `commercialInsuranceSoftwarePenetrationPct` const 0 (G4)
  - `commercialReInsurancePenetrationPct` const 0 (G5)
  - `defiYieldFarmingActiveCount` const 0 (G6)
  - `tokenSpeculationActiveCount` const 0 (G6)
  - `preExistingConditionExclusionEventsCount` const 0 (G7)
  - `administratorVocationFlowCompliantRatioPctIntegerHundredths` const 10000 (G11)
  - `claimDenialEventsCount` const 0 (G3 anti-insurance discipline)

## R0 Status

Schemas at R0 are skeleton-level; full structural enforcement at R1.

## Related Files

- `orgs/etzhayyim/com-etzhayyim-wakai/manifest.edn` (canonical)
- `orgs/etzhayyim/com-etzhayyim-wakai/README.md`
- `orgs/etzhayyim/com-etzhayyim-wakai/CLAUDE.md`
- `/90-docs/adr/2605263500-wakai-mutual-aid-tier-b-actor-r0.md`
