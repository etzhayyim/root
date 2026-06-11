# etzhayyim-project-resource-flow — Resource Flow Visualization Platform

resource-flow.etzhayyim.com — 公的団体 **+ 民間法人** の 12 resource class flow を social post で可視化する 2次ソース platform。
民間拡張は `90-docs/adr/0028-resource-flow-private-sector-extension.md` が権威 (gov 限定撤廃、legal-entity DID を source として accept)。

## Implementation status (2026-04-28)

| 層 | 状態 | 実体 |
|---|---|---|
| Worker | LIVE | `worker/` (ADR-0036 Worker-direct, host-sdk subscribeRepos consumer) |
| NSID | 8 | `getSankey` / `listFlows` / `projectFlow` / `registerEmitter` / `getActorLabels` / `detectAnomaly` / `listAnomalies` / `reviewAnomaly` |
| BPMN | 2 | `registerEmitter.bpmn` + `detectAnomaly.bpmn` (timer-start `R/PT24H`, ADR-0046) |
| AppView | sankey + anomaly tabs | `appview/resource-flow-ui-r3s0fl0w/svelte/` — Svelte 5, d3-sankey, `?tab=sankey\|anomaly` URL-state, severity-coloured anomaly table with ACK/DIS/ESC inline review buttons (Phase 15), bulk DID → label via `getActorLabels`, reviewed-state join via `mv_resource_flow_anomaly_review_latest` (Phase 16'): open/closed/any filter, row dimming, Status badge showing last action |
| Graph | 3 vertex + 3 sankey MV | `vertex_resource_flow_{currency,service,personnel}` + `mv_resource_flow_sankey_*` (rebuilt ADR-0074, key on `COALESCE(root_did, source_did)`) |
| Pilot emitters | 1 | `did:web:yadoya.etzhayyim.com` (hospitality cluster, ISIC I5510) |
| Chain profiles | 12 | `did:web:hospitality.etzhayyim.com:actor:chain:*` minted in `vertex_profile` (external RWE; ERC725 root not applicable, stays facade-only) |
| MCP facade | enabled | `APP_MCP_REGISTRY=1` — sankey + listFlows surface as MCP tools |
| ERC725 alignment (ADR-0074) | facade-only | All 3 cluster tables carry `root_did` / `facade_did` / `counterparty_root_did` / `migration_status`. lexicons accept optional `sourceRootDid` / `counterpartyRootDid`. Auth team backfill via `migrate-rw-erc725-root.mjs` once `etzhayyimRootIdentity` contracts for emitters are registered. |
| AppView (Svelte) | scaffold | `appview/resource-flow-ui-r3s0fl0w/svelte/` (Svelte 5 runes + d3-sankey). Worker `assets` binding mounts `./dist` at `/` with SPA fallback. Counterparty labels via `app.bsky.actor.getProfile`. |

## Identity

| Field | Value |
|---|---|
| **Domain** | resource-flow.etzhayyim.com |
| **nanoid** | r3s0fl0w |
| **performerType** | service |
| **Sensitivity** | public |
| **Source Type** | 2次ソース (Follow-based: Country APP + legal-entity + cohort actor の flow records を受信・集約・可視化) |

## Architecture

```
Country APPs (gov-jpn, gov-usa, gov-deu, gov-intl-un, ...)
  │  Write: com.etzhayyim.apps.gov{Cc}.{class}Flow
  │  ATPost: "FY2025 予算配分..."
  │
Legal-entity DIDs (did:web:legal-entity.etzhayyim.com:lei:*, hospitality:actor:*, ...)
  │  Write: com.etzhayyim.apps.resourceFlow.legalEntity{Currency|Personnel|Service}Flow
  │  ATPost: "Q1 revenue ¥X / headcount +Y / room-nights Z..."
  │
  ├─ Follow ─────────────────────────────────┐
  │                                          ▼
  │                              resource-flow.etzhayyim.com
  │                              ├─ ComAtprotoSyncSubscribeRepos()
  │                              │  ├─ flow record 受信
  │                              │  ├─ 集計・Sankey 生成
  │                              │  └─ ATPost (visualization)
  │                              │
  │                              ├─ Heartbeat
  │                              │  ├─ 定期集計 (daily/weekly)
  │                              │  ├─ 異常検知 (急増/急減)
  │                              │  └─ ATPost (insight)
  │                              │
  │                              └─ G() query
  │                                 └─ Sankey / lineage / time-series
  └──────────────────────────────────────────┘
```

## Private-Sector Extension (ADR-0028)

**Source DID scope**: gov (既存) + legal-entity DID (LEI / 国別登記 / path-based sub-actor) + cohort actor (ADR-0027)。

**Pilot cluster**: hospitality (yadoya + minpaku + chain / OTA / property DID)。

**PII invariant (ADR-0018)**:
- `counterpartyDid` は legal-entity DID のみ (個人 DID 禁止)
- 個人顧客 / 個人従業員を参照する flow は `cohortId` + `cohortSize >= 5` を必須とし、小さい cohort は PDS commit pipeline で reject
- 個別 PII (`individualCustomerDid` / `individualEmployeeDid`) は Tier 3 Preferences に保持、本 record には書かない

**Phase 1 Lexicon (民間 3 class, 2026-04-15)**:
- `com.etzhayyim.apps.resourceFlow.legalEntityCurrencyFlow` (revenue / cost / investment / m&a consideration)
- `com.etzhayyim.apps.resourceFlow.legalEntityPersonnelFlow` (hire / retire / transfer / acquisition)
- `com.etzhayyim.apps.resourceFlow.legalEntityServiceFlow` (customers served / room-nights / tickets / transactions)

**Phase 2 Lexicon (残り 9 class)**: goods / real_property / rights / debt / information / trust / energy / natural_resource / crypto_asset を同パターンで追加。

## 12 Resource Class (権威ソース: 90-docs/260323-states-resource-flow-lexicon-design.md)

| Class | Lexicon suffix | 可視化 |
|---|---|---|
| currency | `currency_flow` | Sankey (通貨別), bar chart (省庁別), time-series |
| personnel | `personnel_flow` | Sankey (組織間異動), heatmap (grade別) |
| goods | `goods_flow` | Sankey (調達先), bar chart (goods_class別) |
| real_property | `real_property_flow` | map (地理), bar chart (property_class別) |
| rights | `rights_flow` | timeline (権利付与/失効), treemap (rights_class別) |
| debt | `debt_flow` | stacked area (残高推移), maturity profile |
| service | `service_flow` | Sankey (委託先), bar chart (service_class別) |
| information | `information_flow` | network graph (共有関係) |
| trust | `trust_flow` | score timeline, radar chart |
| energy | `energy_flow` | Sankey (エネルギー源→消費), carbon intensity |
| natural_resource | `natural_resource_flow` | Sankey (資源フロー), sustainability index |
| crypto_asset | `crypto_asset_flow` | timeline (押収/処分), wallet graph |

## Social Post Types

### 1. Flow Digest (daily/weekly ATPost)

```
🏛️ Japan FY2025 Budget Flow Digest (Week 12)

Currency: ¥33.6T allocated (MOF→12 ministries)
  Top: MHLW ¥12.1T | MOD ¥5.4T | MEXT ¥4.2T
Personnel: 342 transfers across 8 ministries
Goods: ¥180B procurement (74% defense)
Debt: ¥1.2T JGB issued (10Y avg yield 0.52%)

Sankey → resource-flow.etzhayyim.com/jpn/2025/w12
```

### 2. Anomaly Alert (threshold-triggered ATPost)

```
⚠️ Unusual flow detected: Japan MOD

Currency outflow +340% vs 30-day avg
¥890B → Mitsubishi Heavy Industries (corp:4010001008772)
Source: 防衛装備庁 調達公告 2025-03-15

Details → resource-flow.etzhayyim.com/alert/3lr...
```

### 3. Cross-Country Comparison (monthly ATPost)

```
🌍 G7 Defense Spending Flow Q1 2025

USA: $220B | JPN: ¥5.4T | GBR: £52B | FRA: €44B
DEU: €52B | ITA: €28B | CAN: C$27B

Top cross-border: USA→JPN ¥890B (FMS)
Top intl org: NATO contributions $1.2B total

Sankey → resource-flow.etzhayyim.com/g7/defense/2025q1
```

### 4. Lineage Trace (on-demand ATPost)

```
💰 Budget Lineage: 国庫→個人 (生活保護費)

国庫 → MOF ¥33.6T
  → MHLW ¥12.1T (社会保障)
    → 都道府県 ¥3.2T (生活保護負担金)
      → 市区町村 ¥2.8T
        → 福祉事務所 → 受給者 (210万世帯)

5 hops | data_source: MOF予算書+MHLW概算要求

Full trace → resource-flow.etzhayyim.com/lineage/3lr...
```

## Data Model (W Protocol Event Stream)

### Write (集計結果の永続化)

```
ComAtprotoRepoCreateRecord("resourceFlowDigest", digestPayload)       → 日次/週次 digest
ComAtprotoRepoCreateRecord("resourceFlowAlert", alertPayload)          → 異常検知アラート
ComAtprotoRepoCreateRecord("resourceFlowSankey", sankeyPayload)        → Sankey diagram data
ComAtprotoRepoCreateRecord("resourceFlowComparison", compPayload)      → cross-country 比較
ComAtprotoRepoCreateRecord("resourceFlowLineageTrace", tracePayload)  → lineage trace 結果
```

### Read (yata SQL)

Country APP が書いた flow records を **直接 SQL query** で集計:

```go
// 日本 FY2025 の全 currency flow を省庁別集計
result, _ := kotodama.G("GovCurrencyFlow").
    Match(kotodama.Eq{"fiscal_year": "2025"}).
    Where("sourceDid", "STARTS WITH", "did:web:gov-jpn.etzhayyim.com").
    Return("destDid", "SUM(amount) AS total").
    GroupBy("destDid").
    OrderBy("total DESC").
    Query()
```

## subscribeRepos collections (kotodama.jsonld)

以下の 2 系統を両方 accept する:

```json
{
  "triggers": {
    "subscribeRepos": {
      "collections": [
        "com.etzhayyim.apps.govJpn.currencyFlow",
        "com.etzhayyim.apps.govUsa.currencyFlow",
        "com.etzhayyim.apps.govDeu.currencyFlow",
        "com.etzhayyim.apps.govIntlUn.currencyFlow",
        "com.etzhayyim.apps.resourceFlow.legalEntityCurrencyFlow",
        "com.etzhayyim.apps.resourceFlow.legalEntityPersonnelFlow",
        "com.etzhayyim.apps.resourceFlow.legalEntityServiceFlow",
        "com.etzhayyim.apps.hospitality.leiBridge",
        "com.etzhayyim.apps.hospitality.ownedBy",
        "app.bsky.actor.profile"
      ]
    }
  }
}
```

**`hospitality.*` と `app.bsky.actor.profile` の受信**: hospitality umbrella project (`hospitality.etzhayyim.com`) が発行する actor profile (`app.bsky.actor.profile`) + lei bridge (`leiBridge`) + 親子関係 (`ownedBy`) を同時 subscribe し、`vertex_actor_profile_meta` / `edge_same_as` / `edge_owned_by` を更新するたびに resource-flow coverage snapshot を再計算する (`mv_hospitality_actor_coverage` — migration 0057 参照)。

## WIT

`etzhayyim:resource-flow@1.0.0` — 集約・可視化 capability

```
60-apps/etzhayyim-project-resource-flow/wit/resource-flow/package.wit
```

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-resource-flow/wasm/etzhayyim-wasm-resource-flow-r3s0fl0w
etzhayyim build --no-check && etzhayyim deploy --no-smoke
```
