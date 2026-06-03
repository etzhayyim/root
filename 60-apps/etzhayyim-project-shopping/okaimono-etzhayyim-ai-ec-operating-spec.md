# okaimono.etzhayyim.com AI自動運営EC 実装仕様（MVP）

この仕様は「**販売〜発送〜仕入れ〜CSをAIで閉じる**」運用を前提に、
`okaimono.etzhayyim.com`（`60-apps/etzhayyim-project-shopping`）で最初に実装する最小セットです。

## 1) コア前提

- 人手操作は **エスカレーション時のみ**（異常系、規約違反、監査要件）
- すべての意思決定は `decision_context` を残して監査可能化
- 外部コネクタは最小化（決済/配送/税計算/SMS/メール）
- 画面表示は既存 `cdn/shopping-shopping` を継続し、バックエンドは別MCP/Worker群で分離

## 2) API設計（gRPC/MCP前提）

実運用では XRPC + ConnectRPC の1チャネルに寄せ、RESTは外部連携用アダプタのみに限定。

### 2.1 サービス一覧（最低実装）

```proto
syntax = "proto3";
package okaimono.v1;

service CatalogService {
  rpc GetCatalog (CatalogQuery) returns (CatalogPage);
  rpc UpsertListing (ListingUpsertRequest) returns (ListingSnapshot);
}

service InventoryService {
  rpc ReserveStock (StockReserveRequest) returns (StockReserveResult);
  rpc ConfirmReceipt (StockReceipt) returns (InventoryState);
  rpc GetReorderNeeds (ReorderWindow) returns (ReorderList);
}

service OrderService {
  rpc CreateOrder (CreateOrderRequest) returns (OrderEnvelope);
  rpc GetOrder (OrderLookupRequest) returns (OrderSnapshot);
  rpc UpdateOrderState (OrderStatePatch) returns (OrderSnapshot);
}

service FulfillmentService {
  rpc CreateShipmentPlan (ShipmentPlanRequest) returns (ShipmentPlan);
  rpc RegisterCarrierEvent (CarrierEvent) returns (CarrierEventAck);
}

service ProcurementService {
  rpc FindSupplierOffers (SupplierDemand) returns (SupplierOffers);
  rpc PlacePurchaseOrder (PurchaseOrderCommand) returns (PurchaseOrderReceipt);
  rpc UpdateSupplierStatus (SupplierStatusRequest) returns (SupplierStatusAck);
}

service SupportService {
  rpc CreateCase (CaseCreateRequest) returns (CaseSnapshot);
  rpc PostCaseMessage (CaseMessageRequest) returns (CaseMessageAck);
  rpc CloseCase (CaseCloseRequest) returns (CaseSnapshot);
}

service FinanceService {
  rpc CreateRefund (RefundRequest) returns (RefundReceipt);
  rpc CreatePayout (PayoutRequest) returns (PayoutReceipt);
  rpc GetDailyPnl (PnlRequest) returns (PnlSnapshot);
}

service OrchestratorService {
  rpc ReceiveIntent (CustomerIntent) returns (OrderPlan);
  rpc ValidateDecision (DecisionInput) returns (DecisionResult);
}
```

`okaimono.etzhayyim.com` の公開は以下で統一します。
`POST https://{nanoid}.etzhayyim.com/api/mcp` のみ有効です（`nanoid` は既定 `shop4n1ka`）。
`/api/mcp` 単体の直接叩きは仕様上利用しません。

### 2.2 MCP JSON-RPC（MVP）

`shopping` コンポーネントは以下形式で JSON-RPC を受けます。

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "method": "tools/call",
  "params": {
    "name": "shopping.order_create",
    "arguments": {
      "request_id": "order-create-001",
      "customer_id": "cus-001",
      "items": [{ "product_id": "prd-001", "quantity": 1 }]
    }
  }
}
```

- `method` は `tools/call`（実行）または `tools/list`（tool discovery）を使います。
- `tools/call` は `params.name` に `shopping.*`、`params.arguments` に Tool 引数を渡します。
- `tools/list` の場合は `params` は省略可能で、`shopping.*` 一覧を返却します。

```json
{
  "jsonrpc": "2.0",
  "id": "tools-1",
  "method": "tools/list"
}
```

- `request_id` は副作用系（Create/Update）で必須、読み取り系では不要です。
  再送時は同一 `request_id` の二重実行を抑止します。

### 2.3 外部イベント（NATS/Kafka）

`EventBus` でドメインイベントを連携し、AIエージェントは購読して判断する。

```text
shop.order.created
shop.order.paid
shop.order.shipped
shop.order.refunded
shop.inventory.low_stock
shop.procurement.po_requested
shop.procurement.po_received
shop.support.case_opened
shop.support.case_escalated
shop.finance.payout_requested
shop.decision.approved
shop.decision.rejected
```

### 2.4 idempotency / SAGA

- 全 `Create/Update` 系は `request_id` を必須にする
- 決済→在庫確保→ステータス更新は `order.saga_id` 単位で管理
- 実行境界:
  - `CreateOrder`: 3回まで再試行、重複は `idempotency_key` で抑止
  - `ReserveStock`: 在庫確保のみ先行（未払ならTTS/TTL付きロック）
  - `CreateShipmentPlan`: 決済確定後にのみ実行

## 3) DB スキーマ（PostgreSQL）

```sql
CREATE TYPE order_status AS ENUM ('draft','pending_payment','paid','packed','shipped','delivered','cancelled','refund_pending','refunded');
CREATE TYPE payment_status AS ENUM ('pending','authorized','captured','failed','refunded');
CREATE TYPE case_status AS ENUM ('new','in_progress','waiting_for_customer','awaiting_human','resolved','closed');
CREATE TYPE supplier_status AS ENUM ('idle','sourcing','ordered','shipped','received','cancelled');

CREATE TABLE merchants (
  merchant_id BIGSERIAL PRIMARY KEY,
  legal_name TEXT NOT NULL,
  tax_id TEXT UNIQUE NOT NULL,
  country TEXT NOT NULL DEFAULT 'JP',
  policy_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE products (
  product_id BIGSERIAL PRIMARY KEY,
  merchant_id BIGINT NOT NULL REFERENCES merchants(merchant_id),
  sku TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  cost_jpy NUMERIC(12,2) NOT NULL,
  price_jpy NUMERIC(12,2) NOT NULL,
  tax_rate NUMERIC(5,4) NOT NULL DEFAULT 0.1,
  is_active BOOLEAN NOT NULL DEFAULT true,
  ai_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  description_md TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(merchant_id, sku)
);

CREATE TABLE inventory_locations (
  location_id BIGSERIAL PRIMARY KEY,
  merchant_id BIGINT NOT NULL REFERENCES merchants(merchant_id),
  name TEXT NOT NULL,
  location_type TEXT NOT NULL,
  is_default BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE product_stock (
  stock_id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES products(product_id),
  location_id BIGINT NOT NULL REFERENCES inventory_locations(location_id),
  qty_on_hand INT NOT NULL DEFAULT 0,
  qty_reserved INT NOT NULL DEFAULT 0,
  safety_stock INT NOT NULL DEFAULT 0,
  last_cost_jpy NUMERIC(12,2),
  version BIGINT NOT NULL DEFAULT 1,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(product_id, location_id)
);

CREATE TABLE customers (
  customer_id BIGSERIAL PRIMARY KEY,
  external_customer_ref TEXT NOT NULL UNIQUE,
  email TEXT UNIQUE,
  phone TEXT,
  language TEXT NOT NULL DEFAULT 'ja',
  risk_score SMALLINT NOT NULL DEFAULT 50,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE orders (
  order_id BIGSERIAL PRIMARY KEY,
  merchant_id BIGINT NOT NULL REFERENCES merchants(merchant_id),
  customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
  status order_status NOT NULL DEFAULT 'draft',
  total_amount NUMERIC(12,2) NOT NULL,
  payment_status payment_status NOT NULL DEFAULT 'pending',
  shipping_postal TEXT,
  shipping_addr_md JSONB NOT NULL DEFAULT '{}'::jsonb,
  source_channel TEXT NOT NULL DEFAULT 'web',
  saga_id UUID NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
  order_item_id BIGSERIAL PRIMARY KEY,
  order_id BIGINT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
  product_id BIGINT NOT NULL REFERENCES products(product_id),
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price NUMERIC(12,2) NOT NULL,
  unit_cost NUMERIC(12,2) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE shipments (
  shipment_id BIGSERIAL PRIMARY KEY,
  order_id BIGINT NOT NULL REFERENCES orders(order_id),
  carrier TEXT NOT NULL,
  service_type TEXT NOT NULL,
  tracking_id TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'created',
  planned_at TIMESTAMPTZ,
  shipped_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE suppliers (
  supplier_id BIGSERIAL PRIMARY KEY,
  merchant_id BIGINT NOT NULL REFERENCES merchants(merchant_id),
  name TEXT NOT NULL,
  api_contract TEXT NOT NULL DEFAULT 'manual',
  is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE supplier_purchase_orders (
  po_id BIGSERIAL PRIMARY KEY,
  supplier_id BIGINT NOT NULL REFERENCES suppliers(supplier_id),
  product_id BIGINT NOT NULL REFERENCES products(product_id),
  quantity INT NOT NULL CHECK (quantity > 0),
  status supplier_status NOT NULL DEFAULT 'idle',
  unit_cost NUMERIC(12,2),
  external_po_ref TEXT,
  expected_arrival DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE support_cases (
  case_id BIGSERIAL PRIMARY KEY,
  merchant_id BIGINT NOT NULL REFERENCES merchants(merchant_id),
  order_id BIGINT REFERENCES orders(order_id),
  status case_status NOT NULL DEFAULT 'new',
  channel TEXT NOT NULL DEFAULT 'webchat',
  assigned_agent TEXT,
  escalated_to_human BOOLEAN NOT NULL DEFAULT false,
  root_cause JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ai_decisions (
  decision_id BIGSERIAL PRIMARY KEY,
  domain TEXT NOT NULL,
  actor TEXT NOT NULL,
  decision_ref TEXT NOT NULL,
  request_payload JSONB NOT NULL,
  output_payload JSONB NOT NULL,
  confidence NUMERIC(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  rationale TEXT NOT NULL,
  policy_refs TEXT[] NOT NULL DEFAULT '{}',
  is_approved BOOLEAN NOT NULL DEFAULT false,
  approved_by TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(domain, decision_ref)
);

CREATE INDEX idx_orders_status ON orders(status, updated_at);
CREATE INDEX idx_stock_alert ON product_stock(qty_on_hand, qty_reserved, safety_stock);
CREATE INDEX idx_cases_status ON support_cases(status, updated_at);
CREATE INDEX idx_decisions_domain ON ai_decisions(domain, is_approved, created_at DESC);
```

## 4) AI エージェント設計（最小構成）

### 4.1 エージェント定義

```json
[
  {
    "name": "intent_orchestrator",
    "goal": "顧客チャネル入力を注文意図に変換し、受注フローへ安全に接続する",
    "allowed_tools": ["CatalogService.GetCatalog", "OrderService.CreateOrder", "OrderService.UpdateOrderState", "SupportService.CreateCase"],
    "guardrails": [
      "価格・在庫・配送時間・規約照合は必須",
      "支払失敗率が高い顧客は本人確認追加",
      "高リスク注文は human escalation"
    ],
    "prompt_template": "あなたは受注オーケストレーターです。顧客意図を正規化し、CreateOrderに必要な最小情報(住所/商品/数量/支払い方法)を欠けなく抽出してください。確度不足ならSupportService.CreateCaseでヒアリングに移行してください。"
  },
  {
    "name": "procurement_agent",
    "goal": "仕入需要予測と補充発注を自動実行する",
    "allowed_tools": ["InventoryService.GetReorderNeeds", "ProcurementService.FindSupplierOffers", "ProcurementService.PlacePurchaseOrder", "InventoryService.ConfirmReceipt"],
    "guardrails": [
      "安全在庫を下回るSKUのみ対象",
      "単価が上昇トレンド時は発注サイズを最小化",
      "仕入先応答の整合チェック（最小2重チェック）"
    ],
    "prompt_template": "あなたは仕入れエージェントです。需要予測と現在在庫から欠品リスクを評価し、最安値でなく総コスト（単価+納期遅延リスク）最小の発注を決定してください。"
  },
  {
    "name": "pricing_agent",
    "goal": "粗利最大化を優先しつつ在庫回転率を維持する価格最適化",
    "allowed_tools": ["CatalogService.GetCatalog", "CatalogService.UpsertListing", "OrderService.GetOrder", "ai_decisions"],
    "guardrails": [
      "想定原価以下の価格は許可しない",
      "セール価格は1時間単位で上限回数制限",
      "価格改定イベントは監査ログへ必ず残す"
    ],
    "prompt_template": "あなたは価格エージェントです。過去販売データ、競合帯、在庫回転率を入力として、1SKUあたり1日の最適価格を提案してください。粗利率と需要喪失リスクのトレードオフを明示してください。"
  },
  {
    "name": "fulfillment_agent",
    "goal": "受注完了後の出荷を最適化し、配送遅延を最小化する",
    "allowed_tools": ["FulfillmentService.CreateShipmentPlan", "FulfillmentService.RegisterCarrierEvent", "InventoryService.ConfirmReceipt", "SupportService.CreateCase"],
    "guardrails": [
      "決済未完了状態では出荷計画を作成しない",
      "欠品時は代替SKUまたは代替倉庫を再探索",
      "遅延が閾値超ならEScalation"
    ],
    "prompt_template": "あなたは出荷エージェントです。住所帯別の配送コストと到着精度を比較し、最短かつ欠品リスクが低い配送経路を選定してください。"
  },
  {
    "name": "support_agent",
    "goal": "顧客問い合わせを一次解決し、必要時のみエスカレーションする",
    "allowed_tools": ["SupportService.CreateCase", "SupportService.PostCaseMessage", "OrderService.GetOrder", "FulfillmentService.RegisterCarrierEvent", "FinanceService.CreateRefund"],
    "guardrails": [
      "個人情報回答時は最小提示原則",
      "返品条件外は人間承認を要求",
      "返金実行前に`注文ステータス`と`決済状態`を再確認"
    ],
    "prompt_template": "あなたはCSエージェントです。FAQ適合率、RAG根拠、ルール照合に基づいて先に回答を生成してください。判断不能/高リスクは24時間以内の人間エスカレーションに切り替える。"
  }
]
```

### 4.2 エスカレーション条件（共通）

- 返金・交換の閾値超（例: 1日内3件以上・単独顧客1回あたり高額）
- 決済エラー率が連続3回で異常
- 在庫差分の不一致が5件を超えた場合
- 価格改定が上限閾値を超える場合
- `human_confirm_required = true` が発生した意思決定

## 5) 導入順（12週間）

1. Week 1–2: 商品データの正規化 + Catalog/Inventory/APIコア + 在庫ロック実装
2. Week 3–4: OrderFlow + 決済イベントのSAGA + 監査ログ
3. Week 5–6: Fulfillment + 配送イベントハンドラ
4. Week 7–8: Procurement + 価格最適化Agent + 再補充ループ
5. Week 9–10: CS Agent、返金/交換フロー
6. Week 11–12: 監査KPI（取りこぼし率、取り違い率、平均対応秒、粗利率）を本番監視化

## 6) メトリクス・評価基盤（売上・アクセス起点）

okaimono では、`売上` と `アクセス` を起点に意思決定できる運用サイクルを標準化する。

### 6.1 指標設計（KGI/KPI）

| 種別 | 指標 | 定義 | 計算式 / 取得元 |
|---|---|---|---|
| KGI | 月次売上（GMV） | 対象期間の確定受注金額合計 | `SUM(total_amount)` / `orders.status IN ('paid','shipped','delivered')` |
| KGI | 純売上 | 返金控除後の実質売上 | `SUM(total_amount) - SUM(refund_amount)` |
| KGI | 粗利 | 売上 - 売上原価 - 返品原価 - 出荷費 | `SUM(total_amount - (unit_cost*qty) - shipping_fee - refund_cost)` |
| KPI | セッション数 | 店舗訪問セッション数 | `analytics.pageview` 集計 |
| KPI | ユーザー別PV | 重複排除したユーザー数 | `COUNT(DISTINCT customer_id or anon_id)` |
| KPI | 商品閲覧数 | 商品詳細閲覧イベント数 | `event_name='product_viewed'` |
| KPI | カート投入率 | カート投入/商品閲覧 | `SUM(cart_adds) / SUM(product_views)` |
| KPI | 購入コンバージョン率 | 購入確定/カート投入 | `SUM(orders_paid) / SUM(cart_adds)` |
| KPI | 受注単価（AOV） | 注文1件あたりの平均金額 | `SUM(total_amount)/COUNT(*)` |
| KPI | 欠品率 | 在庫切れ時点で失注した割合 | `SUM(out_of_stock_lost)/SUM(order_attempts)` |
| KPI | 決済失敗率 | 決済失敗/注文試行 | `COUNT(*) FILTER (WHERE payment_status='failed') / COUNT(*)` |
| KPI | webhook処理成功率 | 外部イベント取り込み成功率 | `COUNT(*) FILTER (WHERE event_status='ok') / COUNT(*)` |

### 6.2 KPI判定ルール

- 週次で過去4週移動平均に対する増減を比較
- 以下のアラートを設定
  - 前週比で KPI が `-5%` 以上悪化
  - イベント処理成功率が `99.0%` 未満
  - 決済失敗率が `1.5%` を超過
- 目標値はフェーズごとに再調整（初期例）
  - CVR（購入コンバージョン）: `>= 2.2%`
  - 決済失敗率: `< 1.2%`
  - 欠品率: `< 2.0%`
  - 返品率: `< 3.0%`
  - 粗利率: `>= 32%`

### 6.3 SQL（実装時の集計テンプレート）

#### 6.3.1 売上KPI（営業日別）

```sql
WITH paid_orders AS (
  SELECT
    date_trunc('day', o.created_at) AS day,
    o.order_id,
    o.total_amount,
    COALESCE(o.total_amount - oi_total.cost, 0) AS gross_profit_base
  FROM orders o
  JOIN (
    SELECT
      order_id,
      SUM(unit_price * quantity) AS sales,
      SUM(unit_cost * quantity) AS cost
    FROM order_items
    GROUP BY order_id
  ) oi_total ON oi_total.order_id = o.order_id
  WHERE o.status IN ('paid','shipped','delivered')
)
SELECT
  day,
  COUNT(*) AS paid_orders,
  SUM(total_amount) AS gross_merchandise_value,
  SUM(gross_profit_base) AS gross_profit_like
FROM paid_orders
GROUP BY day
ORDER BY day;
```

#### 6.3.2 ファネル（アクセス→購買）

```sql
SELECT
  date_trunc('day', event_time) AS day,
  COUNT(*) FILTER (WHERE event_name = 'page_view') AS sessions_like,
  COUNT(*) FILTER (WHERE event_name = 'product_viewed') AS product_views,
  COUNT(*) FILTER (WHERE event_name = 'cart_add') AS cart_adds,
  COUNT(*) FILTER (WHERE event_name = 'order_completed') AS orders_completed
FROM analytics_events
WHERE event_time >= now() - interval '14 days'
GROUP BY 1
ORDER BY 1;
```

#### 6.3.3 物流・在庫関連の監視

```sql
SELECT
  date_trunc('day', created_at) AS day,
  COUNT(*) FILTER (WHERE status = 'lost') AS lost_orders,
  COUNT(*) FILTER (WHERE status IN ('ready', 'created')) AS pending_orders,
  AVG(EXTRACT(EPOCH FROM (delivered_at - created_at))/86400) AS avg_days_to_deliver
FROM orders o
LEFT JOIN shipments s ON s.order_id = o.order_id
WHERE created_at >= now() - interval '30 days'
GROUP BY 1
ORDER BY 1;
```

#### 6.3.4 webhook監視

```sql
SELECT
  provider,
  DATE_TRUNC('day', occurred_at) AS day,
  COUNT(*) AS all_events,
  COUNT(*) FILTER (WHERE status = 'ok') AS ok_events,
  ROUND(
    COUNT(*) FILTER (WHERE status = 'ok')::numeric / NULLIF(COUNT(*),0) * 100, 2
  ) AS success_pct
FROM provider_events
WHERE occurred_at >= now() - interval '7 days'
GROUP BY provider, DATE_TRUNC('day', occurred_at)
ORDER BY provider, day;
```

### 6.4 追加分析テーブル（推奨）

```sql
CREATE TABLE analytics_events (
  analytics_event_id BIGSERIAL PRIMARY KEY,
  event_name TEXT NOT NULL,
  channel TEXT NOT NULL DEFAULT 'web',
  customer_id BIGINT,
  anon_id TEXT,
  order_id BIGINT,
  product_id BIGINT,
  provider TEXT,
  event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  attributes JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_analytics_events_time_name
  ON analytics_events(event_time, event_name);
```

`event_name` 例: `page_view`, `product_viewed`, `cart_add`, `order_started`, `order_completed`,
`payment_failed`, `ship_status`, `support_case_opened`

### 6.5 事業評価と改善プロセス（RACI）

- **R（Responsible）**: 実行責任者（通常: オペレーション担当）
- **A（Accountable）**: 最終責任者（事業責任者）
- **C（Consulted）**: AI実装責任者/データ分析/カスタマー
- **I（Informed）**: 取締役/運用監査

| 粒度 | 主要タスク | R | A | C | I |
|---|---|---|---|---|---|
| 日次 | 異常値チェック（決済失敗/欠品/webhookエラー） | 運用SRE | 営業責任者 | AI運用 | 経営/CS |
| 週次 | KPIレビューと施策決定（A/B比較含む） | プロダクト/AI担当 | 事業責任者 | マーケ/在庫/CS | 全体 |
| 月次 | 目標対比、改善施策の承認、評価会議 | 経営補佐 | 事業責任者 | 財務/監査 | 全社 |

### 6.6 改善サイクル（PDCA）

1. **Plan（週次）**: 低下したKPIを1本ずつ仮説化し施策化
2. **Do（実行）**: LP・価格・在庫表示・配送候補・顧客導線を最小変更で試験
3. **Check（検証）**: KPI差分を検定し、`decision_context`に結果と根拠を保存
4. **Act（定着）**: 成果が高い施策を本番化、悪影響施策はロールバック

### 6.7 売上×アクセス起点の運用例（実務フロー）

- **日次で見る最小指標**
  - `純売上`
  - `アクセス（セッション数）`
  - `CVR` = `購入CVR`
  - `AOV` = `純売上 / paid_orders`
- **分解式で原因を見る**
  - `純売上 = セッション数 × CVR × AOV`
  - `CVR低下` は導線（商品閲覧→カート / カート→購入）を疑う
  - `AOV低下` は価格・同梱・送料無料条件を疑う
  - `セッション低下` は流入、LP、JS/API障害を疑う
- **判定とアクションの例**
  - CVRが5日移動平均比で -6% 未満：LP文言、在庫表示、決済導線の1点変更
  - AOVが5日移動平均比で -6% 未満：セット販売比率や送料無料閾値の最小変更を1施策実施
  - `webhook処理成功率 < 99%`：配送/決済連携の再試行・障害ログ確認を優先復旧
- **週次レビュー（30分）**
  - 1) KPI 4本（セッション、CVR、AOV、webhook成功率）
  - 2) 原因仮説を1本だけ選定
  - 3) `shopping.orchestrator_decision` の根拠として `decision_context` に保存

### 6.8 監視クエリ雛形（daily/weekly サマリー）+ アラート条件

#### 日次（`kpi_daily`）

```sql
CREATE OR REPLACE VIEW kpi_daily AS
WITH sales AS (
  SELECT
    date_trunc('day', created_at) AS day,
    COUNT(*) FILTER (WHERE status IN ('paid','shipped','delivered')) AS paid_orders,
    COALESCE(SUM(total_amount) FILTER (WHERE status IN ('paid','shipped','delivered')), 0) AS gmv,
    COALESCE(SUM(refund_amount) FILTER (WHERE status='refunded'), 0) AS refunds
  FROM orders
  WHERE created_at >= now() - interval '30 days'
  GROUP BY day
),
funnel AS (
  SELECT
    date_trunc('day', event_time) AS day,
    COUNT(*) FILTER (WHERE event_name='page_view') AS sessions,
    COUNT(*) FILTER (WHERE event_name='product_viewed') AS product_views,
    COUNT(*) FILTER (WHERE event_name='cart_add') AS cart_adds,
    COUNT(*) FILTER (WHERE event_name='order_completed') AS orders_completed
  FROM analytics_events
  WHERE event_time >= now() - interval '30 days'
  GROUP BY day
),
ops AS (
  SELECT
    date_trunc('day', occurred_at) AS day,
    COUNT(*) FILTER (WHERE status='ok') AS webhook_ok,
    COUNT(*) AS webhook_total
  FROM provider_events
  WHERE occurred_at >= now() - interval '30 days'
  GROUP BY day
),
orders_op AS (
  SELECT
    date_trunc('day', created_at) AS day,
    COUNT(*) AS order_attempts,
    COUNT(*) FILTER (WHERE status='failed') AS payment_failed,
    COUNT(*) FILTER (WHERE status='cancelled' AND failure_reason='out_of_stock') AS out_of_stock_lost
  FROM orders
  WHERE created_at >= now() - interval '30 days'
  GROUP BY day
)
SELECT
  COALESCE(s.day, f.day, o.day, e.day) AS day,
  (COALESCE(s.gmv,0) - COALESCE(s.refunds,0)) AS net_sales,
  COALESCE(s.paid_orders,0) AS paid_orders,
  COALESCE(f.sessions,0) AS sessions,
  COALESCE(f.product_views,0) AS product_views,
  COALESCE(f.cart_adds,0) AS cart_adds,
  COALESCE(f.orders_completed,0) AS orders_completed,
  COALESCE(o.order_attempts,0) AS order_attempts,
  COALESCE(o.payment_failed,0) AS payment_failed,
  COALESCE(o.out_of_stock_lost,0) AS out_of_stock_lost,
  COALESCE(e.webhook_ok,0) AS webhook_ok,
  COALESCE(e.webhook_total,0) AS webhook_total
FROM sales s
FULL JOIN funnel f USING (day)
FULL JOIN orders_op o USING (day)
FULL JOIN ops e USING (day);
```

#### 週次サマリー

```sql
SELECT
  date_trunc('week', day) AS week_start,
  SUM(net_sales) AS net_sales,
  SUM(paid_orders) AS paid_orders,
  SUM(sessions) AS sessions,
  SUM(product_views) AS product_views,
  SUM(cart_adds) AS cart_adds,
  SUM(orders_completed) AS orders_completed,
  ROUND(SUM(orders_completed)::numeric / NULLIF(SUM(cart_adds),0) * 100, 2) AS cvr_pct,
  ROUND(SUM(net_sales)::numeric / NULLIF(SUM(paid_orders),0), 2) AS aov,
  ROUND(SUM(payment_failed)::numeric / NULLIF(SUM(order_attempts),0) * 100, 2) AS payment_failed_rate_pct,
  ROUND(SUM(webhook_ok)::numeric / NULLIF(SUM(webhook_total),0) * 100, 2) AS webhook_success_rate_pct
FROM kpi_daily
GROUP BY week_start
ORDER BY week_start;
```

#### アラート条件（例）

```sql
WITH calc AS (
  SELECT
    day,
    ROUND((orders_completed::numeric / NULLIF(cart_adds, 0)), 6) AS cvr,
    ROUND((net_sales::numeric / NULLIF(paid_orders, 0)), 2) AS aov,
    ROUND((payment_failed::numeric / NULLIF(order_attempts, 0)), 6) AS payment_failed_rate,
    ROUND((out_of_stock_lost::numeric / NULLIF(order_attempts, 0)), 6) AS out_of_stock_rate,
    ROUND((webhook_ok::numeric / NULLIF(webhook_total, 0)), 6) AS webhook_success_rate
  FROM kpi_daily
),
metric_window AS (
  SELECT
    *,
    LAG(cvr,1) OVER (ORDER BY day) AS cvr_prev_week,
    AVG(cvr) OVER (ORDER BY day ROWS BETWEEN 27 PRECEDING AND 1 PRECEDING) AS cvr_ma_28d,
    LAG(payment_failed_rate,1) OVER (ORDER BY day) AS payment_failed_prev_week,
    LAG(webhook_success_rate,1) OVER (ORDER BY day) AS webhook_success_prev_week
  FROM calc
)
SELECT
  day,
  cvr,
  payment_failed_rate,
  webhook_success_rate,
  (cvr_prev_week IS NOT NULL AND (cvr < cvr_prev_week * 0.95 OR (cvr_ma_28d IS NOT NULL AND cvr < cvr_ma_28d * 0.95))) AS alert_cvr_down,
  (payment_failed_rate > 0.012 OR (payment_failed_prev_week > 0.012 AND payment_failed_rate > payment_failed_prev_week * 1.3)) AS alert_payment_fail,
  (webhook_success_rate < 0.99 OR (webhook_success_prev_week IS NOT NULL AND webhook_success_rate < webhook_success_prev_week * 0.98)) AS alert_webhook_quality
FROM metric_window
WHERE day >= now() - interval '30 days'
ORDER BY day DESC;
```

運用初期のアラート閾値は README と同一（`CVR前週/4週移動平均-5%`, `payment_failed_rate >1.2%`, `webhook_success_rate <99%`）。

---
