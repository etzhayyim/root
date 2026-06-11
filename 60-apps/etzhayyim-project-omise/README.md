# etzhayyim-project-omise

`omise.etzhayyim.com` 向けの出店者オペレーション UI プロジェクトです。

## MVP Scope (2026-03)

- 出品 3 ステップ: `商品情報 -> 販売条件 -> 公開`
- 受注イベント: `OrderCreated -> FulfillmentRequested -> Shipped -> Delivered`
- DID/VC 連携:
  - `actor_register_did` / `actor_list_did`
  - 出荷更新時に `actor_role + actor_did + signature` を検証してトレース保存
  - `order_event_list` で監査イベント参照

## Targets

- Seller UI: `https://omise.etzhayyim.com/`
- Component: `wasm/omise-seller-ui-component`

## DID Flow Smoke

```bash
cd 60-apps/etzhayyim-project-omise
BASE_URL="https://omise.etzhayyim.com" ORDER_ID="order-..." ./70-tools/70-tools/70-tools/scripts/omise-did-flow.sh
```

このスクリプトは `actor_register_did` → `shipment_create` → `shipment_update_status` → `order_event_list` を順番に実行します。

## Domain Contracts (WIT)

- Export: `etzhayyim:apqc/business-capabilities@0.1.0`
- Export: `etzhayyim:apqc/external-relationships@0.1.0`
- Import: `etzhayyim:isic-m/legal-activities@0.1.0`
- Import: `etzhayyim:isic-m/advertising@0.1.0`
- Import: `etzhayyim:isco/legal-social-cultural-professionals@0.1.0`
