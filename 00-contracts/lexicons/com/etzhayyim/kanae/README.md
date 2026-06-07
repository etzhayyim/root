# com.etzhayyim.kanae.* — Global Government Fiscal-Flow Visualization Lexicons

**ADR**: ADR-2605302300 (R0 scaffold)
**Owner actor**: kanae (鼎) — `did:web:kanae.etzhayyim.com`
**Status**: R0 schema skeletons. Full structural enforcement (const fields, ≥2-CID provenance check, named-element G10 gating, Murakumo attestation) lands at R1 Council attestation review.

## Purpose

These Lexicons are written by kanae cells over the danjo cross-reference
graph (`com.etzhayyim.danjo.*`, ADR-2605301600 + extension ADR-2605302245)
and the already-IPFS-pinned open-government corpus
(`com.etzhayyim.gov.dataset.*`, ADR-2605263900 — USAspending / EU FTS /
IMF SDMX / World Bank / OECD / UN + JP 予算書 / 政府調達). kanae assembles
worldwide fund flows into kotoba EAVT, narrates them with Murakumo-only
LLM (FACTUAL, source-cited, **NON-adjudicating**), and renders
aggregate-first kami-engine WASM visualizations. **danjo finds, kanae
renders.**

## 4 Lexicons

| # | Lexicon | Cell | Purpose |
|---|---|---|---|
| L1 | `fundFlowEdge` | `kanae_flow_assembler` / `kanae_intergov_flow` | Typed FACTUAL fiscal flow edge in the kotoba graph. `flowClass` descriptive enum (no verdict token, G4); `sourceRecordCids[]` ≥2 (G5); kotoba EAVT (G2) |
| L2 | `flowNarrative` | `kanae_flow_narrative` | Murakumo-LLM factual description of a flow subgraph. `nonAdjudicatingNotice=true` (G4); `murakumoInferenceAttestation` required (G7); ≥2 source CIDs (G5) |
| L3 | `visualizationManifest` | `kanae_viz_compiler` | kami-engine WASM scene descriptor (G14); `aggregateOnly=true` (G10); carries the `kotobaQuery` that reproduces it (§2(e)); no ad/analytics SDK (G15) |
| L4 | `methodNote` | (all assembly + narrative cells) | Open, versioned aggregation / narrative-prompt heuristic; the public audits the aggregation itself |

## Schema Discipline (R1+) — CONSTITUTIONAL

- **NON-adjudicating (G4)**: `flowNarrative.nonAdjudicatingNotice` is
  `const: true`; the `fundFlowEdge.flowClass` enum contains NO `crime` /
  `violation` / `guilt` / `不正` value — a legal verdict is
  unrepresentable at the schema layer (same pattern as danjo's
  `discrepancyObservation.category` and chigiri's `posture=offensive`).
  A visualization may imply nothing the linked narrative does not
  factually state. Legal characterization routes to external counsel via
  chigiri + Public Fund.
- **kotoba-native persistence (G2; N13)**: the fund-flow graph is kotoba
  EAVT — NOT RisingWave / Postgres / Lance / SQLite. The `maps` actor's
  RisingWave backend is explicitly NOT a template.
- **Murakumo-only inference (G7)**: `flowNarrative.murakumoInferenceAttestation`
  is REQUIRED, and its `inferenceSubstrate` is `const: "murakumo"` — a
  vendor-LLM origin (openai / anthropic-direct / vertex / runpod /
  bedrock) is unrepresentable at the schema layer.
- **Source-provenance (G5)**: `fundFlowEdge.sourceRecordCids` and
  `flowNarrative.sourceRecordCids` have `minLength: 2`.
- **Open method (G6)**: every edge + narrative cites a `methodNote` CID;
  no closed aggregation.
- **Aggregate-first + named-element gating (G10)**:
  `visualizationManifest.aggregateOnly` is `const: true` (R0–R2). Named
  elements are `#namedElementRef`, whose `publiclyNamedBasis` +
  `councilReviewCid` + `oneSbtOneVoteChainCid` are ALL required — an
  element cannot render a named party without all three. `fundFlowEdge`
  endpoints are `#endpointRef`; a specific party is named only via
  `publiclyNamedBasis` citing the source record that already names them.
- **kami-engine WASM render-only (G14)**:
  `visualizationManifest.renderSubstrate` is `const: "kami-engine-wasm"` —
  any third-party BI (tableau / powerbi / looker / palantir-foundry) is
  unrepresentable.
- **stateAlignedFlag pass-through (G13)**: CN-class / state-aligned
  source flags propagate into every derived edge / narrative / manifest.
- `additionalProperties: false` at top-level + per-ref nested objects
  (R1 closure step, per the repo-wide convention).

## R0 Status

Schemas at R0 are skeleton-level: known-value enums + required-field
lists + the `const` / `minLength` constitutional anchors are in place.
`fundFlowEdge` (`#endpointRef`), `flowNarrative` (`#murakumoAttestation`),
and `visualizationManifest` (`#namedElementRef`) already carry ref-typed
nested defs; `methodNote` stays flat until R1. `additionalProperties:false`
is the R1 closure step.

## Repo-wide validation (integration coverage)

The 4 kanae lexicons are intended to pass the repo's lexicon lints
(`nsid-lexicon-exists`, `lexicon-primary-types`, `nsid-lexicon-registration`)
and to be guarded by the actor-specific `no-kanae-adjudication.mjs`
(G4 + G7 + G8 + G15) and its regression suite.

## Cross-actor consumers

- **ossekai** (ADR-2605264000): aggregate-anonymized §1.12 publication of `visualizationManifest` artifacts
- **kataribe** (語部, press): kanae visualization artifacts as citable primary-source graphics
- **danjo** (ADR-2605301600): UPSTREAM engine — kanae reads danjo fiscal + `intergov-fund-flow` datoms (read-only); danjo finds, kanae renders

## Related Files

- `/90-docs/adr/2605302300-kanae-global-fiscal-flow-visualization-tier-b-actor-r0.md` — master ADR
- `/90-docs/adr/2605302245-danjo-global-fiscal-flow-extension.md` — danjo engine-side extension
- `/00-contracts/lexicons/com/etzhayyim/danjo/README.md` — upstream engine namespace
- `/00-contracts/lexicons/com/etzhayyim/gov/dataset/README.md` — primary input corpus namespace
- `/20-actors/kanae/` — manifest + README + CLAUDE.md + methods
- `/40-engine/kotoba/crates/kotoba-kotodama/cells/kanae_*/` — cell modules (R0 path-reserved)
