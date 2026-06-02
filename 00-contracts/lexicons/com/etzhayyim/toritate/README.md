# com.etzhayyim.toritate.* — toritate (執帳) Lexicons

**Owner actor**: `did:web:toritate.etzhayyim.com` (`20-actors/toritate/`)
**ADR**: ADR-2605262900 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas at R1+.

## 5 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `financialAttestation` | annual_audit_report (+ all summary-emitting cells) | Per-period (daily / monthly / quarterly / annual) summary attestation |
| L2 | `ledgerEntry` | transaction_ledger | Single on-chain transaction; category enum (G12 EXCLUDES `payroll` / `wage` / `salary`); amount; counterparty DID; supporting CID |
| L3 | `annualReport` | annual_audit_report | Annual transparency report; Council ≥3 attestation chain (G6) |
| L4 | `auditObservation` | any cell | Anomaly / finding; routes to Council mediation if critical |
| L5 | `externalAuditorEngagement` | annual_audit_report | External auditor contract record (Public Fund Safe contract CID + scope + Council Lv6+ attestations); G5 UPL-equivalent boundary |

## Schema Discipline (R1+)

All 5 Lexicons at R1 will enforce:

- `additionalProperties: false` at top-level record schema;
- `required` list covering every constitutionally-relevant field;
- `ledgerEntry.category` enum DELIBERATELY excludes `payroll` / `wage`
  / `salary` / `bonus` / `commission` (G12 structural enforcement of
  volunteer ≠ employee per ADR-2605261000 + ADR-2605262700 G13);
- `financialAttestation.publishedDonorPii` enum constrained to
  `{none, aggregated-only, opt-in-explicit}` — `verbatim-donor-names`
  is NOT a valid value (G10 structural enforcement);
- `externalAuditorEngagement.opinionDocumentCid` is the opinion
  document hash from the external auditor; toritate does NOT modify
  the opinion text (G5 UPL boundary).

## R0 Status

Schemas at R0 are skeleton-level: the field set is enumerated but
strict validation is not yet enforced (schemas evolve through R1
Council attestation review).

## Related Files

- `/20-actors/toritate/manifest.jsonld`
- `/20-actors/toritate/README.md`
- `/20-actors/toritate/CLAUDE.md`
- `/90-docs/adr/2605262900-toritate-accounting-audit-tier-b-actor-r0.md`
