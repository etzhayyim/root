# com.etzhayyim.gov.dataset.* — Open-government-data Lexicons

**ADR**: ADR-2605263900 (R0 scaffold)
**Status**: R0 schema skeletons. Full structural enforcement (const fields, vendor-terminal deny-list at lint, per-jurisdiction publication-rule honoring, CN §2(g) display obligation) lands at W1.

**Namespace boundary**: this `com.etzhayyim.gov.dataset.*` sub-namespace describes religious-corp ingestion of officially-published OPEN-DATA / parliament / budget / procurement / statistics records. It is SEPARATE from the existing `com.etzhayyim.gov.{agency,consult,municipality,official,procedure}` sibling namespace (ADR-2605242330) which catalogs the state's structure for read-side interop. The two share the `gov.*` prefix but cover different concerns:

- `com.etzhayyim.gov.{agency,consult,...}` — **state-side organizational catalog** (who/what the state is)
- `com.etzhayyim.gov.dataset.*` — **state-published data corpora** (what the state has published)

**Owner**: religious-corp substrate (no single actor — written by `kotodama.organism.sensors.gov.*` after passive-only fetch of officially-published bulk archives; consumed by ossekai / toritate / chigiri / manabi / baien-distill).

## 5 Lexicons

| # | Lexicon | Sensor source | Purpose |
|---|---|---|---|
| L1 | `openDatasetAttestation` | `gov_open_data_sensor` | Per-portal catalog entry (data.gov / data.gov.uk / data.gouv.fr / data.go.jp / e-Stat / data.europa.eu / govdata.de / CN portal) |
| L2 | `parliamentRecord` | `gov_parliament_sensor` | Per-legislature debate / vote / bill / member-statement (US Congress.gov / UK Hansard / EU OEIL / JP 国会会議録 / DE Bundestag / FR Assemblée) |
| L3 | `budgetRecord` | `gov_budget_sensor` | Per-jurisdiction appropriation / obligation / outlay / subaward (USAspending / EU FTS / UK Treasury / JP 予算書); LEI cross-link |
| L4 | `procurementRecord` | `gov_procurement_sensor` | Per-jurisdiction tender / award / modification / cancellation (EU TED / US SAM.gov / JP 政府調達 / UK Contracts Finder); LEI cross-link |
| L5 | `statisticsObservation` | `gov_statistics_sensor` | Per-IGO indicator observation (Eurostat / OECD.Stat / WB / IMF / UN data); dimension-preserving |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level + per-ref nested objects.
- Per-jurisdiction publication-rule honoring: parliament transcripts + member-statements + procurement awardees + budget recipients pass-through (transparency-regime reason for publication across W1-W3 jurisdictions).
- GDPR right-to-be-forgotten DSARs route through `chigiri.data_privacy` to upstream publisher; religious-corp NEVER performs unilateral removal.
- `stateAlignedFlag` set true for CN-class sources per §2(g) parallel to ADR-2605262800; downstream consumers (ossekai + manabi) MUST display flag in derived publication.
- Vendor commercial gov-intel terminal deny-list at lint integration: GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro hostnames + SDK imports MUST NOT appear in any sensor module under this namespace.
- Tier-C / Tier-D **CONSTITUTIONALLY PROHIBITED** per Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern.
- Passive-only invariant inherited from ADR-2605262400 §7: no live portal / API hits at organism-tick time; only pre-published bulk archives.

## R0 Status

Schemas at R0 are skeleton-level: known-value enums in place, required-field lists defined, but full ref-typed nested structures (e.g. multi-source recipient resolution, jurisdiction-aware publication-rule matrix, SDMX hierarchical-dimension expansion) land at W1.

## Cross-actor consumers

- **danjo** (ADR-2605301600): PRIMARY cross-reference consumer — ingests parliamentRecord (国会会議録) + budgetRecord (予算書) + procurementRecord (政府調達) into kotoba EAVT and emits NON-adjudicating `discrepancyObservation` + aggregate `oversightReport`. The censor's eye, never the censor's sword (passive-only G3; non-adjudicating G4; observation + publication only G11).
- **ossekai** (ADR-2605264000): aggregate-anonymized publication of state-function-routing-around evidence per Charter §1.12 (consumes `danjo.oversightReport`)
- **toritate** (ADR-2605262900): recipient-vendor cross-reference via budget + procurement (anti-related-party check on tithe-recipient vendor list)
- **chigiri** (ADR-2605262700): Charter §1.12 state-function-routing-around evidence base (covenant / inheritance / withdrawal cite publicly-recorded state procedure as substitution context)
- **manabi**: L4 civic-literacy curriculum primary source (parliament + budget + procurement + statistics)
- **baien-distill**: civic-reasoning specialist artifact (per `recipes/gov/gov-civic-literacy-foundations-r1.toml` + `gov-statistics-foundations-r1.toml`)

## Related Files

- `/90-docs/adr/2605263900-public-data-open-government-ipfs-ingestion.md` — corpus ADR
- `/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/gov/` — sensor Protocols
- `/70-tools/e7m-dataset/src/e7m_dataset/fetchers/{us_data_gov,uk_data_gov_uk,jp_data_go_jp,us_congress_gov,uk_hansard,jp_kokkai_kaigiroku,eu_eurostat,worldbank_open_data}.py` — W1 fetcher stubs
- `/70-tools/baien-moemoekyun-train/recipes/gov/` — corpus recipes
- `../../substrate/datasetPin.json` — cross-link target (`datasetPinAt` field on every gov.dataset lexicon)
- `../agency.json` + `../procedure.json` etc. — **sibling-namespace** (state-side organizational catalog; ADR-2605242330)
