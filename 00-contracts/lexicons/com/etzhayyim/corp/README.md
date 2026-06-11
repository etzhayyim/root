# com.etzhayyim.corp.* — Corporate-disclosure Lexicons

**ADR**: ADR-2605263800 (R0 scaffold)
**Status**: R0 schema skeletons. Full structural enforcement (const fields, vendor-terminal deny-list at lint, per-jurisdiction publication-redaction policy) lands at W1.

**Owner**: religious-corp substrate (no single actor — written by `kotodama.organism.sensors.corp.*` after passive-only fetch of officially-published bulk archives; consumed by ossekai / toritate / chigiri / manabi / baien-distill).

## 5 Lexicons

| # | Lexicon | Sensor source | Purpose |
|---|---|---|---|
| L1 | `registryAttestation` | `corp_registry_sensor` | Per-jurisdiction legal-entity registry (SEC EDGAR / EDINET 提出者 / Companies House / SEDAR+ / ASIC / DE / FR) |
| L2 | `disclosureAttestation` | `corp_disclosure_sensor` | Per-jurisdiction periodic financial filing (10-K / 10-Q / 8-K / 有報 / 半期 / 大量保有 / UK statutory accounts) |
| L3 | `leiReference` | `lei_sensor` | GLEIF LEI canonical + relationship (CC0 1.0; cross-jurisdiction key) |
| L4 | `ownershipEdge` | `corp_ownership_sensor` | UBO / parent-subsidiary / control-relationship / officer edges |
| L5 | `filingEvent` | `corp_filing_event_sensor` | Material-event header (8-K class / 大量保有変更); W3 high-cadence hot-path |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level + per-ref nested objects.
- Per-jurisdiction publication-redaction policy honored at sensor layer; `piiRedacted` flag set true on `disclosureAttestation` when policy modified the view.
- Vendor commercial-terminal deny-list at lint integration: Bloomberg Terminal / S&P Capital IQ / Refinitiv Eikon / FactSet / Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro hostnames + SDK imports MUST NOT appear in any sensor module under this namespace.
- Tier-A default; Tier-B (OpenCorporates open-data fork CC-BY-SA) requires `-tierB-` infix on derivative training artifacts per G4 of ADR-2605263800.
- Tier-C / Tier-D **CONSTITUTIONALLY PROHIBITED** per Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern.
- Passive-only invariant inherited from ADR-2605262400 §7: no live registry scraping at organism-tick time; only pre-published bulk archives.

## R0 Status

Schemas at R0 are skeleton-level: known-value enums in place, required-field lists defined, but full ref-typed nested attestation chains (e.g. parent/subsidiary tree depth, GLEIF relationship-record sub-types, EU UBO per-state honoring matrix) land at W1.

## Cross-actor consumers

- **ossekai** (ADR-2605263600): aggregate-anonymized publication via AT Proto `app.bsky.feed.post` membrane
- **toritate** (ADR-2605262900): recipient-vendor cross-reference (corporate-donor LEI lookup + anti-related-party check on vendor disbursement)
- **chigiri** (ADR-2605262700): entity-identity verification before vendor-contract Rider scrutiny + `ipLicenseClaim` recipient validation
- **manabi**: L4 financial-literacy curriculum primary source
- **baien-distill**: financial-literacy specialist artifact training (per `recipes/corp/corp-financial-disclosure-foundations-r1.toml`)

## Related Files

- `/90-docs/adr/2605263800-public-data-corporate-disclosure-ipfs-ingestion.md` — corpus ADR
- `/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/corp/` — sensor Protocols
- `/70-tools/e7m-dataset/src/e7m_dataset/fetchers/{sec_edgar,jp_edinet,uk_companies_house,gleif_lei}.py` — W1 fetcher stubs
- `/70-tools/baien-moemoekyun-train/recipes/corp/` — corpus recipes
- `../substrate/datasetPin.json` — cross-link target (`datasetPinAt` field on every corp lexicon)
