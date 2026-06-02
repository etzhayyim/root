# com.etzhayyim.chigiri.* — chigiri (契) Lexicons

**Owner actor**: `did:web:chigiri.etzhayyim.com` (`20-actors/chigiri/`)
**ADR**: ADR-2605262700 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas (additionalProperties=false + required fields enforcement) at R1+.

## 9 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `covenantAttestation` | `covenant_ceremony` | Generic covenant — SBT issuance / marriage / naming / funeral (ceremonyType enum) |
| L2 | `excommunicationProcedure` | `member_offboarding` | 30-day cure window + Council Lv6+ ≥4/7 + finalization; G12 structural enforcement |
| L3 | `withdrawalAttestation` | `member_offboarding` | Voluntary withdrawal — member-signed + 7-day cooling period |
| L4 | `inheritanceChain` | `inheritance` | DID-bound succession; SBT + wallet handover; Council ≥3 |
| L5 | `disputeMediation` | `dispute_mediation` | Cooperative-first procedure; G10 enforces ≥1 mediation round before arbitration |
| L6 | `ipLicenseClaim` | `ip_licensing` | Apache 2.0 + Charter Rider §3 violation claim; three-tier remedy ladder |
| L7 | `taxReceipt` | `tax_receipt` | Multi-jurisdiction donation receipt routing (US 501(c)(3) eq-det / UK Gift Aid / DE Spendenquittung / JP unavailable / others) |
| L8 | `stewardLaborAttestation` | `employment_compliance` | L0..L6 classification per ADR-2605261000; G13 employmentRelation enum excludes "employee" (constructive-employment prevention) |
| L9 | `forceAuthorizationRecord` | `transparent_force_authorization` | ADR-2605192315 1 SBT = 1 vote integration; posture enum {defensive, deterrent} only (offensive impossible at schema layer per G7) |

## Schema Discipline (R1+)

All 9 Lexicons at R1 will enforce:

- `additionalProperties: false` at top-level record schema (no
  unrecognized fields);
- `required` list covering every constitutionally-relevant field
  (gate enforcement: missing field = invalid record = procedure
  invisible per G2);
- Enum-based posture / classification fields use `knownValues` to
  structurally exclude constitutionally-prohibited values
  (`employee` for stewardLaborAttestation, `offensive` for
  forceAuthorizationRecord).

## R0 Status

Schemas at R0 are skeleton-level: the field set is enumerated but
strict validation is not yet enforced (schemas evolve through R1
Council attestation review).

## Related Files

- `/20-actors/chigiri/manifest.jsonld`
- `/20-actors/chigiri/README.md`
- `/20-actors/chigiri/CLAUDE.md`
- `/90-docs/adr/2605262700-chigiri-legal-procedure-tier-b-actor-r0.md`
