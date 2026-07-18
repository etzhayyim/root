# com.etzhayyim.musubi.* — musubi (結) Lexicons

**Owner actor**: `did:web:musubi.etzhayyim.com` ([`com-etzhayyim-musubi`](https://github.com/etzhayyim/com-etzhayyim-musubi))
**ADR**: ADR-2605263400 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas at R1+.

## 5 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `ceremonyPerformanceAttestation` | all 6 ceremony cells | Per-ceremony performance record; G11 cross-link to chigiri.covenantAttestation CID; G10 multi-gen ratio enforced |
| L2 | `officiantAttestation` | (all cells; officiant verification) | G3 STRUCTURAL: officiantClass enum DELIBERATELY excludes "clergy" / "ordained" / "priest" / "bishop" / "minister-with-ecclesiastical-authority"; valid value = "community-witnessed-competent" |
| L3 | `communityWitnessAttestation` | all 6 cells | Per-ceremony witnesses; G10 multi-gen required |
| L4 | `seasonalCeremonyCalendar` | seasonal_communal_ceremony | Annual calendar of communal ceremonies; opt-in attendance registry |
| L5 | `silenMusubiReview` | (Council attestation scope) | Quarterly Council Wellbecoming + G10 multi-gen ratio + G7 anti-coercive-economy + Charter §1.13 compliance |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level;
- `required` list covering constitutionally-relevant fields;
- L2 `officiantAttestation.officiantClass` enum **DELIBERATELY EXCLUDES** `clergy` / `ordained` / `priest` / `bishop` / `minister-with-ecclesiastical-authority` (G3 STRUCTURAL — Reformed 万人祭司 invariant);
- L2 `officiantAttestation.lLevel` const `"L5"` + `.employmentRelation` const `"vocation-flow"` (G12 STRUCTURAL — same pattern as iyashi.providerAttestation);
- L1 `ceremonyPerformanceAttestation.chigiriCovenantAttestationCid` REQUIRED for marriage / naming / funeral / vocation-vow / rededication ceremony types (G11 STRUCTURAL);
- L1 `bridePriceOrDowryAttested` const `false` (G7 STRUCTURAL);
- L1 `videoRecordingPerPartyConsent` REQUIRED when video produced (G8 STRUCTURAL);
- L5 `silenMusubiReview` const-field structural enforcement (G3/G6/G7/G12 + Wellbecoming).

## R0 Status

Schemas at R0 are skeleton-level; full structural enforcement at R1.

## Related Files

- `orgs/etzhayyim/com-etzhayyim-musubi/manifest.edn` (canonical)
- `orgs/etzhayyim/com-etzhayyim-musubi/README.md`
- `orgs/etzhayyim/com-etzhayyim-musubi/CLAUDE.md`
- `/90-docs/adr/2605263400-musubi-covenant-ceremony-tier-b-actor-r0.md`
