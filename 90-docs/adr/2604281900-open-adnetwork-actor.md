---
id: adr-2604281900-open-adnetwork-actor
title: "ADR-2604281900: open-adnetwork — Open Advertising Network Actor (Publisher / Campaign / Impression / Revenue)"
status: active
doc_type: adr
topic: open-adnetwork
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - open-adnetwork actor (Publisher収益化・Advertiser Campaign・Impression/Click/Conversion)
  - BPMN flows: 8 flows (registerPublisher / registerAdvertiser / createCampaign / recordAdUnit / recordImpression / recordConversion / computePublisherRpm / fetchAuctionMarketDelta)
  - Kotoba/Datomic schema: 8 tables + 3 MVs
  - Lexicon contracts: 8 JSON files
related:
  - adr-0056-bpmn-as-actor
  - adr-2604281800-open-smartphone-layer-actors
---

# ADR-2604281900: open-adnetwork — Open Advertising Network Actor

## Context

オープンな広告ネットワークの必要性。Google AdSense/AdWords のような広告配信・収益化インフラを、誰でも自前で運用できるオープンな形で実装する。

Publisher（媒体社）は自分のサイトやアプリに広告枠（Ad Unit）を設置し、Advertiser（広告主）は Campaign を通じて入札する。Impression / Click / Conversion を記録し、RPM（1,000 インプレッション当たり収益）/ CTR（クリック率）/ CVR（コンバージョン率）をリアルタイムで計算する。収益は Publisher に revenue_share_pct（デフォルト 70%）に従って分配する。

BPMN-as-actor（ADR-0056）パターンに従い、CF Worker + Zeebe BPMN + Kotoba/Datomic で構成する。専用 CF Worker は不要（bpmn.etzhayyim.com dispatcher が XRPC 受付）。

## Decision

- **Actor DID**: `did:web:open-adnetwork.etzhayyim.com`
- **Tier**: T1 Actor（ADR-0056 BPMN-as-actor）
- **NSID prefix**: `com.etzhayyim.openAdnetwork.*`
- **Dispatcher**: `http://dispatcher.etzhayyim.com:8080/xrpc/{nsid}`
- **Graph tables**: 8 `vertex_open_adnetwork_*` + 3 `mv_open_adnetwork_*`

## BPMN Flows

| Flow | Trigger | Task types | Description |
|---|---|---|---|
| `registerPublisher` | XRPC (none-start) | db.insert, audit.emit | Publisher（媒体社）を登録し、revenue_share_pct / floor_cpm を設定 |
| `registerAdvertiser` | XRPC (none-start) | db.insert, audit.emit | Advertiser（広告主）を登録し、月次予算 / 支払方法を設定 |
| `createCampaign` | XRPC (none-start) | db.insert, audit.emit | Campaign を作成（objective / bid_strategy / targeting_json）|
| `recordAdUnit` | XRPC (none-start) | db.insert, audit.emit | Ad Unit（広告枠）を Publisher に紐付けて登録 |
| `recordImpression` | XRPC (none-start) | db.insert, audit.emit | Impression イベントを記録（CPM / viewable / country）|
| `recordConversion` | XRPC (none-start) | db.insert, audit.emit | Conversion イベントを記録（type / value_usd）|
| `computePublisherRpm` | Timer R/P1D | db.select, db.insert, audit.emit | 日次 Publisher RPM スナップショットを計算・保存 |
| `fetchAuctionMarketDelta` | Timer R/P7D | http.fetch, audit.emit | IAB 公開ベンチマーク取得（市場 CPM 参照データ）|

## Kotoba/Datomic Schema

### Vertex Tables (8)

| Table | Description |
|---|---|
| `vertex_open_adnetwork_publisher` | Publisher 登録（domain / owner_did / revenue_share_pct / floor_cpm_usd）|
| `vertex_open_adnetwork_advertiser` | Advertiser 登録（brand_name / industry_category / monthly_budget_usd）|
| `vertex_open_adnetwork_campaign` | Campaign（objective / bid_strategy / targeting_json / status）|
| `vertex_open_adnetwork_ad_unit` | Ad Unit（unit_type / size / placement / floor_cpm_usd）|
| `vertex_open_adnetwork_impression` | Impression イベント（cpm_usd / viewable / country_iso2 / ts_ms）|
| `vertex_open_adnetwork_click` | Click イベント（cpc_usd / country_iso2 / ts_ms）|
| `vertex_open_adnetwork_conversion` | Conversion イベント（conv_type / conv_value_usd / ts_ms）|
| `vertex_open_adnetwork_revenue_snapshot` | 日次 Publisher 収益スナップショット（impressions / clicks / conversions / rpm_usd / ctr_pct / cvr_pct）|

### Streaming MVs (3)

| MV | Description |
|---|---|
| `mv_open_adnetwork_campaign_funnel` | Campaign 別ファネル（impressions / clicks / conversions / ctr_pct / cvr_pct / total_spend_usd）|
| `mv_open_adnetwork_publisher_daily_kpi` | Publisher 日次 KPI（revenue_snapshot から射影）|
| `mv_open_adnetwork_market_cpm_range` | Ad Unit タイプ別市場 CPM レンジ（min / avg / max floor_cpm）|

## Consequences

### Positive

- BPMN-as-actor パターンにより CF Worker のデプロイ不要。`vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` への INSERT 2 rows で即 XRPC live。
- RPM / CTR / CVR は MV でリアルタイム計算（< 100ms freshness）。
- revenue_share_pct は Publisher ごとに設定可能（デフォルト 70%）。

### Limitations / Deferred

- **real-time bidding (RTB)**: リアルタイム入札オークションは本 ADR の scope 外。現在は CPM / CPC / CPA の固定 bid_floor のみ。RTB は将来の ADR で対応。
- **`computePublisherRpm` マルチ Publisher INSERT**: `generic.db.insert` は単一行操作のため、SELECT が返す N Publisher 行に対して多重 INSERT はできない（multi-instance subprocess は既存 BPMN アクターに前例なし）。現実装は `publisher_did = '__all__'` の集約スナップショット 1 行を挿入する。個別 Publisher スナップショットは将来の pyzeebe カスタムハンドラで対応。
- **click 記録**: `recordClick` BPMN は本 ADR では省略（impression から click を派生できる）。追加は `vertex_open_adnetwork_click` テーブル + BPMN + lexicon JSON を別 PR で対応。
- **`computePublisherRpm` FEEL aggregate**: `Task_Select` の出力 `publisherStats` は `generic.db.select` が返す row オブジェクトのリスト。`Task_Insert` の FEEL 式 `sum(publisherStats.impressions)` はリスト要素の field 集約で、Zeebe FEEL エンジンで評価される。yoro `platformPulse` BPMN の前例（ADR-2604240946）では同様の FEEL row 抽出が null を返したため、v2 で `yoro.social.platformPulseGraphFallback` カスタム pyzeebe ハンドラに切り替えた。本フローで同様の null 問題が発生した場合は、`openAdnetwork.computePublisherRpm` カスタム pyzeebe ハンドラへの切り替えを検討すること。
- **`vertex_bpmn_process_def` / `vertex_bpmn_lexicon_binding` seed rows**: 本 ADR はスキーマ + BPMN + lexicon のみ。seed INSERT は F5 watcher が BPMN ファイルを自動検出して Zeebe deploy + registry 登録する（ADR-0056 §F5 watcher）。XRPC-triggered BPMN の lexicon_binding は別途 `sync-bpmn-actors.py --apply` で投入。

### ADR-0056 Compliance

- 全 8 BPMN は `generic.*` primitives のみ使用（カスタム pyzeebe task は 0）。
- XRPC-triggered 6 flows は none-start + `bpmn:documentation` に `nsid` + `resultTimeoutMs` を記載。
- Timer-start 2 flows は `R/P1D` / `R/P7D` サイクル。
- `exporterVersion="1.0"` （hand-written、FEEL v1 互換）。
