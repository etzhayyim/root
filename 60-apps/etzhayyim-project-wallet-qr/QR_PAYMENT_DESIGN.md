# QR Payment Design — PayPay-like GCC Token Payment

`etzhayyim-project-wallet-qr` — AppShell v2 SuperApp の Wallet タブから QR コードで GCC トークン決済を行う App。

## Overview

PayPay モデルを GCC (ETZHAYYIM Computing Credit, ERC-20, 6 decimals) に適用する。
Geth private chain 上の GCC トークン転送を QR コードで実行する P2P / P2M (Person-to-Merchant) 決済。

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  AppShell v2 — SuperApp (Wallet Tab)                │
│  ┌───────────────────────────────────────────────┐  │
│  │  QR Payment MiniApp (Widget API + OpenID)     │  │
│  │  ┌─────────────┐  ┌──────────────────────┐   │  │
│  │  │ QR Display   │  │ QR Scanner           │   │  │
│  │  │ (受取/請求)  │  │ (支払)               │   │  │
│  │  └─────────────┘  └──────────────────────┘   │  │
│  └───────────────────────────────────────────────┘  │
│            │ XRPC                           │
│            ▼                                        │
│  ┌───────────────────────────────────────────────┐  │
│  │  qr-payment App (WASM/TinyGo)                     │  │
│  │  PaymentCommandService / PaymentQueryService   │  │
│  │  ┌────────────┐  ┌─────────────────────────┐  │  │
│  │  │ Payment    │  │ Matrix Room Events      │  │  │
│  │  │ Request    │  │ (payment commands)       │  │  │
│  │  │ Manager    │  │                          │  │  │
│  │  └────────────┘  └─────────────────────────┘  │  │
│  │        │                                       │  │
│  │        ▼                                       │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │ cypher graph (payment_requests_current,      │  │  │
│  │  │          payment_history_current)        │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
│            │ HTTP (internal)                        │
│            ▼                                        │
│  ┌───────────────────────────────────────────────┐  │
│  │  geth-wallet-manager (Native Go)              │  │
│  │  SurvivalService.Transfer (GCC ERC-20)        │  │
│  └───────────────────────────────────────────────┘  │
│            │ JSON-RPC                               │
│            ▼                                        │
│  ┌───────────────────────────────────────────────┐  │
│  │  Geth PoS Node (geth-pos.kotodama-runtime:8545)       │  │
│  │  GCC Contract: 0x799d24a6FFBb758C6E2Ed8f981...│  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Payment Modes (PayPay Model)

### Mode A: Store Scan (店舗スキャン方式)

ユーザーが QR を表示 → 店舗がスキャンして金額入力 → 決済実行。

```
User (Payer)                    Merchant (Payee)
────────────────                ────────────────────
1. Wallet Tab → "支払う"
2. QR 表示
   (user_address + nonce)
                         ──→   3. スキャン → 金額入力
                         ←──   4. PaymentRequest 作成
5. Push通知 → 確認画面
6. 承認 (PIN/生体認証)
                         ──→   7. GCC Transfer 実行
8. 完了通知                     8. 完了通知
```

### Mode B: User Scan (ユーザースキャン方式)

店舗が QR を表示 (固定 or 動的) → ユーザーがスキャンして金額入力 → 決済実行。

```
Merchant (Payee)                User (Payer)
────────────────────            ────────────────
1. 固定 QR or 動的 QR 表示
   (merchant_address +
    amount? + request_id?)
                         ──→   2. スキャン
                                3. 金額入力 (固定額なら skip)
                                4. 確認画面 (金額 + 送金先)
                                5. 承認 (PIN/生体認証)
                         ──→   6. GCC Transfer 実行
7. 完了通知                     7. 完了通知
```

### Mode C: P2P Transfer (個人間送金)

```
Receiver                        Sender
────────────────────            ────────────────
1. Wallet → "受け取る"
2. QR 表示
   (receiver_address + amount?)
                         ──→   3. スキャン
                                4. 金額入力 or 確認
                                5. 承認
                         ──→   6. GCC Transfer 実行
7. 完了通知                     7. 完了通知
```

## QR Code Payload Format

### Static QR (固定 QR — 店舗掲示用)

```
etzhayyim://pay?v=1&to=0x1234...abcd&name=CafeETZHAYYIM
```

| Field | Required | Description |
|-------|----------|-------------|
| `v` | yes | Protocol version (1) |
| `to` | yes | Payee Ethereum address (0x, 42 chars) |
| `name` | no | Display name (URL-encoded, max 32 chars) |

### Dynamic QR (動的 QR — 金額指定・一回限り)

```
etzhayyim://pay?v=1&to=0x1234...abcd&amt=1500.00&rid=req_abc123&exp=1710400000&name=CafeETZHAYYIM
```

| Field | Required | Description |
|-------|----------|-------------|
| `v` | yes | Protocol version (1) |
| `to` | yes | Payee address |
| `amt` | yes | Amount in GCC (decimal, 6 dp max) |
| `rid` | yes | Payment request ID (unique, `req_` prefix + nanoid) |
| `exp` | yes | Expiry Unix timestamp (seconds) |
| `name` | no | Display name |

### User Display QR (ユーザー提示用 — Store Scan 方式)

```
etzhayyim://id?v=1&from=0x5678...efgh&nonce=n_xyz789&exp=1710400000
```

| Field | Required | Description |
|-------|----------|-------------|
| `v` | yes | Protocol version (1) |
| `from` | yes | Payer address |
| `nonce` | yes | One-time nonce (`n_` prefix + nanoid, 5 min expiry) |
| `exp` | yes | Expiry Unix timestamp |

## Security

### Replay Protection

- Dynamic QR: `rid` (request ID) は一度使用したら `consumed` 状態に遷移。再利用不可
- User Display QR: `nonce` は 5 分間有効。使用後は即座に invalidate
- Static QR: `rid` なし。金額はスキャン側で入力するため replay リスクなし（毎回新規 PaymentRequest 作成）

### Authentication Chain

```
1. Widget API OpenID → Matrix identity 検証
2. Clerk JWT → org_id / user_id 確認
3. Payment 承認 → PIN or 生体認証 (WebAuthn)
4. geth-wallet-manager → HD wallet 署名 (server-side, 秘密鍵非公開)
```

### Amount Limits

| Tier | 1 回上限 | 日次上限 | 月次上限 |
|------|---------|---------|---------|
| Basic (KYC なし) | 100 GCC | 500 GCC | 5,000 GCC |
| Verified (KYC 済) | 10,000 GCC | 50,000 GCC | 500,000 GCC |
| Merchant | 100,000 GCC | 1,000,000 GCC | unlimited |

### Fraud Prevention

- 同一 `from` → 同一 `to` への連続送金: 60 秒 cooldown
- 残高不足チェック: Transfer 前に `GetBalance` で事前検証
- `exp` 切れ QR の reject (client + server 両方で検証)
- `information_classification: CUI` (金融トランザクション)

## XRPC Services

### PaymentCommandService

```protobuf
service PaymentCommandService {
  // QR 生成 (Dynamic QR / User Display QR)
  rpc CreatePaymentQR(CreatePaymentQRRequest) returns (CreatePaymentQRResponse);

  // 支払い実行
  rpc ExecutePayment(ExecutePaymentRequest) returns (ExecutePaymentResponse);

  // 支払い承認 (Store Scan 方式で payer が承認)
  rpc ApprovePayment(ApprovePaymentRequest) returns (ApprovePaymentResponse);

  // 支払い拒否
  rpc RejectPayment(RejectPaymentRequest) returns (RejectPaymentResponse);
}
```

### PaymentQueryService

```protobuf
service PaymentQueryService {
  // 支払いリクエスト取得 (QR スキャン後の詳細取得)
  rpc GetPaymentRequest(GetPaymentRequestRequest) returns (GetPaymentRequestResponse);

  // 支払い履歴 (paginated)
  rpc ListPaymentHistory(ListPaymentHistoryRequest) returns (ListPaymentHistoryResponse);

  // 残高取得 (GCC + ETH)
  rpc GetBalance(GetBalanceRequest) returns (GetBalanceResponse);

  // QR nonce 検証
  rpc ValidateNonce(ValidateNonceRequest) returns (ValidateNonceResponse);
}
```

### Message Types

```protobuf
message CreatePaymentQRRequest {
  // "dynamic" | "user_display"
  string qr_type = 1;
  // Amount in GCC (decimal string). Required for dynamic, empty for user_display
  string amount = 2;
  // Display name (optional)
  string display_name = 3;
}

message CreatePaymentQRResponse {
  // QR payload string (etzhayyim://pay?... or etzhayyim://id?...)
  string qr_payload = 1;
  // Payment request ID (for dynamic QR)
  string request_id = 2;
  // Expiry timestamp
  int64 expires_at = 3;
}

message ExecutePaymentRequest {
  // Scanned QR payload
  string qr_payload = 1;
  // Amount in GCC (required for static QR / user_display QR)
  string amount = 2;
  // PIN hash or WebAuthn assertion
  string auth_proof = 3;
}

message ExecutePaymentResponse {
  string payment_id = 1;
  string tx_hash = 2;
  string amount = 3;
  string from_address = 4;
  string to_address = 5;
  string status = 6; // "confirmed" | "pending" | "failed"
  int64 timestamp = 7;
}

message ListPaymentHistoryRequest {
  int32 offset = 1;
  int32 limit = 2;
  // "sent" | "received" | "all"
  string direction = 3;
}

message ListPaymentHistoryResponse {
  repeated PaymentRecord records = 1;
  int32 total = 2;
  int32 offset = 3;
  int32 limit = 4;
}

message PaymentRecord {
  string payment_id = 1;
  string from_address = 2;
  string to_address = 3;
  string amount = 4;
  string tx_hash = 5;
  string status = 6;
  string display_name = 7;
  int64 timestamp = 8;
  string direction = 9; // "sent" | "received"
}
```

## cypher graph Tables

### `payment_requests_current`

Payment request の一時状態管理 (Dynamic QR / Store Scan nonce)。

| Column | Type | Description |
|--------|------|-------------|
| `_doc_id` | String | `req_{nanoid}` or `n_{nanoid}` |
| `org_id` | String | RLS |
| `user_id` | String | RLS (作成者) |
| `actor_id` | String | RLS |
| `request_type` | String | `dynamic_qr` / `user_display` / `store_scan` |
| `from_address` | String | Payer address (user_display の場合) |
| `to_address` | String | Payee address (dynamic_qr の場合) |
| `amount` | String | GCC amount (decimal string, 6 dp) |
| `display_name` | String | 表示名 |
| `status` | String | `pending` / `consumed` / `expired` / `rejected` |
| `expires_at` | Int64 | Unix timestamp (seconds) |
| `created_at` | Int64 | Unix timestamp (ms) |
| `consumed_at` | Int64 | Unix timestamp (ms), 0 if not consumed |
| `payment_id` | String | 関連 payment_id (consumed 後に設定) |

### `payment_history_current`

確定済み決済の履歴。

| Column | Type | Description |
|--------|------|-------------|
| `_doc_id` | String | `pay_{nanoid}` |
| `org_id` | String | RLS |
| `user_id` | String | RLS (payer or payee, 両方の行を作成) |
| `actor_id` | String | RLS |
| `from_address` | String | Payer address |
| `to_address` | String | Payee address |
| `amount` | String | GCC amount |
| `tx_hash` | String | Ethereum tx hash |
| `status` | String | `confirmed` / `pending` / `failed` |
| `direction` | String | `sent` / `received` |
| `display_name` | String | 相手方の表示名 |
| `request_id` | String | 元の payment request ID |
| `block_number` | Int64 | Ethereum block number |
| `gas_used` | Int64 | Gas used |
| `created_at` | Int64 | Unix timestamp (ms) |

## Matrix Event Types

Payment コマンドは Matrix room event として永続化する。

| Event Type | Description |
|------------|-------------|
| `org.etzhayyim.payment.request` | 支払いリクエスト作成 |
| `org.etzhayyim.payment.execute` | 支払い実行 |
| `org.etzhayyim.payment.confirm` | 支払い確定 (on-chain confirmed) |
| `org.etzhayyim.payment.reject` | 支払い拒否 |
| `org.etzhayyim.payment.expire` | 支払いリクエスト期限切れ |

### Event Payload Example

```json
{
  "type": "org.etzhayyim.payment.execute",
  "content": {
    "paymentId": "pay_abc123",
    "requestId": "req_xyz789",
    "fromAddress": "0x1234...abcd",
    "toAddress": "0x5678...efgh",
    "amount": "1500.000000",
    "txHash": "0xabcd...1234",
    "status": "confirmed",
    "timestamp": 1710400000000
  }
}
```

## UI Design (SuperApp Mobile-First)

### Wallet Tab 拡張

```
┌──────────────────────────┐
│  ≡  Wallet         ⚙    │  ← Header
├──────────────────────────┤
│                          │
│    GCC Balance           │
│    ¥ 12,500.00           │  ← GCC balance (¥ 表示)
│    ≈ $125.00 USD         │
│                          │
│  ┌──────┐  ┌──────────┐  │
│  │ 支払う │  │ 受け取る  │  │  ← Primary actions
│  │  📷   │  │   📱     │  │
│  └──────┘  └──────────┘  │
│                          │
│  ┌──────┐  ┌──────────┐  │
│  │ 送金  │  │  履歴    │  │  ← Secondary actions
│  │  💸   │  │   📋     │  │
│  └──────┘  └──────────┘  │
│                          │
│  ─── 最近の取引 ─────────  │
│  CafeETZHAYYIM    -500.00 GCC │
│  田中太郎   +1,200.00 GCC │
│  BookStore   -350.00 GCC │
│                          │
├──────────────────────────┤
│ 🏠  💬  📦  🔍  💳     │  ← SuperApp TabBar
└──────────────────────────┘
```

### QR Scanner View (支払う)

```
┌──────────────────────────┐
│  ←  QR スキャン           │
├──────────────────────────┤
│                          │
│  ┌────────────────────┐  │
│  │                    │  │
│  │    ┌──────────┐    │  │
│  │    │          │    │  │
│  │    │  Camera  │    │  │
│  │    │  Preview │    │  │
│  │    │          │    │  │
│  │    └──────────┘    │  │
│  │                    │  │
│  └────────────────────┘  │
│                          │
│  QR コードを枠内に        │
│  合わせてください          │
│                          │
│  ───────────────────────  │
│  💡 ライト   📷 アルバム   │
│                          │
└──────────────────────────┘
```

### Payment Confirmation View

```
┌──────────────────────────┐
│  ←  支払い確認            │
├──────────────────────────┤
│                          │
│       CafeETZHAYYIM           │
│    0x1234...abcd         │
│                          │
│  ┌────────────────────┐  │
│  │                    │  │
│  │   1,500.00 GCC     │  │  ← Amount (large)
│  │   ≈ ¥1,500         │  │
│  │                    │  │
│  └────────────────────┘  │
│                          │
│  残高: 12,500.00 GCC     │
│  残高 (支払後): 11,000.00 │
│                          │
│  ┌────────────────────┐  │
│  │                    │  │
│  │    支払いを確定      │  │  ← Confirm button
│  │                    │  │
│  └────────────────────┘  │
│                          │
│  PIN / 生体認証で承認     │
│                          │
└──────────────────────────┘
```

### QR Display View (受け取る)

```
┌──────────────────────────┐
│  ←  受け取る              │
├──────────────────────────┤
│                          │
│     マイ QR コード        │
│                          │
│  ┌────────────────────┐  │
│  │                    │  │
│  │   ┌────────────┐   │  │
│  │   │            │   │  │
│  │   │  QR Code   │   │  │
│  │   │            │   │  │
│  │   └────────────┘   │  │
│  │                    │  │
│  │  0x5678...efgh     │  │
│  └────────────────────┘  │
│                          │
│  金額を指定:              │
│  ┌─────────────┐ GCC    │
│  │             │         │
│  └─────────────┘         │
│                          │
│  [金額付き QR を更新]      │
│                          │
│  ⏱ 残り 4:32             │  ← Nonce expiry countdown
│                          │
└──────────────────────────┘
```

### Payment Complete View

```
┌──────────────────────────┐
│                          │
│          ✓               │
│     支払い完了            │
│                          │
│    1,500.00 GCC          │
│    → CafeETZHAYYIM            │
│                          │
│    TX: 0xabcd...1234     │
│    Block: #18,234,567    │
│                          │
│  ┌────────────────────┐  │
│  │      閉じる         │  │
│  └────────────────────┘  │
│                          │
└──────────────────────────┘
```

## Component Structure

```
60-apps/etzhayyim-project-wallet-qr/
├── QR_PAYMENT_DESIGN.md              (this file)
├── PROJECT.jsonld
└── wasm/
    └── etzhayyim-wasm-qrpay-<nanoid>/
        ├── main.go                    (App — payment logic)
        ├── qr.go                      (QR payload encode/decode)
        ├── limits.go                  (amount limits, cooldown)
        ├── kotodama.toml
        ├── go.mod
        ├── wit/
        │   ├── world.wit
        │   └── deps/
        ├── k8s/
        │   └── app.yaml
        └── svelte/
            ├── src/
            │   ├── routes/
            │   │   ├── +layout.svelte
            │   │   ├── +page.svelte     (Wallet home + QR actions)
            │   │   ├── scan/
            │   │   │   └── +page.svelte (QR scanner)
            │   │   ├── receive/
            │   │   │   └── +page.svelte (QR display)
            │   │   ├── confirm/
            │   │   │   └── +page.svelte (Payment confirm)
            │   │   ├── complete/
            │   │   │   └── +page.svelte (Payment result)
            │   │   └── history/
            │   │       └── +page.svelte (Payment history)
            │   └── lib/
            │       ├── client/
            │       │   └── payment-client.ts  (XRPC client)
            │       └── components/
            │           ├── QRDisplay.svelte    (QR code renderer)
            │           └── QRScanner.svelte    (Camera QR reader)
            ├── vite.config.ts
            └── package.json
```

## Payment Flow — Sequence (User Scan Mode)

```
Payer App          qr-payment App               geth-wallet-manager     Geth Node
─────────          ──────────────────       ───────────────────     ─────────
  │                       │                        │                    │
  │ Scan QR               │                        │                    │
  │──────────────────────→│                        │                    │
  │                       │                        │                    │
  │ GetPaymentRequest     │                        │                    │
  │ (if dynamic QR)       │                        │                    │
  │──────────────────────→│                        │                    │
  │←──────────────────────│                        │                    │
  │  {to, amount, name}   │                        │                    │
  │                       │                        │                    │
  │ User confirms         │                        │                    │
  │ + PIN/biometric       │                        │                    │
  │                       │                        │                    │
  │ ExecutePayment        │                        │                    │
  │──────────────────────→│                        │                    │
  │                       │ Validate request       │                    │
  │                       │ Check limits           │                    │
  │                       │ Check balance          │                    │
  │                       │───────────────────────→│                    │
  │                       │←───────────────────────│                    │
  │                       │                        │                    │
  │                       │ Transfer GCC           │                    │
  │                       │───────────────────────→│                    │
  │                       │                        │ ERC-20 transfer()  │
  │                       │                        │───────────────────→│
  │                       │                        │←───────────────────│
  │                       │←───────────────────────│ tx_hash            │
  │                       │                        │                    │
  │                       │ Mark request consumed  │                    │
  │                       │ Write payment_history  │                    │
  │                       │ Emit Matrix event      │                    │
  │                       │                        │                    │
  │←──────────────────────│                        │                    │
  │  {payment_id, tx_hash,│                        │                    │
  │   status: confirmed}  │                        │                    │
```

## geth-wallet-manager Integration

既存の `SurvivalService.Transfer` endpoint を使用。追加 endpoint は不要。

```
POST http://geth-wallet-manager.kotodama-runtime:8080/xrpc/etzhayyim.actor.v1.SurvivalService/Transfer
Content-Type: application/json

{
  "from_nanoid": "payer_nanoid",
  "to_address": "0x1234...abcd",
  "amount": "1500000000",  // 1500 GCC in raw units (6 decimals)
  "token": "gcc"
}
```

HD wallet 導出は `geth-wallet-manager` が `MASTER_SEED` から `nanoid` ベースで実行。
App 側は秘密鍵を持たず、`nanoid` → wallet address のマッピングのみ知る。

## Daily Evolution Team

```go
teamCfg := performer.DefaultAppTeam(appNanoid, "qr-payment",
    "PayPay-like QR code payment using GCC token on Geth",
    homeserver,
)
```

5 ISCO agents:
- **BM (1211)**: 決済ボリューム、GMV、アクティブユーザー数の分析
- **PO (1120)**: 決済 UX、QR スキャン成功率、完了率の改善提案
- **MK (2433)**: 加盟店獲得、キャンペーン設計
- **ENG (2512)**: トランザクション性能、QR 生成/検証の最適化
- **QA (2519)**: セキュリティ監査、replay attack テスト、limit enforcement 検証

## Implementation Priority

| Phase | Scope | Description |
|-------|-------|-------------|
| **P0** | Core | QR payload encode/decode, Static QR, P2P transfer, payment history |
| **P1** | Dynamic | Dynamic QR (金額指定), User Display QR (Store Scan), nonce management |
| **P2** | Security | PIN/WebAuthn 認証, amount limits, cooldown enforcement |
| **P3** | UX | Push 通知 (Matrix event), 取引詳細, 加盟店管理画面 |
| **P4** | Analytics | GMV ダッシュボード, 日次レポート (Daily Evolution 連携) |
