# etzhayyim-project-pharma

OTC 医薬品通販プラットフォーム (pharma.etzhayyim.com). 薬機法コンプライアンス対応. AI エージェント群が Matrix protocol で連携し仕入→在庫→出荷→配送を全自動化.

## Architecture

- **Runtime**: TS Native + Lexicon Contract
- **Domain**: `pharma.etzhayyim.com`
- **nanoid**: `f0963b54`
- **Static**: static delivery で `svelte/build/` を配信

## CRITICAL: XRPC URL Pattern

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-pharma-xrpc-url-pattern` / MCP `etzhayyim.dodaf.tv1.query`

## AI Agent Architecture (Matrix Protocol)

6 AI エージェントが 5 Matrix ルームで連携:

| Agent | nanoid | 役割 |
|-------|--------|------|
| PharmacistAgent | `pharma-rx01` | 問診レビュー, 第1類承認, 相互作用チェック |
| ProcurementAgent | `pharma-pr01` | 在庫監視, 発注点管理, 自動発注 |
| SupplierAgent | `pharma-sp01` | 卸 API 連携, 見積比較, 納期確認 |
| FulfillmentAgent | `pharma-ff01` | ピッキング, 梱包, 出荷指示 |
| LogisticsAgent | `pharma-lg01` | 配送業者連携, 追跡番号, 配達確認 |
| ComplianceAgent | `pharma-cp01` | 監査, 法改正追跡, レポート |

### Matrix Rooms

| Room | 参加エージェント | 用途 |
|------|------------------|------|
| `#pharma-supply-chain` | 全員 | 統合サプライチェーンイベント |
| `#pharma-procurement` | Procurement, Supplier | 仕入・発注 |
| `#pharma-fulfillment` | Fulfillment, Logistics | 出荷・配送 |
| `#pharma-compliance` | Compliance, Pharmacist | 監査・法令 |
| `#pharma-pharmacist` | Pharmacist | 問診レビュー |

### Order Flow (Agent 連携)

```
注文 → [OTC1?] → PharmacistAgent (問診レビュー)
               → 承認 → Matrix #supply-chain → FulfillmentAgent
                                                ↓ ピッキング・梱包
                                              LogisticsAgent → 配送手配 → 追跡番号
                                                ↓ 配達完了
                                              ComplianceAgent (監査ログ)

在庫 < 発注点 → ProcurementAgent → Matrix #procurement → SupplierAgent
                ↓ 見積比較                                  ↓ 卸API照会
              発注確定 → 入荷 → 在庫加算 → FulfillmentAgent 通知
```

## Compliance (薬機法)

- 第1類医薬品: 薬剤師確認フロー必須 (問診票 → レビュー → 承認)
- 指定第2類: 注意喚起表示必須
- 要指導医薬品: `purchasable: false` でシステムレベルブロック
- 処方箋医薬品: 登録不可
- 購入数量制限: `max_per_order` / `max_per_month` で制御
- 監査ログ: 全コンプライアンスイベントを `pharma_audit_log` に記録

## Kotodama KV Buckets + SQL (11)

| Bucket | 用途 |
|--------|------|
| `pharma-products` | 商品マスタ (分類, 発注点, 数量制限) |
| `pharma-orders` | 注文 |
| `pharma-cart` | カート |
| `pharma-questionnaires` | 問診票 (第1類) |
| `pharma-purchase-history` | 購入履歴 (数量制限追跡) |
| `pharma-audit` | コンプライアンス監査ログ |
| `pharma-consultations` | 薬剤師相談ルーム |
| `pharma-purchase-orders` | 発注書 (仕入) |
| `pharma-shipments` | 出荷 |
| `pharma-agent-activity` | エージェントアクティビティログ |
| `pharma-suppliers` | サプライヤーマスタ |

Write path: `kvPutJSON(bucket, key, value)` → kotodama KV.
Read (by key): `kvGetJSON(bucket, key, &dst)` → kotodama KV.
Read (list/filter): `appSql(stmt, params)` → kotodama SQL WIT.
