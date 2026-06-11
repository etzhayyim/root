# Jinushi — Global Land & Building Registry

`jinushi.etzhayyim.com` (nanoid: `ln5qr8tw`) — 全世界の土地・建物の登記情報を DID actor として収集・保持・更新する。

## Actor Types (path-based Multi-DID)

| Actor | DID scheme | kind | 説明 |
|---|---|---|---|
| CadastralZone | `did:web:jinushi.etzhayyim.com:zone:{country}:{region}:{code}` | `cadastral_zone` | 登記管轄区 (法務局/County/Land Registry District) |
| LandParcel | `did:web:jinushi.etzhayyim.com:{country}:{region}:{id}` | `land_parcel` | 土地 (筆界ポリゴン, 地目, 面積) |
| Building | `did:web:jinushi.etzhayyim.com:{country}:{region}:{id}` | `building` | 建物 (階数, 用途, 建築年) |
| Owner | `did:web:jinushi.etzhayyim.com:owner:{id}` | `owner` | 所有者 (個人/法人/政府/信託) |
| OwnershipContract | `did:web:jinushi.etzhayyim.com:contract:{id}` | `ownership_contract` | 所有権契約 (移転/売買/賃貸/相続/抵当) |

## Maps 連携 (CRITICAL)

jinushi は maps.etzhayyim.com を Follow し、3 つの reactive pipeline で連携する。

| Pipeline | Trigger | Action |
|---|---|---|
| AdminArea → CadastralZone | `com.etzhayyim.apps.maps.admin_area` commit (admin_level 6-8) | 自治体レベルを自動 CadastralZone 化 |
| Building リンク | `com.etzhayyim.apps.maps.building` commit | 座標近傍の jinushi Building を `maps_building_id` で紐付け |
| 座標解決 | RegisterLandParcel/Building (住所のみ) | maps `place_search` Invoke で lat/lng 自動取得 |

## 収集戦略 (Kyumei-Koji + Murakumo)

全世界 47+ カ国、5 Phase。詳細は `COLLECTION_PLAN.md`。

| Phase | Countries | 手法 | Scale Target |
|---|---|---|---|
| 1 Gold Standard | FRA, NLD, NZL, NOR, GBR, FIN, SWE, BEL | `api` + `open_data` | ~1M parcels |
| 2 Good Coverage | ITA, DEU, POL, AUT, AUS, JPN, KOR, CHL, TWN, SGP | `api` + partial scrape | ~10M parcels |
| 3 Browser Auto | ESP, PRT, IRL, USA, CAN, HKG, ARE, TUR, ZAF, KOR | `browser_automation` | ~50M parcels |
| 4 Emerging | BRA, MEX, COL, IND, IDN, KEN, MYS, PHL, ARG | `browser_automation` + emerging | ~100M parcels |
| 5 Research | CHN, GRC, THA, VNM, RUS, SAU, EGY, NGA | 調査 | research |

### Murakumo + Kyumei-Koji 連携

- **HandleHeartbeat (60s)**: zone/parcel/building/job stats → `AgentChat` (murakumo.etzhayyim.com, qwen3-vl-8b) → coverage gap 分析
- **KyumeiDeclareSources**: geospatial (3600s) + registry (7200s) + authority (86400s) を heartbeat で宣言
- **GatherRegistryData**: 国別ソース一覧 + `AgentChat` で追加ソース発見 + `KyumeiDeclareSources` で宣言
- **結果**: `com.etzhayyim.agent.chat_result` record (async flush via PDS batch-flush → murakumo proxy)

## 分割・統合

- **分筆 (bunpitsu)**: `SubdivideLandParcel` — 親 parcel → N 子 parcel DID、親 status=`subdivided`
- **合筆 (gappitsu)**: `MergeLandParcels` — N parcel → 1 merged parcel DID、元 status=`merged`

## Graph Schema

```
(:CadastralZone {id, did, country, region, zone_code, zone_name, zone_type, maps_node_id, geometry_json, registry_office})
(:LandParcel {id, did, country, region, parcel_number, address, land_use, area_sqm, land_value, lat, lng, geometry_json, zone_id, source, status})
(:Building {id, did, country, region, building_name, building_type, address, floors, total_area_sqm, built_year, land_parcel_id, maps_building_id, lat, lng, status})
(:Owner {id, did, owner_type, name, identifier, country, address, legal_entity_id})
(:OwnershipContract {id, did, contract_type, target_id, target_type, from_owner_id, to_owner_id, price, currency, deed_number, registration_office, effective_date, country, status})
```

## Collection Job Pattern (CRITICAL — 収集系 app 標準)

収集系 app は **Collection Job Record パターン**を標準とする。

```
Collect{Country} command
  → ComAtprotoRepoCreateRecord("collectionJob", {country, source, source_url, format, status:"pending"})
  → AppBskyFeedPost("Phase N {country}: created N collection jobs")
  → PDS pipeline が source_url を async fetch
  → handleComAtprotoSyncSubscribeReposCommit で fetch 済みデータを受信 → DIDCreate + RegisterLandParcel
```

**Record schema** (`collection_job`):
```
{id, country, region, source, source_url, format, status, phase, created_at}
```
- `format`: `geojson_wfs` / `geojson_download` / `csv` / `browser_automation`
- `status`: `pending` → `fetching` → `completed` / `failed`


### PDS Fetch Pipeline

PDS batch-flush が `collection_job` record (status=pending) を検出すると自動実行:

```
collection_job (status:pending) → PDS batch-flush
  → processCollectionJob(source_url, format)
    → fetch(source_url) → parse GeoJSON/CSV
    → comAtprotoRepoCreateRecord(land_parcel) × N (max 100/job)
    → update collection_job (status:completed, parcels_created:N)
    → social announce (AppBskyFeedPost)
```

- `geojson_wfs` / `geojson_download`: GeoJSON features → parcel records (centroid auto-calc)
- `csv`: CSV rows → parcel records (header mapping: parcel_number/address/area_sqm/lat/lng)
- Max 100 parcels per job (timeout 防止)。大量データは pagination/offset で複数 job に分割

## WIT

- Package: `etzhayyim:jinushi@1.0.0`
- Export: `etzhayyim:jinushi/registry@1.0.0`
- Imports: `kotodama:contract/agreement`, `kotodama:div/{materiel,documents,information}`
