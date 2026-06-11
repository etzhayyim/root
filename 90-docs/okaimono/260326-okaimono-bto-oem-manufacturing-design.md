# okaimono BTO/OEM Manufacturing Design

**Status**: `[DESIGN]`
**Date**: 2026-03-26
**Scope**: okaimono.etzhayyim.com + tsukuru.etzhayyim.com integration

## Problem

okaimono.etzhayyim.com は在庫販売 (stock) のみ対応。電化製品やカスタム製品を OEM 工場で受注生産 (BTO/MTO/CTO) し、注文後に製造開始 → 出荷する flow がない。

## Design

### Fulfillment Mode

catalog item に `fulfillment_mode` フィールドを追加:

| Mode | 説明 | 在庫 | 製造トリガー |
|---|---|---|---|
| `stock` | 在庫販売 (default) | 必須 | なし |
| `bto` | Build-to-Order | 0 許容 | 注文確定時 |
| `mto` | Made-to-Order (カスタム仕様) | 0 許容 | 注文確定時 |
| `cto` | Configure-to-Order (定義済みオプション選択) | 0 許容 | 注文確定時 |

### BTO Order Flow

```
Customer → okaimono bto-order-create
  → okaimono_order (fulfillment_mode=bto, status=draft)
  → Checkout SAGA (chk8uty2):
    1. validate-cart
    2. check-product-spec (在庫チェック skip、仕様確認)
    3. process-payment (前払い)
    4. create-production-order → Invoke(tsukr8u0, "create-production-order")
       → tsukuru → factory DID Invoke("manufacture")
    5. confirm-order
    6. await-manufacturing (async)

Factory → tsukuru production_progress events
  → okaimono Subscribe → okaimono_production_progress record
  → customer 通知

Factory → tsukuru quality_inspection
  → okaimono Subscribe → okaimono_quality_result record

Factory → tsukuru production_order (status=shipped)
  → checkout-agent Subscribe → auto fulfillment-create-shipment
  → order status → shipped → delivered
```

### System Integration

```
okaimono.etzhayyim.com ──Follow──→ tsukuru.etzhayyim.com
    │                              │
    │ Invoke("create-production-   │ Invoke(factory_did,
    │        order")               │        "manufacture")
    │                              │
    │ Subscribe:                   │ WRecord:
    │  production_order            │  production_progress
    │  production_progress         │  quality_inspection
    │  quality_inspection          │  production_order
    │                              │
    └──────────────────────────────┘
```

### New Record Kinds

**okaimono domain** (`com.etzhayyim.apps.okaimono.*`):
- `okaimono_production_link` — okaimono order ↔ tsukuru production order mapping
- `okaimono_production_progress` — customer-facing progress (mirrored from tsukuru)
- `okaimono_quality_result` — QC results (mirrored from tsukuru)

**tsukuru domain** (`com.etzhayyim.apps.tsukuru.*`):
- `production_order` — manufacturing order lifecycle
- `production_progress` — factory floor milestone updates
- `quality_inspection` — pre-shipment QC reports

### Checkout SAGA Branching

checkout-agent (`chk8uty2`) が order の `fulfillment_mode` で分岐:

| Step | Stock | BTO/MTO/CTO |
|---|---|---|
| 1 | validate-cart | validate-cart |
| 2 | check-inventory | check-product-spec |
| 3 | reserve-stock | process-payment |
| 4 | process-payment | create-production-order |
| 5 | confirm-order | confirm-order |
| 6 | create-shipment | await-manufacturing |

BTO の補償トランザクション:
- payment 後に production order 失敗 → 自動 refund + order cancel
- production 中の cancel → `cancel-production-order` (pending/accepted/material-procurement のみ)

### WIT Changes

**New**: `etzhayyim:tsukuru-production-order@1.0.0` (3 interfaces: production-order, production-progress, quality-inspection)

**Modified**: `etzhayyim:okaimono@1.0.0` に `manufacturing` interface 追加

**world.wit imports**:
- `okaimono-shopping` → tsukuru manufacturer-registry + factory-registry + production-order + production-progress + quality-inspection
- `okaimono-checkout-agent` → okaimono manufacturing + tsukuru production-order

### Certification Gate

電化製品の BTO では tsukuru の certification 体系で gate:
- PSE (電気用品安全法), 技適 (技術基準適合証明)
- CE marking, UL listing, RoHS, REACH
- `certifications_required` が production order に含まれ、QC inspection で verified

### Commands Added

**okaimono-shopping** (`ok4imn1o`):
- `bto-catalog-upsert` — BTO/MTO catalog item 作成/更新
- `bto-order-create` — BTO 注文作成 (→ tsukuru production order)
- `bto-production-status` — 製造進捗確認
- `bto-list-manufacturers` — OEM 工場一覧 (→ tsukuru search)
- `bto-estimate` — リードタイム/コスト見積もり (→ tsukuru estimate)

## Convo Integration (yoro.etzhayyim.com/convo)

**URL**: `yoro.etzhayyim.com/profile/did:web:tsukr8u0.etzhayyim.com` → メッセージ → `/convo/{convoId}`

ユーザーが tsukuru agent と DM で会話しながら製造プロジェクトを進行。

### Flow

```
User: "スマホを1000台OEMで製造したい"
  → Murakumo LLM + MCP tool calling
  → SearchManufacturers → Foxconn, Pegatron 等の候補提示
  → estimate-lead-time → 35日、¥28,000/台
  → create-production-order → 製造発注
  → ops.CreateProject → プロジェクト管理開始
  → production-progress → リアルタイム進捗通知
  → quality-inspection → QC結果報告
```

### MCP Tools (convo 内で実行可能)

- `tsukuru.SearchManufacturers` — OEM 工場検索
- `tsukuru.create-production-order` — 製造発注
- `tsukuru.estimate-lead-time` — リードタイム見積もり
- `tsukuru.report-production-milestone` — 進捗報告
- `tsukuru.submit-quality-inspection` — 品質検査
- `ops.CreateProject` — プロジェクト作成
- `ops.CreateTask` — タスク追加
- `okaimono.bto-order-create` — BTO 注文作成
