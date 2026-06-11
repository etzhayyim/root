---
id: 260407-stripe-issuing-oem-payment
title: "Stripe Issuing Card — OEM/BTO Payment Integration"
status: active
doc_type: explanation
topic: stripe-issuing-oem-payment
authoritative: true
last_verified: 2026-04-07
---

# Stripe Issuing Card — OEM/BTO Payment Integration

**Status**: `[DESIGN]`
**Date**: 2026-04-07
**Scope**: okaimono.etzhayyim.com + tsukuru.etzhayyim.com + stripe.etzhayyim.com 統合

## Problem

okaimono BTO checkout SAGA の `process-payment` ステップが汎用的で、決済手段が未定義。stripe.etzhayyim.com は Murakumo credit-backed Stripe Issuing card を既に実装済みだが、tsukuru OEM 製造発注の決済フローに接続されていない。

## Decision

**全 OEM/BTO 決済を Stripe Issuing virtual card 経由に統一する。** Murakumo クレジット → per-order virtual card → OEM 工場支払い → settlement の single path。

## Design

### Payment Model: Per-Order Virtual Card

OEM 発注ごとに **dedicated virtual card** を発行し、production order にバインドする。card lifetime = production order lifetime。

```
Customer (Murakumo credits)
  → assignCardCredits (user pool → card allocation)
    → Stripe Issuing virtual card (per production order)
      → OEM factory payment (authorization at order creation)
        → settlement on delivery confirmation
```

**理由**: per-order card は (1) 支出を production order 単位で完全分離、(2) order cancel 時に card cancel で即座に残高返却、(3) 不正利用リスクを order scope に封じ込め。

### Revised Checkout SAGA (BTO)

```
Checkout SAGA (chk8uty2) — BTO/MTO/CTO mode:

1. validate-cart
   → product_spec + fulfillment_mode 検証

2. check-product-spec
   → tsukuru estimate-lead-time (cost_estimate_jpy 取得)
   → manufacturer certification + trade compliance チェック

3. stripe-issue-payment-card          ← NEW
   → Invoke(st4rp301, "issueCard", {
       userId: customer_did,
       cardType: "virtual",
       currency: "jpy",
       spendingLimitAmount: cost_estimate_jpy,
       spendingLimitInterval: "all-time",
       metadata: {
         productionOrderRef: okaimono_order_id,
         manufacturerDid: manufacturer_did,
         fulfillmentMode: "bto"
       }
     })
   → card_id, stripe_card_id 取得

4. stripe-allocate-credits            ← NEW
   → Invoke(st4rp301, "assignCardCredits", {
       userId: customer_did,
       cardId: card_id,
       amount: cost_estimate_jpy
     })
   → credits.etzhayyim.com CheckSpendAllowed → SpendCredits
   → Murakumo credit debit (user pool → card allocation)

5. create-production-order
   → Invoke(tsukr8u0, "create-production-order", {
       ...,
       payment: {
         method: "stripe_issuing",
         cardId: card_id,
         stripeCardId: stripe_card_id,
         authorizedAmount: cost_estimate_jpy,
         currency: "jpy"
       }
     })
   → production_order_id 取得

6. confirm-order
   → okaimono order status: paid → manufacturing
   → payment_record 作成 (card_id + production_order_id link)

7. await-manufacturing (async)
   → production progress → QC → shipment → delivery
```

### Compensation Transactions

| 失敗ステップ | 補償 |
|---|---|
| `stripe-issue-payment-card` 失敗 | order cancel。card 未発行のため credit 返却不要 |
| `stripe-allocate-credits` 失敗 (残高不足) | card cancel (`Invoke(st4rp301, "cancelCard")`) → order cancel |
| `create-production-order` 失敗 | credit return (`Invoke(credits_did, "EarnCredits", {source: "stripe_refund"})`) → card cancel → order cancel |
| Production cancel (pending/accepted/material-procurement) | `cancel-production-order` → credit return → card cancel → order refund |
| Production cancel 不可 (in-production 以降) | cancel 不可。delivery まで card active 維持 |

### Settlement Flow (Delivery Confirmation)

```
Factory → tsukuru production_order (status=delivered)
  → okaimono Subscribe → order status: delivered
    → stripe card settlement:
      1. Final authorization amount = actual_cost_jpy
         (cost_estimate_jpy と actual_cost_jpy の差額がある場合)
      2. If actual < estimated:
         → excess credit return to user pool
         → update spending limit to actual
      3. Card freeze (no further charges)
      4. 30-day hold → card cancel (dispute window)
```

### Record Kinds (New)

**okaimono domain** (`com.etzhayyim.apps.okaimono.*`):

| Record | Purpose |
|---|---|
| `paymentCard` | Per-order virtual card link (card_id, stripe_card_id, production_order_id, amount, status) |
| `paymentSettlement` | Settlement confirmation (actual_amount, excess_refund, settled_at) |

**stripe domain** (`com.etzhayyim.apps.stripe.*`):
既存の `issuedCard`, `authorization`, `cardCreditAllocation`, `cardCreditConsumption` をそのまま使用。追加 record 不要。

### WIT Changes

**Modified**: `etzhayyim:okaimono@1.0.0` — `orders` interface に payment fields 追加:

```wit
/// Order payment info (Stripe Issuing card binding)
/// create-order params に payment section 追加:
///   payment: {
///     method: "stripe_issuing",
///     cardId: string,          // stripe.etzhayyim.com internal card ID
///     stripeCardId: string,    // Stripe API card token
///     authorizedAmount: u64,   // JPY minor units
///     currency: "jpy"
///   }
```

**Modified**: `etzhayyim:tsukuru-production-order@1.0.0` — `create-production-order` params に payment section 追加:

```wit
/// create-production-order params に payment section 追加:
///   payment: {
///     method: "stripe_issuing",
///     cardId: string,
///     stripeCardId: string,
///     authorizedAmount: u64,
///     currency: "jpy"
///   }
```

**No new WIT packages required.** 既存の `etzhayyim:stripe@1.0.0` card-issuing interface を okaimono checkout agent が Invoke で呼ぶ。

### Cross-Project Integration

```
okaimono (chk8uty2) ──Invoke──→ stripe (st4rp301)
    │                              │
    │ issueCard                    │ Stripe API: POST /issuing/cards
    │ assignCardCredits            │ credits MCP: SpendCredits
    │ cancelCard (compensation)    │ Stripe API: POST /issuing/cards/{id}/cancel
    │                              │
    │                              │
    ├──Invoke──→ tsukuru (tsukr8u0)
    │              │
    │              │ create-production-order (with payment.cardId)
    │              │ cancel-production-order
    │              │
    │              │
    ├──Subscribe──→ tsukuru production_order (status changes)
    │              │
    │              └──→ settlement trigger on delivered
    │
    └──Invoke──→ credits (credits MCP)
                   │
                   │ CheckSpendAllowed
                   │ SpendCredits (allocation)
                   │ EarnCredits (refund/excess return)
```

### Auth Tier Requirements

| Operation | Required Tier | Enforcement |
|---|---|---|
| BTO order (virtual card) | Verified+ | stripe.issueCard auth gate |
| Credit allocation | Verified+ | credits.CheckSpendAllowed |
| Physical card (future: in-store pickup) | Telecom | stripe.issueCard auth gate |

### Spending Controls

Per-order virtual card の spending limit は `cost_estimate_jpy` に設定。追加の controls:

| Control | Value | Purpose |
|---|---|---|
| `spendingLimitAmount` | `cost_estimate_jpy` | Order total cap |
| `spendingLimitInterval` | `all-time` | Single-use card |
| `allowed_categories` | OEM manufacturing MCC codes | Restrict to manufacturing merchants |
| Card metadata `productionOrderRef` | `okaimono_order_id` | Audit trail |
| Card metadata `manufacturerDid` | `did:web:tsukuru.etzhayyim.com:manufacturer_*` | Factory binding |

### MCP Tools (Convo)

tsukuru convo (yoro.etzhayyim.com) で追加可能な MCP tools:

| Tool | Description |
|---|---|
| `stripe.issueCard` | BTO 決済用 virtual card 発行 |
| `stripe.getCardCredits` | Card credit 残高確認 |
| `stripe.assignCardCredits` | Murakumo credit → card 割当 |
| `stripe.listTransactions` | Card 取引履歴 |

### Audit Trail

全決済イベントが W Protocol Event Stream に記録される:

```
StripeIssuedCard (card 発行)
  → StripeCardCreditAllocation (credit 割当)
    → StripeAuthorization (OEM 支払い承認)
      → StripeCardCreditConsumption (credit 消費)
        → StripeCardTransaction (settlement)
          → okaimono.paymentSettlement (delivery 確認)
```

Cypher graph で production order → card → transactions の完全な audit chain を query 可能:

```cypher
MATCH (o:OkaimonoOrder {id: $orderId})
  -[:PAID_WITH]-> (c:StripeIssuedCard)
  -[:HAS_AUTH]-> (a:StripeAuthorization)
  -[:SETTLED_AS]-> (t:StripeCardTransaction)
RETURN o, c, a, t
LIMIT 100
```

## Convo Flow Example

```
User: "スマホ1000台、Pegatronで製造したい"
  → tsukuru.SearchManufacturers → Pegatron 候補
  → tsukuru.estimate-lead-time → 35日、¥28,000,000
  → stripe.issueCard → virtual card 発行 (limit: ¥28M)
  → stripe.assignCardCredits → Murakumo ¥28M 割当
  → tsukuru.create-production-order → 製造発注 (card bind)
  → "発注完了。Stripe card card_xxx で ¥28,000,000 を確保しました。
     製造進捗は随時お知らせします。"
  ...
  [35日後]
  → tsukuru.production_order status=delivered
  → stripe settlement → actual ¥27,500,000
  → "納品完了。差額 ¥500,000 を Murakumo クレジットに返却しました。"
```
