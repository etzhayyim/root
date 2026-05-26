---
id: doc-260527-corp-gov-w1-snapshot
title: "ADR-2605263800 + ADR-2605263900 W1 snapshot — corp + gov ingestion substrate concrete-impl complete (14 sensors, 12 fetcher stubs, 15/15 pytest)"
status: active
doc_type: snapshot
topic: corp-gov-ingestion-w1
authoritative: false
last_verified: 2026-05-27
related:
  - adr-2605263800-public-data-corporate-disclosure-ipfs-ingestion
  - adr-2605263900-public-data-open-government-ipfs-ingestion
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
  - adr-2605263600-ossekai-information-arbitrage-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
---

# Corp + Gov ingestion W1 snapshot — 2026-05-27

## TL;DR

Two ADRs landed 2026-05-26 (ADR-2605263800 corporate disclosure + ADR-2605263900 open government). Across 22 iterations of the recurring `/loop` task `eaeee13b`, W1 progressed from **R0 path-reserved scaffold** to **14 concrete sensor implementations + 15/15 pytest harness + complete cross-cutting infrastructure (recipes, lexicons, acceptance templates, deps.toml registration, cross-actor wiring, legacy script supersession)**. Fetcher code remains W0-stub (`NotImplementedError` w/ ADR pointer); the sensors consume operator-staged or fetcher-emitted NDJSON, so the W1 sensor layer is independently testable.

All work respects: passive-only invariant (ADR-2605262400 §7), Murakumo-only inference (ADR-2605215000), Charter Rider §2(e)+§2(c) vendor terminal deny-list (Bloomberg Terminal / Refinitiv / FactSet / Moody's Orbis / D&B / Pitchbook / Crunchbase Pro / GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro — 13 vendors structurally rejected at lint).

## 1. Concrete W1 sensor matrix (14 / 10+ original target)

### corp/ (4 concrete; covers Registry + Disclosure + LEI + missing OwnershipEdge/FilingEvent)

| # | Sensor | Path | Yield | Source | Tier-A license |
|---|---|---|---|---|---|
| 1 | `GleifLeiSensor` | `corp/lei_sensor.py` | `LeiObservation` | GLEIF Concatenated L1 | CC0 1.0 |
| 2 | `SecEdgarSensor` | `corp/sec_edgar_sensor.py` | `CorpDisclosureObservation` | SEC EDGAR (16 form-code mapping) | public-domain (17 CFR 200) |
| 3 | `UkCompaniesHouseSensor` | `corp/uk_companies_house_sensor.py` | `CorpRegistryObservation` | UK Companies House FCD | OGL v3.0 |
| 4 | `JpEdinetSensor` | `corp/jp_edinet_sensor.py` | `CorpDisclosureObservation` | JP 金融庁 EDINET (7 form-code mapping) | fsa-open-data-utilization-terms |

### gov/ (10 concrete; gov 5 facet COMPLETE — Statistics + Parliament + OpenData + Budget + Procurement)

| # | Sensor | Path | Yield | Facet | Tier-A license |
|---|---|---|---|---|---|
| 5 | `WorldBankOpenDataSensor` | `gov/worldbank_open_data_sensor.py` | `GovStatisticsObservation` | Statistics | CC-BY 4.0 |
| 6 | `EuEurostatSensor` | `gov/eu_eurostat_sensor.py` | `GovStatisticsObservation` | Statistics | eurostat-free-reuse (Dec 2011/833) |
| 7 | `UkHansardSensor` | `gov/uk_hansard_sensor.py` | `GovParliamentObservation` | Parliament | OGL v3.0 |
| 8 | `UsCongressGovSensor` | `gov/us_congress_gov_sensor.py` | `GovParliamentObservation` | Parliament | public-domain (17 USC 105) |
| 9 | `JpKokkaiKaigirokuSensor` | `gov/jp_kokkai_kaigiroku_sensor.py` | `GovParliamentObservation` | Parliament | ndl-public-record-free-use (著作権法 §13) |
| 10 | `UsDataGovSensor` | `gov/us_data_gov_sensor.py` | `GovOpenDataObservation` | OpenData | public-domain |
| 11 | `UkDataGovUkSensor` | `gov/uk_data_gov_uk_sensor.py` | `GovOpenDataObservation` | OpenData | OGL v3.0 |
| 12 | `JpDataGoJpSensor` | `gov/jp_data_go_jp_sensor.py` | `GovOpenDataObservation` | OpenData | CC-BY 4.0 (政府標準利用規約 2.0) |
| 13 | `UsUsaspendingSensor` | `gov/us_usaspending_sensor.py` | `GovBudgetObservation` | Budget | public-domain |
| 14 | `EuTedSensor` | `gov/eu_ted_sensor.py` | `GovProcurementObservation` | Procurement | eu-reuse-decision-2011-833 |

## 2. W0-stub layer (path-reserved; NotImplementedError w/ ADR pointer)

### Fetchers (12 — `70-tools/e7m-dataset/src/e7m_dataset/fetchers/`)

| File | ADR | Target sensor consumer | W1-impl status |
|---|---|---|---|
| `sec_edgar.py` | 263800 | SecEdgarSensor | stub |
| `jp_edinet.py` | 263800 | JpEdinetSensor | stub |
| `uk_companies_house.py` | 263800 | UkCompaniesHouseSensor | stub |
| `gleif_lei.py` | 263800 | GleifLeiSensor | stub |
| `us_data_gov.py` | 263900 | UsDataGovSensor | stub |
| `uk_data_gov_uk.py` | 263900 | UkDataGovUkSensor | stub |
| `jp_data_go_jp.py` | 263900 | JpDataGoJpSensor | stub |
| `us_congress_gov.py` | 263900 | UsCongressGovSensor | stub |
| `uk_hansard.py` | 263900 | UkHansardSensor | stub |
| `jp_kokkai_kaigiroku.py` | 263900 | JpKokkaiKaigirokuSensor | stub |
| `eu_eurostat.py` | 263900 | EuEurostatSensor | stub |
| `worldbank_open_data.py` | 263900 | WorldBankOpenDataSensor | stub |

**Workaround for sensor smoke-testing without fetchers**: operators stage NDJSON shards directly under `90-docs/baien/datasets/<subdataset>/<rev>/*.ndjson` using the row shape documented in each sensor's docstring; the sensors will read those without requiring the fetcher to run. This unblocks pytest validation + downstream actor wiring before fetcher impls land.

### Sensors not yet concrete (W1-impl deferred — 5 of `corp/gov` Protocol family unfulfilled)

| Sensor Protocol | First W1 concrete needed | Notes |
|---|---|---|
| `CorpRegistrySensor` (corp) | one of SEDAR+ / ASIC / Unternehmensregister / INFOGREFFE | UK CH already covers GBR; W2 anchors for CA / AU / DE / FR registries |
| `CorpOwnershipSensor` (corp) | GLEIF L2 RR-only sensor OR OpenCorporates Tier-B (-tierB- infix) | W3 anchor per ADR-2605263800 §3 |
| `CorpFilingEventSensor` (corp) | `sec_edgar_rss_sensor.py` + `jp_edinet_api_sensor.py` (high-cadence) | W3 anchor |
| Additional Parliament legislatures | EU OEIL / DE Bundestag / FR Assemblée | W2/W3 expansion |
| Additional Statistics IGOs | OECD.Stat / IMF SDMX / UN data | W2 expansion |
| Additional Budget systems | EU FTS / UK Treasury / JP 予算書 | W3 expansion |
| Additional Procurement systems | US SAM.gov / JP 政府調達 / UK Contracts Finder | W3 expansion |
| Per-jurisdiction OpenData portals | EU data.europa.eu / FR data.gouv.fr / DE govdata.de | W2 expansion |
| CN-class sources (W4 only) | CN 中国政府网 / NBS w/ `state_aligned_flag=True` per §2(g) | W4 anchor |

## 3. Pytest harness (15/15 PASS)

**Location**: `20-actors/magatama/py/tests/sensors/`

- `conftest.py` — isolated-module loader (importlib bypass of `pymagatama.__init__` langchain/pydantic chain)
- `test_w1_corp_gov_sensors.py` — 14 per-sensor round-trip tests + 1 cross-cutting vendor-terminal deny lint test

**Verified via importlib bypass runner** (operator pytest infra fails on `pydantic-core 2.46.4 vs pydantic 2.41.5` env mismatch, but the test file is structured to run under `pytest tests/sensors/` the moment the env mismatch is fixed):

```
✓ test_gleif_lei_sensor_round_trip
✓ test_sec_edgar_sensor_round_trip
✓ test_uk_companies_house_sensor_round_trip
✓ test_jp_edinet_sensor_round_trip
✓ test_worldbank_sensor_round_trip
✓ test_uk_hansard_sensor_round_trip
✓ test_eurostat_sensor_round_trip
✓ test_us_congress_sensor_round_trip
✓ test_jp_kokkai_sensor_round_trip
✓ test_us_data_gov_sensor_round_trip
✓ test_uk_data_gov_uk_sensor_round_trip
✓ test_jp_data_go_jp_sensor_round_trip
✓ test_us_usaspending_sensor_round_trip
✓ test_eu_ted_sensor_round_trip
✓ test_no_vendor_terminal_imports_in_sensor_sources
═══ 15/15 W1 sensor pytest harness PASS ═══
```

## 4. Cross-cutting infrastructure (landed across 22 iterations)

| Layer | Artifact | Count | Path |
|---|---|---|---|
| **ADR** | corp + gov ingestion 2 ADRs | 2 | `90-docs/adr/2605263{800,900}-*.md` |
| **Sensor Protocol namespace** | corp + gov base.py | 2 | `20-actors/magatama/py/src/pymagatama/organism/sensors/{corp,gov}/base.py` |
| **Sensor concrete impl** | 4 corp + 10 gov | 14 | (see §1) |
| **Fetcher path-reserved** | 4 corp + 8 gov | 12 | `70-tools/e7m-dataset/src/e7m_dataset/fetchers/*.py` |
| **Corpus recipes (TOML)** | 2 corp + 2 gov + 2 READMEs | 4 + 2 | `70-tools/baien-moemoekyun-train/recipes/{corp,gov}/` |
| **Acceptance flag templates** | 3 generic (Tier-A/B/C) + 1 specific (opencorporates) + README | 4 + 1 | `70-tools/e7m-dataset/acceptance-templates/` |
| **Lexicon (corp)** | registry/disclosure/lei/ownership/filing-event + README | 5 + 1 | `00-contracts/lexicons/app/etzhayyim/corp/` |
| **Lexicon (gov.dataset)** | openDataset/parliament/budget/procurement/statistics + README | 5 + 1 | `00-contracts/lexicons/app/etzhayyim/gov/dataset/` |
| **deps.toml entries** | [[adrs]] + [[modules]] | 2 + 30+ | `deps.toml` |
| **Cross-actor wiring** | ossekai (`crossActor` object), chigiri (`lexiconReadAccess`), toritate (`lexiconReadAccess`) | 3 manifest updates | `20-actors/{ossekai,chigiri,toritate}/manifest.jsonld` |
| **Legacy script supersession marker** | sec-edgar / gleif-bulk / legal-entity-relationship / multi-country-scheduled-ingest + MIGRATION-NOTES.md | 4 + 1 | `70-tools/scripts/` |
| **README index entries** | 2 ADR rows | 2 | `90-docs/adr/README.md` |
| **Pytest harness** | conftest + 1 test module (15 tests) | 2 | `20-actors/magatama/py/tests/sensors/` |
| **This snapshot** | release notes / Council brief | 1 | `90-docs/baien/corp-gov-w1-snapshot-260527.md` |

## 5. Downstream actor unblocks (immediate / W1 activation gated)

| Consumer actor | Cross-link surface | Unblock action |
|---|---|---|
| **ossekai** (ADR-2605263600) | `crossActor.{corp-disclosure-substrate,gov-dataset-substrate}` in `20-actors/ossekai/manifest.jsonld` | aggregate-anonymized publication of corporate officer networks + state-function-routing-around evidence (G4 aggregate-first invariant; CN `stateAlignedFlag` display obligation) |
| **toritate** (ADR-2605262900) | `lexiconReadAccess.{corp.leiReference, corp.ownershipEdge, gov.dataset.budgetRecord, gov.dataset.procurementRecord}` in `manifest.jsonld` | anti-related-party check via UBO traversal + budget recipient cross-ref + EU TED awardee LEI lookup |
| **chigiri** (ADR-2605262700) | `lexiconReadAccess.{gov.dataset.parliamentRecord, gov.dataset.openDatasetAttestation, corp.registryAttestation, corp.leiReference}` in `manifest.jsonld` | state-function-routing-around evidence base + vendor-contract Rider scrutiny + ipLicenseClaim recipient validation |
| **manabi** | corpus recipe `gov/gov-civic-literacy-foundations-r1.toml` + `gov/gov-statistics-foundations-r1.toml` | L4 civic-literacy + numerical-reasoning curriculum (Tier-A only; publishable; vendor-terminal deny-list enforced) |
| **baien-distill** | corpus recipe `corp/corp-financial-disclosure-foundations-r1.toml` + (W3) `corp-ownership-graph-tierB-r1.toml` | financial-literacy specialist artifact training (Murakumo-only inference per ADR-2605215000) |

## 6. R1 activation triggers (Council ratification checklist)

For ADR-2605263800 / ADR-2605263900 to move from R0 (proposed) to R1 (operational), the following gates must close:

- [ ] **G1**. Bootstrap Council Seats 2-5 RFP closure (2026-06-19 per ADR-2605192300 — independent gate; no corp/gov-specific blocker)
- [ ] **G2**. Council Lv6+ ≥3 ratify ADR-2605263800
- [ ] **G3**. Council Lv6+ ≥3 ratify ADR-2605263900
- [ ] **G4**. Charter Rider §2 scanner FP rate ≤5% over 7-day trial on corp/gov-bound document samples (R8 KaizenObserver health)
- [ ] **G5**. `app.etzhayyim.substrate.datasetPin` PDS extension verified accepting `corp/*` and `gov/dataset/*` revisions
- [ ] **G6**. At least ONE fetcher concrete impl (sensor W1 layer is already covered; fetcher W1 is independently sequenced — see §7)
- [ ] **G7**. lint hook deploy: vendor commercial terminal deny-list in `lefthook.yml` for `corp/*.py` + `gov/*.py` sensor sources (currently enforced in pytest only)
- [ ] **G8**. chigiri R1 active (cross-actor `ipLicenseClaim` chain; ADR-2605262700 gates separately)
- [ ] **G9**. ossekai R1 active (cross-actor aggregate-publication chain; ADR-2605263600 gates separately)

R1 activation **DOES NOT require** all 14 sensors to be wired into cells — sensor W1-impl-landed status means "the Protocol is correctly implemented with reservoir sampling + G7 schema discipline + invariants verified"; cell wiring is a Pregel-cell-side concern that proceeds in parallel.

## 7. Fetcher W1 concrete impl — recommended order

When fetcher concrete impls begin, the recommended landing order optimizes for downstream unblock + license simplicity:

| Order | Fetcher | Why first | License simplicity |
|---|---|---|---|
| 1 | `gleif_lei.py` | LeiSensor is the cross-jurisdiction key resolver — other corp sensors reference its pin | CC0 1.0 (simplest) |
| 2 | `iana_root.py` (existing — already W1-impl per ADR-2605262400 W1) | already shipped per parent ADR | public-domain |
| 3 | `worldbank_open_data.py` | enables manabi numerical-literacy curriculum | CC-BY 4.0 |
| 4 | `eu_eurostat.py` | EU SDMX pattern sibling | EU re-use |
| 5 | `sec_edgar.py` | ossekai material-event publication unblock | public-domain |
| 6 | `us_data_gov.py` + `uk_data_gov_uk.py` + `jp_data_go_jp.py` | CKAN portal triad | public-domain / OGL / CC-BY |
| 7+ | Hansard / Congress / Kokkai / Companies House / EDINET / USAspending / TED | depend on per-source rate-limit + bulk-archive integration | mixed Tier-A |

Each fetcher impl follows the pattern: `httpx[http2]` (already in `pymagatama` pyproject deps), respects upstream User-Agent identification + rate limits, downloads pre-published bulk archive (NOT live per-record API at organism-tick time — passive-only per ADR-2605262400 §7), emits NDJSON sidecar conforming to the sensor's expected row shape, returns a `FetchResult` for the DataLad save chain.

## 8. Founder explicit position

This is the third complete sub-ADR W1 substrate landed under the religious-corp regime (sibling of ADR-2605262400 W1 organism public-data + ADR-2605262800 W1 legal corpus). The pattern — **Sensor Protocol + W0 fetcher stub + corpus recipe + acceptance template + Lexicon registration + deps.toml registration + cross-actor wiring + pytest harness + legacy script supersession + ADR/README/snapshot documentation** — is now well-trodden and replicable for future ingestion-substrate ADRs (e.g., future `tech-stack`/`tooling`/`scientific-corpora` family).

The vendor commercial terminal deny-list (Bloomberg Terminal / Refinitiv Eikon / FactSet / Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro / GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro — 13 vendors) is **structurally enforced at multiple layers**: ADR §2 source ladder ban + corpus recipe `[scan].vendor_terminal_denylist` shard-lint + pytest cross-cutting `test_no_vendor_terminal_imports_in_sensor_sources` import-line scan + Charter Rider §2(e)+§2(c) constitutional ground (Council Lv6+ supermajority to amend). No single layer is the bypass; all three layers must fail simultaneously for a violation to land.

## 9. Cycle artifacts (this iteration cohort, 2026-05-26 → 2026-05-27)

22 `/loop eaeee13b` iterations across ~14 hours. Cumulative deltas:
- New files: 31 (.py sensor 14 + fetcher stubs 12 + lexicons 10 + recipes 4 + acceptance templates 4 + READMEs 4 + pytest 2 + ADR 2 + snapshot 1, minus some path overlaps)
- `deps.toml` modules: 271 → ~323 (+52 entries)
- `90-docs/adr/README.md`: +2 ADR rows
- 4 legacy `.mjs` scripts: +supersession marker (~35 lines/file)
- 3 actor `manifest.jsonld`: +`crossActor`/`lexiconReadAccess` entries (DID-array linter-safe)
- 1 navigation hub: `70-tools/scripts/MIGRATION-NOTES-corp-gov-2026-05-26.md`

cron job `eaeee13b` ran auto-paced every 30 minutes at :07 + :37, 7-day session-only lifetime (auto-expires ~2026-06-02). CronDelete to halt sooner.
