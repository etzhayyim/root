# Oil Supply Chain Global Coverage Plan (Reverse Topological Sort)

## Goal

石油サプライチェーンを **global 100% coverage** できる actor topology を、既存の Mitama T1/T3 actor・`vertex_*` / `edge_*` graph・coverage snapshot 運用に合わせて設計する。

ここでいう 100% は「世界中の全法人・全設備の完全収集」ではなく、次の 4 軸を満たす状態を指す。

1. **Topology completeness**: upstream / midstream / downstream / trading / shipping / regulation の全レイヤを actor と graph で表現できる
2. **Country completeness**: 主要産油・精製・消費・海上輸送ハブ国を global baseline として管理できる
3. **Entity completeness**: 国家・NOC・IOC・refinery・pipeline・terminal・tanker route・pricing hub を first-class vertex として扱える
4. **Operational completeness**: coverage / disruption / sanctions / compliance / flow bottleneck を query できる

## Current State

既存 actor で石油に直接効くのは以下の周辺のみ。

- `bunker`: marine fuel procurement / BDN / sulphur compliance
- `vessel`: tanker / LNG carrier / AIS / voyage
- `port`: tanker port / berth / terminal / port call
- `cargo`: bill of lading / cargo manifest / container
- `marine-insurance`: H&M / P&I / cargo insurance

不足しているのは、石油 supply chain の中核である以下。

- upstream: basin / block / field / well / production / reserves
- midstream: pipeline / pumping station / storage / terminal / LNG liquefaction / regas
- downstream: refinery / unit / product slate / petrochemical / retail
- market: crude grade / benchmark / contract / trader / offtake / sanctions exposure
- state/regulator: ministry / regulator / environmental / customs / strategic reserves

## Dependency DAG

依存は原則として以下の向きで流れる。

`Reference/Authority`
→ `Company/Asset Identity`
→ `Physical Upstream`
→ `Midstream Transport & Storage`
→ `Refining & Petrochemical`
→ `Trading & Allocation`
→ `Shipping & Port Operations`
→ `Downstream Distribution & Retail`
→ `Risk / Compliance / Coverage / Decision`

ただし rollout は **reverse topological sort** で進める。
理由は、下流の観測面・意思決定面・coverage 面を先に定義すると、上流の収集対象と graph contract がぶれにくいから。

## Reverse Topological Rollout Order

### R8. Coverage / Risk / Decision

まず「完成判定」を置く。

- 新規 actor: `oil-coverage`
- 新規 actor: `oil-risk`
- 役割:
  - global coverage snapshot
  - choke point / sanctions / outage / force majeure 監視
  - actor gap detection
  - reverse dependency planning

この層が先に必要な理由:

- 何を集めれば 100% と見なすかを先に定義できる
- 後続 actor の KPI を `coverage.get` 契約で統一できる

### R7. Downstream Distribution / Retail

- 新規 actor: `oil-distribution`
- 新規 actor: `oil-retail`
- 役割:
  - product terminal
  - wholesale rack
  - retail network
  - jet / marine / industrial fuel distribution

理由:

- downstream はユーザ向け需要面に最も近く、最終 product taxonomy を固定できる
- refinery の output schema を先に拘束できる

### R6. Shipping / Port / Marine Interface

既存 actor を拡張して石油 chain に寄せる。

- 既存活用: `vessel`, `port`, `bunker`, `marine-insurance`, `cargo`
- 新規 actor: `oil-shipping`
- 役割:
  - crude tanker / product tanker / LNG / LPG / FSO/FPSO routing
  - STS transfer
  - export terminal / import terminal 結合
  - sanctions / dark fleet / AIS anomaly

理由:

- 海上フローは global oil chain の observability 上の中心
- 既存 actor の再利用率が高い

### R5. Trading / Allocation / Pricing

- 新規 actor: `oil-trading`
- 新規 actor: `oil-pricing`
- 役割:
  - crude grade / product grade
  - benchmark linkage (Brent / WTI / Dubai/Oman)
  - offtake / liftings / cargo allocation
  - trader / counterparty / sanctions / payment risk

理由:

- 下流と海運の両方を join する市場層
- refinery / terminal / vessel を束ねる契約面

### R4. Refining / Petrochemical

- 新規 actor: `oil-refining`
- 新規 actor: `petrochemical`
- 役割:
  - refinery registry
  - CDU / FCC / hydrocracker / coker / reformer
  - throughput / utilization / maintenance outage
  - product yield

理由:

- upstream crude と downstream product を変換する中心ノード
- product taxonomy と facility taxonomy をここで固定

### R3. Midstream Transport / Storage

- 新規 actor: `oil-midstream`
- 新規 actor: `lng-infra`
- 役割:
  - pipeline / segment / compressor / pump station
  - tank farm / cavern / SPR
  - gathering / trunkline / export terminal
  - LNG liquefaction / regasification

理由:

- upstream と refinery / shipping を結ぶ物理 backbone
- edge 設計の中心

### B2. Upstream Production

- 新規 actor: `oil-upstream`
- 新規 actor: `oilfield-services`
- 役割:
  - basin / block / field / well
  - operator / working interest
  - reserves / production / decline / outage
  - offshore / onshore / shale / oil sands

理由:

- source of truth だが、先に下流 contract を決めた方が field data の required shape が明確

### R1. Reference / Authority / Identity

最後に依存の根を整備するのではなく、implementation 的には最初に最低限を seed する。
ただし reverse topo の設計上は最下層のため `R1` と表記する。

- 既存活用: `gov`, `legal-entity` 相当の法人系 graph, `maps`
- 新規 actor: `oil-reference`
- 役割:
  - country / basin / region / benchmark / product code / unit conversion
  - NOC / IOC / trader / regulator canonical DID
  - sanctions list / authority / reporting standard

## Target Actor Set

最小構成は 12 actor。

1. `oil-reference`
2. `oil-upstream`
3. `oilfield-services`
4. `oil-midstream`
5. `lng-infra`
6. `oil-refining`
7. `petrochemical`
8. `oil-trading`
9. `oil-pricing`
10. `oil-shipping`
11. `oil-distribution`
12. `oil-risk`

運用 actor を加えると 14 actor。

13. `oil-coverage`
14. `oil-regulatory`

既存 actor からの再利用 / federation:

- `vessel`
- `port`
- `bunker`
- `cargo`
- `marine-insurance`
- `gov`
- `maps`

## Vertex Design

既存規約に合わせ、まずは domain-oriented の coarse vertex を置き、必要なら P10v2 的に後で分解する。

### Reuse First

既存の `vertex_energy`, `vertex_logistics`, `vertex_finance`, `vertex_commerce`, `vertex_actor`, `vertex_did`, `vertex_domain` を再利用する。

ただし oil chain を first-class queryable にするには、以下の専用 vertex を追加した方がよい。

### New Vertex Tables

- `vertex_oil_country_profile`
  - country_code, role_flags(producer/refiner/importer/exporter/transit), reserve_rank, production_rank
- `vertex_oil_company`
  - did, company_type(NOC/IOC/trader/service/refiner), hq_country, sanctions_status
- `vertex_oil_basin`
  - basin_code, basin_name, country_code, basin_type(onshore/offshore)
- `vertex_oil_block`
  - block_code, basin_code, license_type, operator_did
- `vertex_oil_field`
  - field_code, basin_code, field_type(oil/gas/condensate), operator_did, status
- `vertex_oil_well`
  - api_like_code, field_code, well_type, status
- `vertex_oil_reserve_snapshot`
  - field_code, proved, probable, possible, effective_date
- `vertex_oil_production_snapshot`
  - entity_type(country/basin/field/refinery), entity_key, commodity, volume, unit, as_of
- `vertex_oil_pipeline`
  - pipeline_code, commodity, operator_did, capacity_bpd, length_km, status
- `vertex_oil_terminal`
  - terminal_code, terminal_type(export/import/storage/STS), locode, operator_did, storage_capacity
- `vertex_oil_storage_site`
  - site_code, storage_type(tank/cavern/floating), capacity_barrel, operator_did
- `vertex_lng_facility`
  - facility_code, facility_type(liquefaction/regas), capacity_mtpa, operator_did
- `vertex_refinery`
  - refinery_code, complexity_index, throughput_bpd, operator_did, status
- `vertex_refinery_unit`
  - unit_code, refinery_code, unit_type(CDU/FCC/HCU/Coker/Reformer), capacity_bpd
- `vertex_product_grade`
  - product_code, product_family(crude/gasoline/diesel/jet/fuel-oil/lpg/naphtha), sulfur_band
- `vertex_crude_grade`
  - grade_code, api_gravity, sulfur_pct, benchmark_link
- `vertex_trade_contract`
  - contract_id, contract_type(spot/term/offtake), commodity, incoterm, pricing_basis
- `vertex_oil_cargo`
  - cargo_id, commodity, grade_code, quantity, load_port, discharge_port, laycan
- `vertex_pricing_benchmark`
  - benchmark_code, region, commodity, publisher
- `vertex_price_assessment`
  - benchmark_code, assessed_at, price, currency, unit
- `vertex_sanctions_program`
  - authority, program_code, target_type, status
- `vertex_oil_disruption_event`
  - event_type(outage/attack/leak/closure/sanction/weather), severity, started_at, status
- `vertex_oil_coverage_snapshot`
  - actorDid, bucket, nodeCount, freshness, topCollections, countryCoverage, segmentCoverage

## Edge Design

既存 edge 規約に合うものは再利用し、oil-specific semantics が query 上重要なものだけ追加する。

### Reuse Existing Edges

- `edge_owns`
  - company → asset
- `edge_operates`
  - 必要なら新設せず `edge_governance` / `edge_other` ではなく専用化推奨
- `edge_located_at`
  - asset → port / region / coordinates
- `edge_produces`
  - field/refinery/unit → crude/product
- `edge_contains`
  - basin → block → field → well
- `edge_connects`
  - pipeline → terminal/refinery/field
- `edge_transacts`
  - company/contract/cargo 間
- `edge_requires`
  - regulatory or technical dependency
- `edge_registered_with`
  - company/asset → regulator

### New Edge Tables

- `edge_operates`
  - operator company → asset
- `edge_has_working_interest`
  - company → block/field, with equity_pct
- `edge_feeds`
  - field/storage/terminal → pipeline/refinery/export terminal
- `edge_ships`
  - terminal/refinery/trader → cargo
- `edge_loaded_at`
  - cargo → terminal/port
- `edge_discharged_at`
  - cargo → terminal/port
- `edge_priced_against`
  - contract/cargo/crude_grade/product_grade → pricing_benchmark
- `edge_blends_to`
  - crude/product grade → blended grade
- `edge_refines_to`
  - crude_grade/refinery_unit → product_grade
- `edge_stores`
  - storage site/terminal → crude_grade/product_grade
- `edge_constrained_by`
  - asset/route/company → sanctions program / regulation / disruption
- `edge_insures`
  - insurer / club → vessel / cargo / terminal / refinery
- `edge_flows_to`
  - generic material flow edge with commodity + volume + time bucket

`edge_flows_to` は特に重要で、global chain query の backbone にする。

## Minimal Query Backbone

global coverage の可視化に必要な最小 query は以下。

1. country → company → field → pipeline → terminal → tanker → discharge terminal → refinery → product terminal → market
2. benchmark → crude grade → cargo → route → refinery → product yield
3. sanctions program → company / cargo / vessel / terminal / refinery exposure
4. disruption event → impacted edges / reroute candidates / alternative supply

このため、最初に揃えるべき backbone vertex/edge は次。

- vertex:
  - `vertex_oil_company`
  - `vertex_oil_field`
  - `vertex_oil_pipeline`
  - `vertex_oil_terminal`
  - `vertex_refinery`
  - `vertex_oil_cargo`
  - `vertex_crude_grade`
  - `vertex_product_grade`
  - `vertex_pricing_benchmark`
- edge:
  - `edge_operates`
  - `edge_feeds`
  - `edge_flows_to`
  - `edge_loaded_at`
  - `edge_discharged_at`
  - `edge_priced_against`
  - `edge_constrained_by`

## Coverage Contract

全 oil actor は既存 `gov` や `media-gamers` と同じく `coverage.get` を持つ。

共通 snapshot key:

- `actorDid`
- `actorName`
- `nanoid`
- `bucket`
- `nodeCount`
- `latestSeq`
- `topCollections`
- `countryCoverage`
- `segmentCoverage`
- `freshnessMinutes`

XRPC:

- `com.etzhayyim.apps.<segment>.coverage.get`

cron:

- `0 */6 * * *` で snapshot 更新

## Global 100% Definition by Segment

### Upstream

coverage target:

- top 100 producing countries
- top 500 fields/basins by production or reserves
- all major NOC / supermajor / key independents

### Midstream

coverage target:

- all major cross-border pipelines
- all major export/import terminals
- all major LNG liquefaction / regas facilities
- all strategic petroleum reserve systems

### Downstream

coverage target:

- top 300 refineries by throughput
- top national product terminal systems
- key retail / wholesale networks in G20 + major frontier producers

### Market / Shipping

coverage target:

- all major benchmarks
- all major tanker routes / chokepoints
- all major crude and clean tanker operators
- all major sanctions-sensitive fleets / dark fleet clusters

## Phase Plan

### Phase 0. Graph Backbone

- add new `vertex_*` / `edge_*` table mappings
- add Kysely row types
- add `oil-coverage` actor design

### Phase 1. Coverage First

- implement `oil-coverage`
- define target matrix:
  - country × segment
  - segment × entity-type
  - actor × contract freshness

### Phase 2. Maritime-Market Slice

- implement `oil-shipping`
- extend `vessel` / `port` / `bunker`
- add `vertex_oil_cargo`, `vertex_crude_grade`, `edge_loaded_at`, `edge_discharged_at`

### Phase 3. Refining Slice

- implement `oil-refining`
- add refinery / unit / product grade / refine edges

### Phase 4. Midstream Slice

- implement `oil-midstream`, `lng-infra`
- add pipeline / terminal / storage / flow edges

### Phase 5. Upstream Slice

- implement `oil-upstream`, `oilfield-services`
- add basin / block / field / reserve / production snapshots

### Phase 6. Trading / Pricing / Risk

- implement `oil-trading`, `oil-pricing`, `oil-risk`
- add benchmark / contract / sanctions / disruption graph

### Phase 7. Distribution / Regulatory

- implement `oil-distribution`, `oil-regulatory`
- close the loop from refinery output to national market delivery and compliance

## Why Reverse Topological Sort Is Correct Here

通常の生成順は reference → upstream → downstream だが、この問題は「global coverage を最短で operational にする」ことが目的なので、先に downstream/risk/coverage を置く方が良い。

理由:

- 終端 query が先に決まる
- graph の列設計が先に固まる
- 上流収集の無駄を減らせる
- maritime actor など既存資産を最初に活かせる
- coverage-driven で不足を埋めるループを回せる

## Recommended First Implementation Set

最初の 90 日でやるべき最小セットは次。

1. `oil-coverage`
2. `oil-shipping`
3. `oil-refining`
4. `oil-midstream`
5. `oil-upstream`

この 5 actor と backbone vertex/edge だけで、global oil chain の主要 query はほぼ成立する。

## Implementation Notes

- vertex/edge 追加時は既存 `30-graph/graph-schema/src/helpers.ts` の label / edge mapping に揃える
- actor 側は T1 manifest から入り、`coverage.get` と `coverageSnapshot` を標準搭載する
- country baseline は `gov` と同様に seed actor で管理する
- maritime 系の既存 actor は捨てず、oil chain の federation layer として接続する

## Exit Criteria

完了条件は次の 5 つ。

1. 12-14 actor が全 segment を覆う
2. backbone vertex/edge で end-to-end flow query が通る
3. `oil-coverage` が country × segment の欠損を返せる
4. disruption / sanctions / outage の impact propagation を graph query できる
5. 既存 `vessel` / `port` / `bunker` / `marine-insurance` と join できる
