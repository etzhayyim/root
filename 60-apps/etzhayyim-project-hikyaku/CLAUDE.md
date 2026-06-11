# etzhayyim-project-hikyaku — Transport Agent (飛脚)

## Overview

AI エージェントが運送オーダーを生成し、hc.etzhayyim.com の HC ギグワーカー (runner) が物理配達を実行するプラットフォーム。

- **URL**: https://hikyaku.etzhayyim.com
- **API**: https://hk7ky4ku.etzhayyim.com/xrpc
- **Nanoid**: `hk7ky4ku`

## Architecture

```
Browser (SuperApp Mobile-First)
  ├─ HTML/JS → hikyaku.etzhayyim.com (static delivery)
  └─ API → hk7ky4ku.etzhayyim.com/xrpc → Envoy Gateway
              ↓
       App: hikyaku-nhk7ky4ku (TS Native)
              ├─ HikyakuCommandService — order/dispatch/tracking commands
              ├─ HikyakuQueryService — list/search/track/stats
              ├─ actor.SendRoomEvent() → Matrix MessagingService
              ├─ HC Integration → hc.etzhayyim.com HCCommandService (runner 募集)
              └─ kotodama WIT → SQL graph (Arrow schema)
```

## Event Stream Services

| Service | Path |
|---|---|
| HikyakuCommandService | `/xrpc/etzhayyim.hikyaku.v1.HikyakuCommandService/*` |
| HikyakuQueryService | `/xrpc/etzhayyim.hikyaku.v1.HikyakuQueryService/*` |

### Transport Rule

- 正規 command contract は Matrix `org.etzhayyim.command.hikyaku.*`
- typed read は XRPC `HikyakuQueryService`
- HC 連携は XRPC `HCCommandService/CreateShift` 経由

## Arrow Tables (sql graph/sql graph)

| Table | DocID | Purpose |
|---|---|---|
| `hikyaku_orders` | `order_id` | 配達オーダー (sender/receiver/package/status/runner) |
| `hikyaku_runners` | `runner_id` | Runner プロフィール (HC worker 参照) |
| `hikyaku_tracking_events` | `event_id` | 追跡イベント (位置/状態遷移/写真) |
| `hikyaku_delivery_zones` | `zone_id` | 配達エリア・料金設定 |

## HC Integration (CRITICAL)

CreateOrder 時に hc.etzhayyim.com の HC シフトを自動生成。HC ↔ Hikyaku マッピング:

| Hikyaku | HC |
|---|---|
| Order | Shift |
| Runner | Worker |
| PickupConfirm | CheckIn |
| DeliveryConfirm | CheckOut |
| price_jpy * 0.75 | hourly_rate_jpy |

HC シフトの `metadata_json` に `order_id` を埋め込み双方向参照。

## Matrix Protocol Integration

| Room | Purpose |
|---|---|
| `!hikyaku-orders-{nanoid}` | オーダー通知 |
| `!hikyaku-dispatch-{nanoid}` | ディスパッチ・Runner 割当 |
| `!hikyaku-tracking-{nanoid}` | 配達追跡 (per-order thread) |
| `!hikyaku-issues-{nanoid}` | 問題報告・再配達 |

## Order Lifecycle

```
draft → pending → assigned → picking_up → in_transit → delivering → delivered
                    │                                                    │
                    └── cancelled                            failed → rescheduled → pending
```

## Pricing

```
total = base_price + (distance_km * per_km) + weight_surcharge + type_surcharge
runner_pay = total * 0.75
platform_fee = total * 0.25
```

## UI (SuperApp Mobile-First)

- SuperAppTabBar (Home / Talk)
- Sidebar 禁止
- max-w-[600px] モバイル幅統一
- Home タブ: オーダー一覧 / 追跡 / ダッシュボード
- Talk タブ: Matrix ThreadPanel (per-order thread)

## Build & Deploy

```bash
cd wasm/etzhayyim-wasm-hikyaku-hk7ky4ku/svelte
pnpm install && pnpm build
cd ..
etzhayyim build
etzhayyim deploy --smoke-url https://hk7ky4ku.etzhayyim.com/health
```

## Design Authority

`90-docs/260314-hikyaku-transport-agent-design.md`
