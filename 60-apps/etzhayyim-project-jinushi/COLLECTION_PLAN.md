# Jinushi Global Collection Plan

全世界の土地・建物登記データを DID actor として収集するフェーズ計画。

## Phase 1: Gold Standard Open Data `[IMPLEMENTED]`

API/Open Data が充実。自動収集可能。**8カ国 collection job 作成済み。**

| # | Country | System | URL | Method | Data | Status |
|---|---|---|---|---|---|---|
| 1 | FRA | Cadastre.data.gouv.fr | cadastre.data.gouv.fr | `open_data` download | 全国 cadastral parcels, buildings (GeoJSON/Shapefile) | job created |
| 2 | NLD | PDOK | pdok.nl | `api` WMS/WFS | Cadastral parcels (DKK), addresses, buildings | job created |
| 3 | NZL | LINZ | data.linz.govt.nz | `api` + download | Property boundaries, ownership, addresses (CC0) | job created |
| 4 | NOR | Kartverket | kartverket.no | `api` WFS | Property register, buildings, addresses (30min lag) | job created |
| 5 | GBR | HM Land Registry | use-land-property-data.service.gov.uk | `api` REST | INSPIRE Index Polygons, Price Paid Data | job created |
| 6 | FIN | Maanmittauslaitos | maanmittauslaitos.fi | `api` WFS + download | Cadastral index map, property boundaries | job created |
| 7 | SWE | Lantmäteriet | lantmateriet.se | `api` WMTS | Property Register, cadastral map (CC0) | job created |
| 8 | BEL | Cadastral Map | finance.belgium.be | `api` WMS/WFS + download | Cadastral parcels, buildings (Shapefile/GeoJSON) | job created |

**Expected yield**: ~100M+ parcels (FRA alone ~36M cadastral sheets)
**DID estimate**: ~50K zone DIDs + seed parcels per country
**Fetch pipeline**: `[IMPLEMENTED]` — PDS batch-flush auto-triggers processCollectionJob

## Phase 2: Good Coverage `[IMPLEMENTED]`

API あり or structured open data あり。一部 scraping 必要。**14 ソース定義済み、zone seeding 129 zones。**

| # | Country | System | Source URL | Method | Zones | Status |
|---|---|---|---|---|---|---|
| 9 | ITA | Agenzia Entrate Catasto | agenziaentrate.gov.it | `api` WFS | 20 regioni | seed + job ready |
| 10 | DEU | ALKIS (州別) | NRW open data + Berlin WFS | `open_data` + `api` WFS | 16 Bundesländer | seed + job ready |
| 11 | POL | EGiB + Geoportal | geoportal.gov.pl | `api` WFS | 16 voivodeships | seed + job ready |
| 12 | AUT | BEV + Grundbuch | bev.gv.at | `api` WFS | 9 Bundesländer | seed + job ready |
| 13 | AUS | State registries (NSW + VIC) | portal.spatial.nsw.gov.au + services.land.vic.gov.au | `api` WFS | 8 states/territories | seed + job ready |
| 14 | JPN | MLIT 国土数値情報 + 地価公示 | nlftp.mlit.go.jp + land.mlit.go.jp | `open_data` + `csv` | 47 prefectures | seed done (47 zones) |
| 15 | KOR | NSDI Parcels | openapi.nsdi.go.kr | `api` WFS | 17 시도 | seed + job ready |
| 16 | CHL | IDE MBN Geoportal | ide.cl | `api` WFS | 16 regions | seed + job ready |
| 17 | TWN | NLSC eMap | maps.nlsc.moi.gov.tw | `api` WFS | 22 counties/cities | seed + job ready |
| 18 | SGP | SLA OneMap | onemap.gov.sg | `api` download | 5 CDC districts | seed + job ready |

**Expected yield**: ~80M parcels
**Zone seeding**: 129 zones across 10 countries (`SeedPhase2AllZones`)
**Fetch pipeline**: `[IMPLEMENTED]` — same PDS processCollectionJob handles P2 sources

### Phase 2 Zone Detail

| Country | Zone Count | Zone Type | Registry Office Pattern |
|---|---|---|---|
| ITA | 20 | regione | `agenzia_entrate_{city}` |
| DEU | 16 | bundesland | `grundbuchamt_{city}` |
| POL | 16 | voivodeship | `egib_{city}` |
| AUT | 9 | bundesland | `vermessungsamt_{city}` |
| AUS | 8 | state_territory | `{name}_land_registry` |
| JPN | 47 | houmukyoku | `{city}_houmukyoku` / `{city}_chihouhoumukyoku` |
| KOR | 17 | metropolitan_province | `{city}_registry_office` |
| CHL | 16 | region | `cbr_{city}` |
| TWN | 22 | county_city | `{city}_land_office` |
| SGP | 5 | cdc_district | `sla_{district}` |

## Phase 3: Browser Automation Required (2-4 weeks)

Online portal あるが API なし。`kotodama:browser/automation` WIT で headless Chromium。

| # | Country | System | URL | Method | Data |
|---|---|---|---|---|---|
| 19 | ESP | Registro de la Propiedad | sede.registradores.org | `browser_automation` | Property rights, mortgages |
| 20 | PRT | Predial Online | predialonline.pt | `browser_automation` | Land registry, property descriptions |
| 21 | IRL | Tailte Éireann | landregistryireland.com | `browser_automation` | Folios, title information |
| 22 | USA | County Assessors (3,100+) | (county-specific) | `browser_automation` + `open_data` | Deeds, titles, assessments |
| 23 | CAN | Provincial (POLARIS/LTSA) | ontario.ca, ltsa.ca | `browser_automation` | Land titles, ownership |
| 24 | HKG | IRIS | iris.gov.hk | `browser_automation` + data.gov.hk | Land register, property addresses |
| 25 | ARE | Dubai Land Dept | dubailand.gov.ae | `api` + `browser_automation` | Real estate transactions, blockchain |
| 26 | TUR | TAKBIS / WebTapu | tkgm.gov.tr | `browser_automation` | ~58M parcels, property registry |
| 27 | ZAF | DeedsWEB | deeds.gov.za | `browser_automation` | Property deeds, ownership |
| 28 | KOR | IROS (追加) | iros.go.kr | `browser_automation` | 登記簿謄本 |

**Expected yield**: ~200M parcels (USA alone ~150M)
**DID estimate**: USA = ~3,100 county zone DIDs + parcels

## Phase 4: Emerging Systems (1-2 months)

デジタル化進行中。部分的カバレッジ。

| # | Country | System | URL | Method | Data |
|---|---|---|---|---|---|
| 29 | BRA | CIB / SICAR | registrodeimoveis.org.br | `browser_automation` + emerging API | Property registration, CAR環境 |
| 30 | MEX | INEGI + Catastro | inegi.org.mx | `open_data` + state | Cadastral data (州別) |
| 31 | COL | IGC | igac.gov.co | `api` portal + blockchain | Cadastral certificates (~30% digital) |
| 32 | IND | Bhulekh + NGDRS | ngdrs.gov.in | `browser_automation` (state) | Land records, khatauni (~95% computerized) |
| 33 | IDN | BPN / BHUMI | bhumi.atrbpn.go.id | `browser_automation` + app | Land locations, plot details |
| 34 | KEN | ArdhiSasa | ardhisasa.lands.go.ke | `api` platform | Land titles, ownership (47 counties rollout) |
| 35 | MYS | CLRS / SPTB | jkptg.gov.my | `browser_automation` | Land titles, cadastral (州別) |
| 36 | PHL | PHILARIS | lra.gov.ph | `browser_automation` | Property titles |
| 37 | ARG | Provincial cadastres | (province-specific) | `browser_automation` | Cadastral parcels |

**Expected yield**: ~300M parcels (IND/BRA/IDN large)

## Phase 5: Research / Limited Access

公開データ極少。調査フェーズ。

| # | Country | Status | Notes |
|---|---|---|---|
| 38 | CHN | No public cadastral data | Government-controlled; investigate via Hong Kong/Macau bridge |
| 39 | GRC | Ktimatologio transitioning 2026 | Unified property register launching |
| 40 | THA | In-person only | Department of Lands; no online system |
| 41 | VNM | Emerging geospatial portal | GDLA; open-source initiatives underway |
| 42 | RUS | Rosreestr | Limited access; sanctions considerations |
| 43 | SAU | Ministry of Justice | Emerging; Vision 2030 digitization |
| 44 | EGY | Real Estate Publicity | Partially digital |
| 45 | NGA | State-based land registries | Lagos pioneering digital |

## Implementation per Phase

### Kyumei-Koji Pipeline (全 Phase 共通)

```
KyumeiDeclareSources(geospatial + registry + authority)
  → KyumeiDiscover(source_url, data_format)
    → KyumeiGather(records[]) → DIDCreate per parcel/building
      → KyumeiValidate(geometry, ownership)
        → KyumeiIntegrate(ComAtprotoRepoCreateRecord + AppBskyFeedPostAs)
```

**Murakumo LLM 連携**: `AgentChat` で coverage gap 分析 + 追加ソース発見。結果は `com.etzhayyim.agent.chat_result` record として永続化。

### Collection Job Pattern (標準) `[IMPLEMENTED]`

```
Collect{Country} command
  → ComAtprotoRepoCreateRecord("collection_job", {country, source, source_url, format, status:"pending", phase:N})
  → AppBskyFeedPost("Phase N {country}: created N collection jobs")
  → PDS batch-flush detects collection_job (status:pending)
  → processCollectionJob: fetch(source_url) → parse GeoJSON/CSV → comAtprotoRepoCreateRecord(land_parcel) × N
  → update collection_job (status:completed, parcels_created:N)
  → social announce
```

**PDS processCollectionJob** (50-infra/cloudflare/workers/atproto/src/index.ts):
- `geojson_wfs` / `geojson_download`: GeoJSON features → land_parcel records (centroid auto-calc from Polygon)
- `csv`: CSV header mapping → land_parcel records
- Max 100 parcels/job (30s timeout)
- Auto status update: `pending` → `fetching` → `completed` / `failed`

### Zone Seeding Strategy

| Phase | Zone Source | Method | Status |
|---|---|---|---|
| 1 | P1 は zone seed なし (collection job のみ) | — | done |
| 2 | 国別 seed command (`SeedItalyZones` 等) | hardcoded admin divisions | `[IMPLEMENTED]` |
| 2 | JPN 47 prefectures (`SeedJapanZones`) | houmukyoku mapping | `[IMPLEMENTED]` |
| 2 | 一括 (`SeedPhase2AllZones`) | 10カ国 129 zones | `[IMPLEMENTED]` |
| 1-2 | maps AdminArea (`SyncZonesFromMaps`) | Invoke maps → auto CadastralZone | ready |
| 3-4 | OSM admin boundaries (Overpass) | maps 経由 Overpass → AdminArea → Zone | planned |

### Heartbeat + Murakumo Analysis `[IMPLEMENTED]`

```
HandleHeartbeat (60s)
  → G() query: zone/parcel/building/job counts
  → AgentChat(stats, "cadastral analyst") → murakumo.etzhayyim.com (qwen3-vl-8b)
  → KyumeiDeclareSources(geospatial + registry + authority)
  → Result: com.etzhayyim.agent.chat_result record (async flush)
```

### DID Naming Convention

```
Zone:     did:web:jinushi.etzhayyim.com:zone:{iso3}:{region}:{code}
Parcel:   did:web:jinushi.etzhayyim.com:{iso3}:{region}:{id}
Building: did:web:jinushi.etzhayyim.com:{iso3}:{region}:{id}
Owner:    did:web:jinushi.etzhayyim.com:owner:{id}
Contract: did:web:jinushi.etzhayyim.com:contract:{id}
```

Country codes: ISO 3166-1 alpha-3 (jpn, gbr, usa, fra, deu, ...)

### Scale Targets

| Phase | Countries | Zones | Parcels | Buildings | Owners |
|---|---|---|---|---|---|
| 1 | 8 | ~5K | ~1M seed | ~500K | — |
| 2 | 10 | ~15K | ~10M | ~5M | — |
| 3 | 12 | ~20K | ~50M | ~20M | ~10M |
| 4 | 9 | ~30K | ~100M | ~50M | ~30M |
| 5 | 8+ | ~35K | research | research | research |
| **Total** | **47+** | **~35K** | **~100M+** | **~50M+** | **~30M+** |

### Current Progress (2026-03-26)

| Metric | Count |
|---|---|
| CadastralZone DIDs | 47 (JPN seed) + 129 (P2 seed ready) |
| LandParcel DIDs | 7 |
| Building DIDs | 1 |
| Owner DIDs | 3 |
| OwnershipContract DIDs | 2 |
| P1 Collection Jobs | 8 |
| P2 Collection Sources | 14 |
| Countries (zone seeded) | 10 (JPN done, 9 ready) |
| Murakumo integration | `[IMPLEMENTED]` (heartbeat + GatherRegistryData) |
| Kyumei-Koji SDK | `[IMPLEMENTED]` (DeclareSources in heartbeat + gather) |
