# Migration notes — corp + gov legacy scripts → religious-corp substrate

**Date**: 2026-05-26
**ADR**: ADR-2605263800 (corp) + ADR-2605263900 (gov)
**Status**: legacy scripts annotated with supersession marker; W4 removal scheduled after sensor parity verification

## Scripts annotated with SUPERSEDED marker

| Legacy script | Lines | New path | New W1 deliverable |
|---|---|---|---|
| `sec-edgar-disclosure-ingest.mjs` | 446 | `70-tools/e7m-dataset/src/e7m_dataset/fetchers/sec_edgar.py` | `CorpRegistrySensor` + `CorpDisclosureSensor` + `CorpFilingEventSensor` |
| `gleif-bulk-ingest.mjs` | 583 | `70-tools/e7m-dataset/src/e7m_dataset/fetchers/gleif_lei.py` | `LeiSensor` (canonical cross-juris key resolver) |
| `legal-entity-relationship-ingest.mjs` | 257 | (consumed by) `corp_ownership_sensor` via `gleif_lei.py` + `opencorporates_opendata.py` (W3) | `CorpOwnershipSensor` (UBO / parent-subsidiary / control-relationship / officer) |
| `multi-country-scheduled-ingest.mjs` | 117 | per-country fetchers (W2): `ca_sedar.py` / `au_asic.py` / `de_unternehmensregister.py` / `fr_rncs_infogreffe.py` + W1/W2 gov fetchers | Multiple sensors per ADR-2605263800 §2 + ADR-2605263900 §2 |

## Why superseded (religious-corp substrate-fit)

| Concern | Legacy script pattern | religious-corp substrate pattern |
|---|---|---|
| Storage | RisingWave + `vertex_*` PG tables | DataLad subdataset + IPFS-pin (per ADR-2605262130 + ADR-2605241500) |
| Lexicon | etzhayyim-side legacy NSID, no Charter Rider provenance | `com.etzhayyim.corp.*` + `com.etzhayyim.gov.dataset.*` records with `datasetPinAt` cross-link |
| Network discipline | Live per-record API hits at cron-tick time | Passive-only per ADR-2605262400 §7: pre-published bulk archives only |
| Vendor scope | Some scripts permitted vendor commercial-terminal imports | Charter Rider §2(e)+§2(c) deny-list: Bloomberg Terminal / Refinitiv / FactSet / Moody's Orbis / D&B / Pitchbook / Crunchbase Pro / GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro **CONSTITUTIONALLY PROHIBITED** |
| Tier discipline | implicit (no tier ladder) | A/B/C/D ladder per ADR-2605262400 §2 + per-source acceptance flag (`70-tools/e7m-dataset/acceptance-templates/`) |
| Inference path | n/a (this layer didn't do inference) | Murakumo-only per ADR-2605215000 (extends to any derivative training artifact via `recipes/corp/` + `recipes/gov/`) |
| State tracking | `/tmp/<source>-state.json` offset bookkeeping | `com.etzhayyim.substrate.datasetPin` PDS records + IPFS revision-content-hash |

## Operator action

1. **For new ingestion**: use the W1 fetcher stubs at `70-tools/e7m-dataset/src/e7m_dataset/fetchers/` once their NotImplementedError stubs are filled in (W1 deliverable).
2. **For data already in RisingWave**: read ADR-2605263800 §7 (W4 deliverable) for the migration plan. No migration tool is committed yet; the W4 deliverable will land it.
3. **Do NOT run any of the 4 annotated scripts on the religious-corp substrate** — they will fail closed (RisingWave RW_CONN is not provisioned) or, if accidentally pointed at a stray PG cluster, will write non-Charter-Rider-compliant records that would need W4 cleanup.

## NOT annotated (out of scope for this iteration)

- `bulk-stream-ingest.mjs` (9908 lines — large multi-domain orchestrator; needs per-domain decomposition before per-stream supersession can land)
- `talent-ingest-cohort-eurostat.mjs` (separate cohort-curation ADR pending)
- `gov/` sub-directory scripts (separate review under ADR-2605242330 vendor-importer-survey gate)

## Related

- `/90-docs/adr/2605263800-public-data-corporate-disclosure-ipfs-ingestion.md` — corpus ADR (corp)
- `/90-docs/adr/2605263900-public-data-open-government-ipfs-ingestion.md` — corpus ADR (gov)
- `/90-docs/adr/2605262400-public-data-organism-ipfs-ingestion.md` — parent pattern (passive-only invariant + DataLad+IPFS)
- `/90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — storage substrate (RW removed from design surface)
- `/CHARTER-RIDER.md` — license + Rider canonical text (§2 vendor commercial-terminal deny-list)
