# app.etzhayyim.danjo.* — Public-Accountability Oversight Lexicons

**ADR**: ADR-2605301600 (R0 scaffold)
**Owner actor**: danjo (弾正) — `did:web:danjo.etzhayyim.com`
**Status**: R0 schema skeletons. Full structural enforcement (const fields, ≥2-CID provenance check, named-party G10 gating, PII pass-through honoring) lands at R1 Council attestation review.

## Purpose

These Lexicons are written by danjo cross-reference cells over the
already-IPFS-pinned open-government corpus (`app.etzhayyim.gov.dataset.*`,
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
- **PII honoring (G9)**: no unilateral re-identification; 個人情報 / GDPR
  DSARs route via `chigiri.data_privacy` to the upstream publisher.
- **stateAlignedFlag pass-through (G13)**: CN-class / state-aligned source
  flags propagate into every derived publication.
- `additionalProperties: false` at top-level + per-ref nested objects (R1).

## R0 Status

Schemas at R0 are skeleton-level: known-value enums + required-field
lists + the `const`/`minLength` constitutional anchors are in place, but
full ref-typed nested structures land at R1.

## Cross-actor consumers

- **ossekai** (ADR-2605264000): aggregate-anonymized §1.12 publication of `oversightReport`
- **chigiri** (ADR-2605262700): external-counsel routing for legal characterization; `data_privacy` for DSARs
- **toritate** (ADR-2605262900): boundary peer — cross-reference where a state vendor also appears in the religious-corp's own tithe-recipient set
- **kataribe** (語部, press): `oversightReport` as a citable primary source

## Related Files

- `/90-docs/adr/2605301600-danjo-public-accountability-oversight-tier-b-actor-r0.md` — master ADR
- `/00-contracts/lexicons/app/etzhayyim/gov/dataset/README.md` — primary input corpus namespace
- `/20-actors/danjo/` — manifest + README + CLAUDE.md
- `/20-actors/magatama/cells/danjo_*/` — cell modules (R0 path-reserved)
