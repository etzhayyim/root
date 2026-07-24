# com.etzhayyim.kataribe.* — kataribe (語部) Lexicons

**Owner actor**: `did:web:kataribe.etzhayyim.com` ([`com-etzhayyim-kataribe`](https://github.com/etzhayyim/com-etzhayyim-kataribe))
**ADR**: ADR-2605263600 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas at R1+.

## 5 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `communityChronicleAttestation` | community_chronicle + annual_history_compendium | G4 STRUCTURAL: toneAttestation enum DELIBERATELY excludes apocalyptic/clickbait/engagement-optimized; nonEschatologicalAttested const true (Charter §1.15) |
| L2 | `doctrineCommentaryPublishing` | doctrine_commentary | G6 STRUCTURAL: doctrinalMonopolyAttested const false (cross-doctrinal Wellbecoming priority) |
| L3 | `translationAttestation` | translation | G7+G12 STRUCTURAL: translationProvider const "murakumo-only"; commercialAiTranslationToolUsed const false |
| L4 | `whistleblowerReport` | whistleblower_channel | G10 STRUCTURAL: encryptedPayloadCid REQUIRED; chigiri.ipLicenseClaim cross-link |
| L5 | `silenKataribeReview` | (Council attestation scope) | G3/G4/G5/G6/G7/G8/G11/G12 const-field structural enforcement |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level;
- `required` list covering constitutionally-relevant fields;
- L1 STRUCTURAL: `toneAttestation` enum DELIBERATELY excludes apocalyptic/clickbait/engagement-optimized; `nonEschatologicalAttested` const true;
- L2 STRUCTURAL: `doctrinalMonopolyAttested` const false;
- L3 STRUCTURAL: `translationProvider` const "murakumo-only"; `commercialAiTranslationToolUsed` const false;
- L4 STRUCTURAL: `encryptedPayloadCid` REQUIRED;
- L5 STRUCTURAL multiple const-field enforcement (G3/G4/G5/G6/G7/G8/G11/G12 — see review schema).

## R0 Status

Schemas at R0 are skeleton-level; full structural enforcement at R1.

## Related Files

- `orgs/etzhayyim/com-etzhayyim-kataribe/manifest.edn` (canonical)
- `orgs/etzhayyim/com-etzhayyim-kataribe/README.md`
- `orgs/etzhayyim/com-etzhayyim-kataribe/CLAUDE.md`
- `/90-docs/adr/2605263600-kataribe-press-publishing-translation-tier-b-actor-r0.md`
