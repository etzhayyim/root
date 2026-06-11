---
id: adr-2604281830-open-sales-crm-actor
title: "ADR-2604281830: open-sales — Open CRM Actor (Lead / Opportunity / Pipeline / Forecast)"
status: active
doc_type: adr
topic: open-sales
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - open-sales actor (Lead管理・Opportunity・Pipeline・Forecast)
  - BPMN flows: 8 flows (createLead / qualifyLead / updateOpportunity / logActivity / generateQuote / closeDeal / fetchPipelineDelta / computeForecast)
  - Kotoba/Datomic schema: 7 tables + 3 MVs
  - Lexicon contracts: 8 JSON files
related:
  - adr-0056-bpmn-as-actor
  - adr-2604281800-open-smartphone-layer-actors
---

# ADR-2604281830 — open-sales Open CRM Actor

**Status**: active
**Date**: 2026-04-28
**Authors**: Jun Kawasaki + Claude Code

## Context

Salesforce や HubSpot のような営業管理 (CRM) システムは SaaS 契約に縛られており、データのオーナーシップが曖昧である。オープンな CRM actor を etzhayyim プラットフォーム上に構築することで、誰でも自前で Lead → Opportunity → Pipeline → Forecast のフルサイクルを運用でき、データは Kotoba/Datomic + AT Protocol repo に完全に自己管理できる。

ADR-0056 (BPMN-as-actor) パターンに従い、新規 CF Worker を 0 追加せずに BPMN 8 flows として実装する。timer-start BPMNs (fetchPipelineDelta / computeForecast) が定期的なデータ取得と AI 予測を自律的に実行する。

## Decision

### Actor 定義

| 項目 | 値 |
|---|---|
| Actor name | open-sales |
| Domain | `open-sales.etzhayyim.com` |
| DID | `did:web:open-sales.etzhayyim.com` |
| Layer | T1 (BPMN-as-actor, ADR-0056) |
| XRPC endpoint | `dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.openSales.*` |
| New CF Workers | 0 |

### BPMN Inventory — 8 flows

| BPMN | Trigger | Table / Action |
|---|---|---|
| createLead | XRPC | vertex_open_sales_lead |
| qualifyLead | XRPC | vertex_open_sales_lead (update via re-insert) + LLM score |
| updateOpportunity | XRPC | vertex_open_sales_opportunity |
| logActivity | XRPC | vertex_open_sales_activity |
| generateQuote | XRPC | vertex_open_sales_quote + LLM summary |
| closeDeal | XRPC | vertex_open_sales_opportunity (status=won/lost) |
| fetchPipelineDelta | R/P1D timer | audit only (benchmark fetch) |
| computeForecast | R/P7D timer | vertex_open_sales_forecast + LLM forecast |

### Kotoba/Datomic Schema — 7 tables + 3 MVs

#### Vertex Tables

| Table | 主キー概念 | 用途 |
|---|---|---|
| vertex_open_sales_lead | lead_id | 見込み客 (Lead) 管理 |
| vertex_open_sales_contact | contact_id | 連絡先 (Contact) |
| vertex_open_sales_account | account_id | 取引先 (Account/Company) |
| vertex_open_sales_opportunity | opp_id | 商談 (Opportunity) |
| vertex_open_sales_activity | activity_id | 活動ログ (Call/Email/Meeting/Demo) |
| vertex_open_sales_quote | quote_id | 見積書 (Quote) |
| vertex_open_sales_forecast | forecast_id | 売上予測 (Forecast) |

#### Materialized Views

| MV | 用途 |
|---|---|
| mv_open_sales_pipeline_health | ステージ別 pipeline KPI (件数 / 金額 / 加重) |
| mv_open_sales_stage_velocity | ステージ別 win/loss 分析 |
| mv_open_sales_activity_summary | Opportunity 別活動件数集計 |

### Lexicon Contracts — 8 JSON files

| Lexicon NSID | Type | 概要 |
|---|---|---|
| com.etzhayyim.openSales.createLead | procedure | Lead 新規作成 |
| com.etzhayyim.openSales.qualifyLead | procedure | Lead 資格評価 (LLM スコア) |
| com.etzhayyim.openSales.updateOpportunity | procedure | 商談更新 |
| com.etzhayyim.openSales.logActivity | procedure | 活動ログ記録 |
| com.etzhayyim.openSales.generateQuote | procedure | 見積書生成 (LLM サマリ) |
| com.etzhayyim.openSales.closeDeal | procedure | 商談クローズ (won / lost) |
| com.etzhayyim.openSales.listOpportunities | query | 商談一覧取得 |
| com.etzhayyim.openSales.getPipelineHealth | query | Pipeline KPI 取得 |

## Consequences

- 全 8 BPMN が Zeebe に deploy される (F5 watcher 経由, 30s 以内)
- `dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.openSales.*` で XRPC 6 手続きが即座に利用可能
- timer-start 2 flows (fetchPipelineDelta R/P1D, computeForecast R/P7D) が自律的に実行
- LLM (qualifyLead / generateQuote / computeForecast) は `generic.llm.json` primitive 経由で Murakumo fleet を使用
- vertex_open_sales_forecast に AI 予測値 (ai_forecast_usd / confidence_pct) が蓄積される
- 新規 CF Worker は不要 — ADR-0056 の 0-new-worker 制約を満たす
