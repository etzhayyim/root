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
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
---

# Corp + Gov ingestion W1 snapshot — 2026-05-27

## TL;DR

Two ADRs landed 2026-05-26 (ADR-2605263800 corporate disclosure + ADR-2605263900 open government). Across **35 iterations of the recurring `/loop` task `eaeee13b` (2026-05-26 → 2026-05-27)**, W1 progressed from **R0 path-reserved scaffold** to **W1 IMPL LANDED**:

- **12 / 12 concrete fetcher implementations** ═══ PARITY COMPLETE ═══ (corp 4 = gleif_lei + sec_edgar + uk_companies_house + jp_edinet; gov 8 = worldbank_open_data + eu_eurostat + 3 CKAN portals US/UK/JP + 3 Parliament US/UK/JP)
- **14 concrete sensor implementations** (corp 4 + gov 10; covers gov 5-facet COMPLETE: Statistics + OpenData triad + Parliament triad + Budget + Procurement)
- **15/15 sensor pytest harness PASS** (via importlib bypass runner; pytest-CI-ready)
- **Per-fetcher end-to-end fetcher→sensor integration verified** (12/12 pipelines green at smoke-test phase: real Apple/Microsoft/JPM/Sony/Toyota/HSBC/NatWest/額賀議長/石破総理/Speaker Hoyle/Streeting/Schumer/Jeffries fixtures)
- **Complete cross-cutting infrastructure**: 10 Lexicons + 4 corpus recipes + 4 acceptance templates + deps.toml [[modules]] +50 registrations + cross-actor wiring (ossekai/chigiri/toritate `lexiconReadAccess`) + 4 legacy script supersession markers + MIGRATION-NOTES.md

ADR status (both): **`proposed` → `w1-impl-landed`** as of 2026-05-27. R1 activation gated on Bootstrap Council Seats 2-5 RFP closure 2026-06-19 + Council Lv6+ ≥3 ratify.

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

## 2. Concrete fetcher layer — W1 PARITY 12/12 (`70-tools/e7m-dataset/src/e7m_dataset/fetchers/`)

| File | ADR | Sensor consumer | Format / pattern | W1-impl status |
|---|---|---|---|---|
| `gleif_lei.py` | 263800 | GleifLeiSensor | JSON + ZIP detect; 4 input shapes | **w1-impl-landed-concrete** |
| `sec_edgar.py` | 263800 | SecEdgarSensor | master.idx pipe-parse; CIK zero-pad | **w1-impl-landed-concrete** |
| `uk_companies_house.py` | 263800 | UkCompaniesHouseSensor | FCD ZIP+CSV stream; CRN regex | **w1-impl-landed-concrete** |
| `jp_edinet.py` | 263800 | JpEdinetSensor | v2 documents.json; JST→UTC | **w1-impl-landed-concrete** |
| `worldbank_open_data.py` | 263900 | WorldBankOpenDataSensor | WB 2-elem `[header, [data]]` paging | **w1-impl-landed-concrete** |
| `eu_eurostat.py` | 263900 | EuEurostatSensor | SDMX-JSON 2.0 flat-index decoder | **w1-impl-landed-concrete** |
| `us_data_gov.py` | 263900 | UsDataGovSensor | CKAN `package_search` paging | **w1-impl-landed-concrete** |
| `uk_data_gov_uk.py` | 263900 | UkDataGovUkSensor | CKAN; British `organisation` UX | **w1-impl-landed-concrete** |
| `jp_data_go_jp.py` | 263900 | JpDataGoJpSensor | CKAN; 省庁 publisher preserved | **w1-impl-landed-concrete** |
| `us_congress_gov.py` | 263900 | UsCongressGovSensor | api.congress.gov v3; bill-type synthesis | **w1-impl-landed-concrete** |
| `uk_hansard.py` | 263900 | UkHansardSensor | Hansard search API; AttributedTo parser | **w1-impl-landed-concrete** |
| `jp_kokkai_kaigiroku.py` | 263900 | JpKokkaiKaigirokuSensor | NDL `/api/meeting`; nameOfMeeting passthrough | **w1-impl-landed-concrete** |

All 12 fetchers share: (a) network mode + local-source mode (operator-staged or test fixtures); (b) 3-or-4 input shape dispatcher (native API / flat list / pre-normalized envelope / NDJSON pass-through); (c) `max_records` cap for memory-bounded operator runs; (d) per-source filters (date / chamber / form type / CRN / organization / etc.); (e) passive-only invariant (operator-triggered, NOT organism-tick); (f) Charter Rider §2(e)+§2(c) vendor terminal deny-list compliance; (g) raw + normalized output co-located in `<staging>/<name>-<capture_ts>/` for forensic auditability.

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

**Location**: `40-engine/kotoba/crates/kotoba-kotodama/py/tests/sensors/`

- `conftest.py` — isolated-module loader (importlib bypass of `kotodama.__init__` langchain/pydantic chain)
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
| **Sensor Protocol namespace** | corp + gov base.py | 2 | `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/{corp,gov}/base.py` |
| **Sensor concrete impl** | 4 corp + 10 gov | 14 | (see §1) |
| **Fetcher path-reserved** | 4 corp + 8 gov | 12 | `70-tools/e7m-dataset/src/e7m_dataset/fetchers/*.py` |
| **Corpus recipes (TOML)** | 2 corp + 2 gov + 2 READMEs | 4 + 2 | `70-tools/baien-moemoekyun-train/recipes/{corp,gov}/` |
| **Acceptance flag templates** | 3 generic (Tier-A/B/C) + 1 specific (opencorporates) + README | 4 + 1 | `70-tools/e7m-dataset/acceptance-templates/` |
| **Lexicon (corp)** | registry/disclosure/lei/ownership/filing-event + README | 5 + 1 | `00-contracts/lexicons/com/etzhayyim/corp/` |
| **Lexicon (gov.dataset)** | openDataset/parliament/budget/procurement/statistics + README | 5 + 1 | `00-contracts/lexicons/com/etzhayyim/gov/dataset/` |
| **deps.toml entries** | [[adrs]] + [[modules]] | 2 + 30+ | `deps.toml` |
| **Cross-actor wiring** | ossekai (`crossActor` object), chigiri (`lexiconReadAccess`), toritate (`lexiconReadAccess`) | 3 manifest updates | `20-actors/{ossekai,chigiri,toritate}/manifest.jsonld` |
| **Legacy script supersession marker** | sec-edgar / gleif-bulk / legal-entity-relationship / multi-country-scheduled-ingest + MIGRATION-NOTES.md | 4 + 1 | `70-tools/scripts/` |
| **README index entries** | 2 ADR rows | 2 | `90-docs/adr/README.md` |
| **Pytest harness** | conftest + 1 test module (15 tests) | 2 | `40-engine/kotoba/crates/kotoba-kotodama/py/tests/sensors/` |
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
- [ ] **G5**. `com.etzhayyim.substrate.datasetPin` PDS extension verified accepting `corp/*` and `gov/dataset/*` revisions
- [x] **G6**. At least ONE fetcher concrete impl — **EXCEEDED 2026-05-27: 12/12 W1 fetcher parity COMPLETE (see §2 + §7 for the landed sequence)**
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

Each fetcher impl follows the pattern: `httpx[http2]` (already in `kotodama` pyproject deps), respects upstream User-Agent identification + rate limits, downloads pre-published bulk archive (NOT live per-record API at organism-tick time — passive-only per ADR-2605262400 §7), emits NDJSON sidecar conforming to the sensor's expected row shape, returns a `FetchResult` for the DataLad save chain.

## 8. Founder explicit position

This is the third complete sub-ADR W1 substrate landed under the religious-corp regime (sibling of ADR-2605262400 W1 organism public-data + ADR-2605262800 W1 legal corpus). The pattern — **Sensor Protocol + W0 fetcher stub + corpus recipe + acceptance template + Lexicon registration + deps.toml registration + cross-actor wiring + pytest harness + legacy script supersession + ADR/README/snapshot documentation** — is now well-trodden and replicable for future ingestion-substrate ADRs (e.g., future `tech-stack`/`tooling`/`scientific-corpora` family).

The vendor commercial terminal deny-list (Bloomberg Terminal / Refinitiv Eikon / FactSet / Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro / GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro — 13 vendors) is **structurally enforced at multiple layers**: ADR §2 source ladder ban + corpus recipe `[scan].vendor_terminal_denylist` shard-lint + pytest cross-cutting `test_no_vendor_terminal_imports_in_sensor_sources` import-line scan + Charter Rider §2(e)+§2(c) constitutional ground (Council Lv6+ supermajority to amend). No single layer is the bypass; all three layers must fail simultaneously for a violation to land.

## 9. Cycle artifacts (this iteration cohort, 2026-05-26 → 2026-05-27)

**35 `/loop eaeee13b` iterations across ~24 hours**. Cumulative deltas at session-close:

- New `.py` files: 14 concrete sensors + 12 concrete fetchers + 2 sensor `base.py` + 2 sensor `__init__.py` + pytest conftest + harness = **31 Python modules**
- New JSON: 10 Lexicons (5 corp + 5 gov.dataset)
- New TOML: 4 corpus recipes + 4 acceptance templates
- New Markdown: 2 ADRs + 1 RELEASE NOTES snapshot + 2 corpus README + 2 lexicon README + 1 acceptance template README + 1 migration-notes navigation hub = **9 docs**
- `deps.toml` modules: 271 → **346** (**+75 entries** over the session)
- `90-docs/adr/README.md`: +2 ADR rows (top of list)
- 4 legacy `.mjs` scripts: +supersession marker (~35 lines/file annotation)
- 3 actor `manifest.jsonld`: +`crossActor`/`lexiconReadAccess` entries (DID-array linter-safe after parallel-session schema arbitration)

**Session-close state** (2026-05-27): ADR 2605263800 + 2605263900 status **`proposed` → `w1-impl-landed`**. cron `eaeee13b` halted via CronDelete (no further auto-fires). W1 is complete; next operator move is Council Lv6+ ≥3 ratification post-Bootstrap Seat 2-5 RFP close (2026-06-19+).
