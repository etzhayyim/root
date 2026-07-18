# com.etzhayyim.danjo.* — Public-Accountability Oversight Lexicons

**ADR**: ADR-2605301600 (R0 scaffold)
**Owner actor**: danjo (弾正) — `did:web:danjo.etzhayyim.com`
**Status**: R0 schema skeletons. Full structural enforcement (const fields, ≥2-CID provenance check, named-party G10 gating, PII pass-through honoring) lands at R1 Council attestation review.

## Purpose

These Lexicons are written by danjo cross-reference cells over the
already-IPFS-pinned open-government corpus (`com.etzhayyim.gov.dataset.*`,
ADR-2605263900 — for Japan: 国会会議録 / 予算書 / 政府調達 / e-Stat).
danjo ingests that corpus into kotoba EAVT and emits FACTUAL, source-
cited, **NON-adjudicating** discrepancy observations + aggregate
transparency reports. The censor's eye, never the censor's sword.

## 4 Lexicons

| # | Lexicon | Cell | Purpose |
|---|---|---|---|
| L1 | `discrepancyObservation` | `danjo_crossref_engine` / `danjo_statement_consistency` | Factual, source-cited, NON-adjudicating anomaly. `nonAdjudicatingNotice=true` (G4); `sourceRecordCids[]` ≥2 (G5); `methodNoteCid` (G6) |
| L2 | `crossReferenceLink` | `danjo_crossref_engine` | Typed factual edge between gov records (or gov record ↔ corp entity), citing public basis |
| L3 | `oversightReport` | `danjo_oversight_report` | Periodic AGGREGATE transparency report; Council Lv6+ ≥3 attestation; IPFS-pinned |
| L4 | `methodNote` | (all detector cells) | Open, versioned detector-heuristic definition; the public audits the detector itself |

## Schema Discipline (R1+) — CONSTITUTIONAL

- **NON-adjudicating (G4)**: `discrepancyObservation.nonAdjudicatingNotice`
  is `const: true`; the `category` enum contains NO `crime` / `violation`
  / `guilt` value — a legal verdict is unrepresentable at the schema
  layer (same pattern as chigiri's `posture=offensive` being
  unrepresentable in `forceAuthorizationRecord`). Legal characterization
  routes to external counsel via chigiri + Public Fund.
- **Source-provenance (G5)**: `sourceRecordCids` has `minLength: 2`; every
  observation is grounded in ≥2 upstream `gov.dataset.*` public records.
- **Open method (G6)**: every observation cites a `methodNote` CID; no
  closed scoring.
- **Aggregate-first + named-party gating (G10)**: `oversightReport`
  publishes aggregate stats by default; `namedPartySection` is populated
  ONLY where source records already name the party publicly AND
  severity-gated + Council-reviewed + 1 SBT = 1 vote (`oneSbtOneVoteChainCid`).
- **Named parties are structurally gated (G10), not free text**:
  `discrepancyObservation.namedParties[]` is `#namedPartyRef` — every entry
  MUST carry a `publiclyNamedBasis` enum + the single `sourceRecordCid` that
  ALREADY names the party. danjo can never originate a name. In
  `oversightReport`, `namedPartySection[]` is `#namedPartyEntry`, whose
  `councilReviewCid` + `oneSbtOneVoteChainCid` are REQUIRED fields — an entry
  is structurally incomplete (and cannot publish) without both gate proofs.
- **Aggregate counts are structured (N9)**: `oversightReport.aggregateStats[]`
  is `#aggregateStat` ({category, severity, count, methodNoteCids}); never a
  per-individual figure. Replaces the R0 freeform JSON string.
- **PII honoring (G9)**: no unilateral re-identification; 個人情報 / GDPR
  DSARs route via `chigiri.data_privacy` to the upstream publisher.
- **stateAlignedFlag pass-through (G13)**: CN-class / state-aligned source
  flags propagate into every derived publication.
- `additionalProperties: false` at top-level + per-ref nested objects (R1).

## R0 Status

Schemas at R0 are skeleton-level: known-value enums + required-field
lists + the `const`/`minLength` constitutional anchors are in place.
`discrepancyObservation` + `oversightReport` already carry ref-typed
nested defs (`#namedPartyRef` / `#aggregateStat` / `#namedPartyEntry`);
`crossReferenceLink` + `methodNote` stay flat until R1. `additionalProperties:false`
is the R1 closure step (per the repo-wide convention; see toritate
`financialAttestation`).

## Repo-wide validation (integration coverage)

The 4 danjo lexicons pass the repo's lexicon lints: `nsid-lexicon-exists`,
`lexicon-primary-types`, and `nsid-lexicon-registration` all green, and
the generated `NSID_APP_ETZHAYYIM_DANJO_*` constants are collision-free
(no name clash with any of the ~6.7k existing lexicons). They are also
guarded by the actor-specific `no-danjo-adjudication.mjs` (G4 + G8) and
its 8-test regression suite.

## Cross-actor consumers

- **ossekai** (ADR-2605264000): aggregate-anonymized §1.12 publication of `oversightReport`
- **chigiri** (ADR-2605262700): external-counsel routing for legal characterization; `data_privacy` for DSARs
- **toritate** (ADR-2605262900): boundary peer — cross-reference where a state vendor also appears in the religious-corp's own tithe-recipient set
- **kataribe** (語部, press): `oversightReport` as a citable primary source

## Related Files

- `/90-docs/adr/2605301600-danjo-public-accountability-oversight-tier-b-actor-r0.md` — master ADR
- `/00-contracts/lexicons/com/etzhayyim/gov/dataset/README.md` — primary input corpus namespace
- `/orgs/etzhayyim/com-etzhayyim-danjo/` — manifest + README + CLAUDE.md
- `/40-engine/kotoba/crates/kotoba-kotodama/cells/danjo_*/` — cell modules (R0 path-reserved)
