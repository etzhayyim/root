# com.etzhayyim.narashi.* — Global Inequality Observation Lexicons

**ADR**: ADR-2607101800 (R0 scaffold)
**Owner actor**: narashi (均) — `did:web:narashi.etzhayyim.com`
**Status**: R0 schema skeletons. Full structural enforcement (const fields, provenance-CID checks,
G8 non-causal gating, Murakumo attestation) lands at R1 Council attestation review.

## Purpose

These Lexicons are written by narashi cells over the pre-published World Bank WDI / UN SDG API / Our
World in Data DataLad snapshots (`org.worldbank.api`, `org.un.unstats`, `org.ourworldindata`) and,
read-only, over kanae's `com.etzhayyim.kanae.fundFlowEdge` graph (ADR-2605302300). narashi projects
global inequality indicators (Gini, poverty headcount, income share, SDG 10) into kotoba EAVT,
optionally juxtaposes them against kanae's aid/loan flow data (**non-causally**, G8), narrates trends
with Murakumo-only LLM (FACTUAL, source-cited, **NON-adjudicating**), and — at R3+ — publishes
aggregate reports. **narashi never ranks jurisdictions and never claims causality.**

## 4 Lexicons

| # | Lexicon | Cell | Purpose |
|---|---|---|---|
| L1 | `metricObservation` | `narashi_metric_ingest` | One typed FACTUAL indicator value (Gini / poverty-headcount / income-share / SDG 10.1.1). `indicator` descriptive enum (no ranking token, G4); `sourceRecordCids[]` (G5); kotoba EAVT (G2) |
| L2 | `crossReferenceNote` | `narashi_cross_reference` | Non-causal pairing of a `metricObservation` trend with a kanae `fundFlowEdge`. `causalClaim` const `false` (G8) |
| L3 | `metricNarrative` | `narashi_narrative` | Murakumo-LLM factual trend description. `nonAdjudicatingNotice=true` (G4); `murakumoInferenceAttestation` required (G7) |
| L4 | `methodNote` | (all cells) | Open, versioned normalization/aggregation heuristic; the public audits the aggregation itself (G6) |

## Schema Discipline — CONSTITUTIONAL

- **NON-adjudicating (G4)**: `metricNarrative.nonAdjudicatingNotice` is a required `const: true`. The
  `indicator` enum on `metricObservation` carries no merit/ranking token — a value is a disclosed
  statistic, never a verdict on the jurisdiction.
- **Non-causal (G8)**: `crossReferenceNote.causalClaim` is a required `const: false`. narashi juxtaposes
  two independently-sourced series; it structurally cannot assert that one caused the other.
- **Source-provenance mandatory (G5)**: `sourceRecordCids[]` on `metricObservation` requires ≥2 CIDs
  unless `singleSourced=true` is explicit (some indicator-jurisdiction-year triples are published by
  only one Tier-A source).
- **Murakumo-only inference (G7)**: `metricNarrative.murakumoInferenceAttestation` is required; a
  vendor-LLM origin is unrepresentable at the schema layer.
- **kotoba-native persistence (G2)**: all four record types live in kotoba EAVT — RisingWave / Postgres
  / Lance / DuckDB / SQLite are PROHIBITED as primary store or read backend (ADR-2605262130).

See `20-actors/narashi/README.md` (in the standalone `etzhayyim/com-etzhayyim-narashi` repo) and
`90-docs/adr/2607101800-narashi-global-inequality-observation-tier-b-actor-r0.md` for the full actor
scope, gates (G1–G9), and non-goals (N1–N8).
