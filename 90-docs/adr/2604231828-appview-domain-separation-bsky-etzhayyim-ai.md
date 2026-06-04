---
id: adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
title: "ADR: AppView を bsky.etzhayyim.com に分離 — PDS/AppView domain separation (self-hosting guide 準拠)"
status: active
doc_type: adr
topic: service-topology
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - PDS (atproto.etzhayyim.com) と AppView の public domain 分離方針
  - bsky.etzhayyim.com を Layer 2 AppView の正 host とする決定
  - yoro.etzhayyim.com から AppView 機能を剥離する設計
  - did:web 配下での PDS/AppView endpoint 宣言規則
related:
  - adr-2604231811-atproto-extension-service-layers
  - adr-2604231800-atproto-permission-spec-integration
  - adr-2604231821-atproto-oauth-wire-format-snake-case
  - adr-0022-auth-topology-consolidation
supersedes: []
superseded_by: []
---

# Context

AT Protocol self-hosting guide (`https://atproto.com/ja/guides/self-hosting`) は
**"PDS and AppView should use different domain names"** を推奨する。根拠:

1. **scaling**: AppView は read-heavy public infra (全 PDS から叩かれる)、
   PDS は write/commit heavy per-user
2. **trust boundary**: PDS = private identity + commit custody、
   AppView = public index (federable, swappable)
3. **failure isolation**: AppView 障害で PDS commit / login を巻き込まない

ADR-2604231811 で定めた 15-Layer Taxonomy でも Layer 1 (PDS) と Layer 2 (AppView)
は別層と位置付けている。

## 現状 (2026-04-23 監査)

**全部 `atproto.etzhayyim.com` に集約、AppView 分離は未実装**。

```
Browser / @atproto/api
   ↓ XRPC (app.bsky.* / com.atproto.* / com.etzhayyim.*)
atproto.etzhayyim.com  ← PDS + Entryway (OAuth AS)
   │ (内部 service binding, 無効化中)
   └─ APPVIEW_SERVICE → yoro AppView Worker
```

### 現在の routing (`50-infra/cloudflare/workers/atproto/src/dispatch.ts`)

- `dispatch.ts:331-363` — `pipethroughAppView()` 実装は存在
- `app.bsky.*` read (`meta.layer === "appview" && !meta.requiresAuth`) は
  `dispatch.ts:497-501` で `APPVIEW_SERVICE` binding に forward する設計
- しかし `50-infra/cloudflare/workers/atproto/wrangler.jsonc:29` で
  **binding が comment-out 中**:

```jsonc
// { "binding": "APPVIEW_SERVICE", "service": "magatama-yoro" }
// disabled — circular dep with yoro PDS_SERVICE binding causes
// Subrequest depth limit. PDS handles app.bsky.* locally.
```

原因: yoro Worker 側も `PDS_SERVICE` binding を持っており、

```
PDS → APPVIEW_SERVICE → yoro Worker → PDS_SERVICE → PDS → ...
```

が無限 loop になり、Cloudflare の subrequest depth limit (~32) を踏む。
現状は PDS が `app.bsky.*` を **自力で処理** することで回避中。

### yoro Worker の AppView 実装

`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts:909-950` に
`handleAppViewRpc` が存在し、以下を serve する実装は既にある:

- `app.bsky.actor.getProfile`
- `app.bsky.actor.searchActors`
- `app.bsky.feed.getTimeline`
- `app.bsky.feed.getDiscoverFeed`
- `app.bsky.feed.getAuthorFeed`

このコードは yoro Worker の `/xrpc/*` route (`app.ts:1076-1090`) からも呼ばれる
構造だが、Svelte SPA / Client App (Layer 9) と **同一 Worker に同居**。

### ADR-2604231811 Layer 分類との不整合

ADR-2604231811 では:

| Worker | Layer | AT standard? |
|---|---|---|
| `atproto.etzhayyim.com` | 1 PDS + 4 Entryway | standard |
| `yoro.etzhayyim.com` | 9 Client App | standard |
| (Layer 2 AppView host) | 2 AppView | standard |

Layer 2 AppView host が **未実装 (physical domain 不在)** であり、実体は
atproto.etzhayyim.com (PDS) + yoro.etzhayyim.com (Client App) に散在している。

### did:web との関係

user handle (`{user}.etzhayyim.com`) は did:web で identity binding され、DID Document
の `service[]` に PDS endpoint を宣言する:

```
did:web:alice.etzhayyim.com
  → https://alice.etzhayyim.com/.well-known/did.json
  → {
      "service": [{
        "id": "#atproto_pds",
        "type": "AtprotoPersonalDataServer",
        "serviceEndpoint": "https://atproto.etzhayyim.com"
      }]
    }
```

つまり **handle domain ≠ PDS domain は既に分離**されている (handle = per-user、
PDS = 1 つ)。AppView を別 domain に出すのは did:web とは直交した運用判断。

## 影響

| client | 現状 flow |
|---|---|
| etzhayyim CLI + 内部 Worker | ✅ 動く |
| `@atproto/api` / Bluesky App | ⚠️ `atproto-proxy` header で明示する場合のみ動作。federation 経由で 3rd-party AppView に向ける flow は構造的に不可能 |
| 3rd-party AppView (bsky.app 等) | ❌ user が選択不可 (PDS と AppView が同一 host のため) |
| 内部 scaling | ❌ AppView の read load が PDS CPU を食う。独立 scale 不能 |

# Decision

**AppView を独立 Worker に切り出し、`bsky.etzhayyim.com` を Layer 2 AppView の正
public host として運用する**。yoro Worker からは AppView 実装を剥離し、
Client App (Layer 9) の純粋な責務に閉じる。

## 方針 5 axis

1. **`bsky.etzhayyim.com` = Layer 2 AppView host** — 新規 public domain。`etzhayyim-appview`
   Worker を立てる。`app.bsky.*` NSID の read-path を全て担う
2. **PDS は AppView に public HTTP で forward** — service binding の代わりに
   `https://bsky.etzhayyim.com/xrpc/*` に直接 fetch。circular dep 解消
3. **yoro Worker は Client App 専業** — `handleAppViewRpc` + `handleYoroAppView`
   を削除、`/xrpc/*` route を撤去。Svelte SPA + SEO snapshot + cache purge のみ
4. **did:web DID Document に AppView endpoint を宣言** — `service[]` に
   `#bsky_appview` エントリを追加 (type: `BskyAppView`、service spec 提案中)
5. **Federation-ready**: user が 3rd-party AppView を選ぶ可能性を考慮し、
   `atproto-proxy: <did>#<service>` header による override を維持

## 責務分界

| Worker | host | Layer | 責務 |
|---|---|---|---|
| `etzhayyim-pds` | `atproto.etzhayyim.com` | 1 PDS + 4 Entryway | commit log / blob / identity / OAuth AS |
| **`etzhayyim-appview` (新)** | **`bsky.etzhayyim.com`** | 2 AppView | `app.bsky.*` read (timeline/profile/feed/search/graph) |
| `etzhayyim-yoro` | `yoro.etzhayyim.com` | 9 Client App | Svelte SPA + SEO snapshot + cache purge only |

## Topology 図

### Before (現状)

```
Browser
   ↓ all XRPC
atproto.etzhayyim.com (PDS + Entryway + AppView local handler)
   │ internal binding (disabled)
   └╴APPVIEW_SERVICE → yoro Worker (AppView 実装 + Svelte SPA + PDS_SERVICE 逆 binding)
                                                                    ↑
                          circular dep → subrequest depth limit ────┘
```

### After (本 ADR)

```
Browser
   ├─ app.bsky.* read → bsky.etzhayyim.com ← Layer 2 AppView (new, standalone)
   │                        │
   │                        └─ HYPERDRIVE → RisingWave (同じ graph DB)
   │
   ├─ com.atproto.* write → atproto.etzhayyim.com (PDS)
   ├─ OAuth flow         → atproto.etzhayyim.com (Entryway)
   ├─ com.etzhayyim.vault.*    → atproto.etzhayyim.com → VAULT_SERVICE
   ├─ com.etzhayyim.signal.*   → atproto.etzhayyim.com → signal.etzhayyim.com
   └─ com.etzhayyim.convo.*    → atproto.etzhayyim.com (Chat service)

yoro.etzhayyim.com (Svelte SPA only, no /xrpc/* route)
```

## AT Protocol DID Document 拡張

AT Protocol spec は service type `AtprotoPersonalDataServer` を標準化して
いるが AppView service type は community 提案段階 (2026-01 時点で
`BskyAppView` / `AtprotoAppView` が議論中)。

本 ADR は **暫定的に `#bsky_appview` エントリを追加する**:

```json
{
  "service": [
    {
      "id": "#atproto_pds",
      "type": "AtprotoPersonalDataServer",
      "serviceEndpoint": "https://atproto.etzhayyim.com"
    },
    {
      "id": "#bsky_appview",
      "type": "BskyAppView",
      "serviceEndpoint": "https://bsky.etzhayyim.com"
    }
  ]
}
```

AT Protocol community で standardize されたら type 名 (`AtprotoAppView` 等) を
migration する (follow-up ADR)。

## client 側の resolution

OAuth / `@atproto/api` client は以下の順で AppView を解決:

1. **`atproto-proxy` header** (存在すれば最優先) — user 選択の 3rd-party AppView
2. **DID Document `service[]` の `#bsky_appview`** — 本 ADR の default
3. **fallback: PDS に forward** — 既存 behavior 維持 (PDS が自力で app.bsky.* を handle する fallback path)

# Work Plan

3 phase に分ける。Phase 1 (新 Worker deploy) + Phase 2 (PDS forward 切替) +
Phase 3 (yoro AppView 剥離) の順。Phase 間は互換性を保つ。

## Gap 一覧

| # | Gap | 対象 | 優先度 |
|---|---|---|---|
| A1 | `etzhayyim-appview` Worker 新規作成 + `bsky.etzhayyim.com` route 設定 | 新規 `50-infra/cloudflare/workers/appview/` | **CRITICAL** |
| A2 | yoro Worker から `handleAppViewRpc` / `handleYoroAppView` / `/xrpc/*` route を剥離 | `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts:909-1090` | HIGH |
| A3 | PDS `pipethroughAppView` を service binding → public HTTP fetch に変更 | `50-infra/cloudflare/workers/atproto/src/dispatch.ts:331-363` | **CRITICAL** |
| A4 | `wrangler.jsonc` の `APPVIEW_SERVICE` binding 削除、secret / env に `APPVIEW_URL=https://bsky.etzhayyim.com` を追加 | `50-infra/cloudflare/workers/atproto/wrangler.jsonc` | CRITICAL |
| A5 | DID Document serve に `#bsky_appview` service 追加 | `60-apps/etzhayyim-project-auth/worker/src-ts/did.ts` + `50-infra/cloudflare/workers/atproto/src/handlers/pds/` | MEDIUM |
| A6 | `@etzhayyim/wproto` AtpAgent config に default AppView resolution を追加 (optional, DID doc 経由) | `10-protocol/wproto/src/client.ts` | LOW |

## A1. `etzhayyim-appview` Worker 新規作成 (CRITICAL)

```
50-infra/cloudflare/workers/appview/
├── wrangler.jsonc
├── src/
│   ├── index.ts          # Hono entry, /xrpc/app.bsky.* routing
│   ├── handlers/
│   │   ├── actor.ts      # getProfile / searchActors
│   │   ├── feed.ts       # getTimeline / getAuthorFeed / getPostThread / getDiscoverFeed
│   │   ├── graph.ts      # getFollows / getFollowers
│   │   └── notification.ts
│   └── auth.ts           # viewer DID 取得 (trusted PDS header or verified JWT)
```

Bindings:
- `HYPERDRIVE` — RisingWave (同じ graph DB、read-only)
- **No `PDS_SERVICE` binding** — これが circular dep 回避の肝
- `ENVIRONMENT` / `APPVIEW_VERSION`
- `AT_PROTOCOL_REGION` (optional, future federation shard)

Auth:
- 全 endpoint public (AT Protocol AppView は認証不要が仕様)
- viewer-specific response (feed personalization 等) は:
  - `Authorization: Bearer <access_token>` が付いていれば DPoP verify + PDS JWKS で検証
  - 失敗 or 欠落 → anonymous viewer
  - 現状の `x-etzhayyim-authenticated-did` header 依存 (`dispatch.ts:345`) は PDS
    trusted binding 専用なので public Worker では使えない。必ず JWT verify 経由

Route:
- `bsky.etzhayyim.com/*` → `etzhayyim-appview` Worker (CF route)
- `bsky.etzhayyim.com/_worker/health` / `/health` smoke test

## A2. yoro Worker から AppView 剥離 (HIGH)

削除対象:
- `app.ts:909-950` — `handleAppViewRpc`
- `app.ts:996-1044` — `handleYoroAppView` (yoro-specific AppView wrapper)
- `app.ts:1076-1090` — `app.all("/xrpc/*", ...)` の AppView dispatch
- `handleGetProfile` / `handleSearchActors` / `handleGetTimeline` /
  `handleGetDiscoverFeed` / `handleGetAuthorFeed` の実装を新 Worker に移動
  (共通 graph query helper は `10-protocol/appview-helpers/` 等に切り出す案も可)

yoro Worker に残るもの:
- Svelte SPA 配信 (Workers Assets)
- `/sitemap.xml` (動的 sitemap, RisingWave graph query)
- `/api/internal/cache/purge`
- Bot/LLM crawler SEO snapshot (`renderRichBotSnapshot` / `renderYoroLlmText`)
- `PDS_SERVICE` binding は維持 (SSR の `getProfile` 等で使用、ただし AppView 経由に切替の選択肢も検討)

## A3. PDS `pipethroughAppView` public HTTP 化 (CRITICAL)

`dispatch.ts:331-363` を書き換え:

```ts
async function pipethroughAppView(nsid: string, ctx: PdsDispatchCtx): Promise<Response | null> {
  const appViewUrl = (ctx.env as Record<string, unknown>).APPVIEW_URL as string | undefined;
  if (!appViewUrl) return null;

  try {
    const url = new URL(ctx.request.url);
    const outUrl = `${appViewUrl}/xrpc/${nsid}${url.search}`;
    const headers = new Headers(ctx.request.headers);
    headers.delete("host");
    // viewer DID は trusted PDS → AppView header で forward
    headers.set("x-etzhayyim-authenticated-did", ctx.auth.userDid || "");
    // AppView 間の trust 確立: HMAC-signed shared secret or mTLS
    const internalSecret = ctx.env.APPVIEW_INTERNAL_SECRET;
    if (internalSecret) headers.set("x-etzhayyim-internal-trust", await resolveSecret(internalSecret));
    const init: RequestInit = {
      method: ctx.request.method,
      headers,
      body: ctx.request.method !== "GET" && ctx.request.method !== "HEAD"
        ? JSON.stringify(ctx.body)
        : undefined,
    };
    const resp = await fetch(outUrl, init);
    if (resp.status === 501) return null;
    return new Response(resp.body, { status: resp.status, headers: resp.headers });
  } catch (e) {
    console.warn(`[pds] AppView pipethrough failed for ${nsid}, falling back to local:`, e);
    return null;
  }
}
```

変更点:
- `ctx.env.APPVIEW_SERVICE.fetch(...)` → `fetch(appViewUrl + path, init)` (public HTTP)
- `APPVIEW_INTERNAL_SECRET` を介した internal-trust header (BPMN dispatcher と同じ pattern, ADR 2604231457)
- circular dep 完全解消 (AppView は `PDS_SERVICE` を持たない)

## A4. wrangler.jsonc 書き換え (CRITICAL)

`50-infra/cloudflare/workers/atproto/wrangler.jsonc:29` の disabled binding を
完全削除し、env に `APPVIEW_URL` + `APPVIEW_INTERNAL_SECRET` を追加:

```jsonc
{
  "vars": {
    "APPVIEW_URL": "https://bsky.etzhayyim.com"
  },
  // secrets_store_secrets (既存パターンに追加)
  "secrets_store_secrets": [
    { "binding": "APPVIEW_INTERNAL_SECRET", "store_id": "...", "secret_name": "appview_internal_trust" }
  ]
}
```

`magatama-yoro` binding は削除。

## A5. DID Document に `#bsky_appview` 追加 (MEDIUM)

authn Worker + PDS の DID doc serve handler で `service[]` に追加:

```ts
service: [
  { id: "#atproto_pds", type: "AtprotoPersonalDataServer", serviceEndpoint: "https://atproto.etzhayyim.com" },
  { id: "#bsky_appview", type: "BskyAppView", serviceEndpoint: "https://bsky.etzhayyim.com" },
],
```

影響範囲:
- `60-apps/etzhayyim-project-auth/worker/src-ts/did.ts` の `buildDidDocument`
- 既存 user DID doc は regenerate (lazy、次回 create/update 時)
- `atproto.etzhayyim.com/.well-known/did.json` も service 追加

## A6. `@etzhayyim/wproto` AtpAgent default resolution (LOW, optional)

```ts
import { AtpAgent } from '@atproto/api';
// ...
const pds = new AtpAgent({ service: "https://atproto.etzhayyim.com" });
// 将来的に:
const appview = new AtpAgent({ service: "https://bsky.etzhayyim.com" });
```

browser client が read/write で別 endpoint を使う pattern は既存 `@atproto/api`
が対応 (`resolveAppView()` 等)。本 ADR Phase 1-3 では **PDS 経由の pipethrough**
で済ませ、A6 は Phase 4 (follow-up) に送る。

# Migration

## Phase 0 (本 ADR land)

registry entry 追加、`deps.toml [[conventions]]` に Layer 2 AppView の正 host
を明示、CLAUDE.md pointer 追加。

## Phase 1 (A1 + A4, 2026-04-25)

1. `etzhayyim-appview` Worker を新規 deploy
2. `bsky.etzhayyim.com` DNS + CF route 設定 (Terraform)
3. `handleAppViewRpc` / `handleYoroAppView` のロジックを新 Worker に移植
   (yoro 側はまだ残したまま、dual-serve 期間)
4. smoke test: `curl https://bsky.etzhayyim.com/xrpc/app.bsky.actor.getProfile?actor=xxx`
5. PDS `wrangler.jsonc` に `APPVIEW_URL=https://bsky.etzhayyim.com` を追加 + secret 設定

## Phase 2 (A3, 2026-04-28)

1. PDS `pipethroughAppView` を public HTTP 版に切替 deploy
2. `app.bsky.*` trafficが PDS → bsky.etzhayyim.com に流れることを log 監視
   (Logpush `atproto-worker` → B2)
3. 1 週間 regression watch、yoro /_xrpc/* route は warning log だけ出す
   (`[yoro] deprecated /xrpc/ call — use bsky.etzhayyim.com`)

## Phase 3 (A2, 2026-05-05)

1. yoro Worker から AppView 実装削除 deploy
2. yoro `app.all("/xrpc/*", ...)` route を削除 (既存 caller は PDS に直接
   または bsky.etzhayyim.com に向ける)
3. `60-apps/etzhayyim-project-yoro/CLAUDE.md` 更新 (Layer 9 Client App 明示)

## Phase 4 (A5, 2026-05-12)

1. authn Worker + PDS の DID doc serve handler に `#bsky_appview` 追加
2. `etzhayyim identity rotate-keys` 相当で既存 user DID doc を lazy regenerate
3. `@atproto/api` 経由で DID doc resolution 時に `#bsky_appview` が取得
   できることを確認

## Phase 5 (A6, follow-up ADR)

`@etzhayyim/wproto` client が DID doc から AppView endpoint を resolve して直接
叩く flow を追加。PDS pipethrough は fallback に降格。本 ADR の scope 外。

# Consequences

## Positive

- **Circular dep 完全解消**: `APPVIEW_SERVICE` binding disabled 状態を解消、
  PDS が AppView を自力 handle する暫定状態から脱却
- **AT Protocol self-hosting guide 準拠**: PDS/AppView domain separation の
  推奨を満たす。3rd-party AppView federation の前提が整う
- **独立 scaling**: AppView の read burst が PDS の OAuth / commit path に
  影響しない。逆も同様
- **Layer 2 の物理実体**: ADR-2604231811 で定義した Layer 2 AppView が実在
  する Worker として存在、taxonomy が紙から実装に落ちる
- **Client App の純粋化**: yoro が Svelte SPA + SEO + cache purge のみに
  閉じる。Layer 9 Client App の定義に厳密に一致
- **Failure isolation**: AppView RisingWave read path が死んでも PDS commit
  と OAuth flow は生きる (login と投稿が止まらない)

## Negative

- **新 Worker deploy 運用**: 3 Worker (PDS + AppView + yoro) の deploy
  rotation + CI/CD 複雑化
- **public HTTP overhead**: service binding (zero-copy, <1ms) → public HTTP
  fetch (1-5ms same-colo) に変わる。`app.bsky.*` read は CF edge cache でも
  ほぼ吸収可能だが、cache miss 時に数 ms 増
- **internal-trust の HMAC signing コスト**: BPMN dispatcher pattern 踏襲、
  per-request ~0.3ms ECDSA/HMAC 計算追加
- **DID Document migration**: 既存 user DID doc の service 配列拡張を全
  user に propagate する必要。lazy regenerate で 90 日程度の遅延許容

## Neutral

- RisingWave graph DB は共有したまま (PDS write → MV → AppView read)。
  schema / migration 責務は graph 側で一元管理
- com.etzhayyim.*/chat.bsky.convo.* / com.etzhayyim.vault.* / com.etzhayyim.signal.* 等の
  non-bsky namespace は **atproto.etzhayyim.com に残す** (Layer 1 PDS + Layer 7 Chat
  + Layer 11 Key Directory + Layer 12 Secret Vault の pipethrough target)。
  本 ADR は `app.bsky.*` のみ AppView に分離

# Alternatives Considered

## B1. 現状維持 (PDS に AppView 同居)

- pros: deploy シンプル
- cons: self-hosting guide 非準拠、circular dep 解消不能、ADR-2604231811
  Layer 2 が物理実体なし、3rd-party AppView federation 不能。**却下**

## B2. AppView を yoro Worker に同居のまま、circular dep を回避する別策

- 案: yoro の `PDS_SERVICE` binding を削除、yoro は HTTP で atproto.etzhayyim.com
  を叩くだけにする
- pros: 新 Worker 不要
- cons: yoro は Client App (Svelte SPA) + AppView の 2 責務が同居し続ける。
  Layer taxonomy 違反。SPA deploy と AppView deploy の blast radius が
  結合し、SPA バグで AppView を巻き込む。**却下**

## B3. `appview.etzhayyim.com` を host にする

- pros: 名前が責務を直接表す
- cons: Bluesky / AT Protocol community では `bsky.{tld}` が慣例 (bsky.app,
  bsky.social 等)。`bsky.etzhayyim.com` の方が `@atproto/api` default resolution /
  user の心当たりで通じやすい。**却下** (`appview.etzhayyim.com` を CNAME alias と
  して残すのは許容)

## B4. AppView も atproto.etzhayyim.com に残し、path で分離 (`/appview/xrpc/*`)

- pros: domain 追加不要
- cons: AT Protocol client は host ベースで routing する前提 (service
  endpoint = URL origin)。path 分離は spec 違反、3rd-party client 互換不能。
  **却下**

## B5. Cloudflare Service Binding の subrequest depth を回避する設計 (yoro の PDS_SERVICE 削除 + AppView は yoro に残す)

- pros: public HTTP overhead 回避、Worker 1 つ減る
- cons: yoro = Client App + AppView 同居の責務混合が残る (B2 と同じ問題)。
  deploy blast radius 結合。**却下**

# Non-Goals

本 ADR は **scope 外**:

- Relay (BGS) の自ホスト — Bluesky 公式依存のまま
- 3rd-party AppView federation の実装 (user が AppView を選べる UI / DID doc
  update 経路) — Phase 5 follow-up ADR
- Ozone (moderation dashboard) の自ホスト — 別 Layer 8、別 ADR
- Feed Generator (`app.bsky.feed.getFeedSkeleton`) の自ホスト — 別 Layer 5、別 ADR
- AppView の read caching strategy (CF Cache API / Durable Object cache 設計)
  — 実装 detail、別 design doc
- AppView の graph query pagination / rate limit 設計 — 実装 detail

# References

## 公式仕様

- [AT Protocol self-hosting guide](https://atproto.com/ja/guides/self-hosting) — "PDS and AppView should use different domain names"
- [AT Protocol service reference](https://atproto.com/guides/overview) — PDS / AppView / Relay / Feed Generator の責務
- [AT Protocol DID spec](https://atproto.com/specs/did) — service endpoint 宣言形式
- [did:web W3C spec](https://w3c-ccg.github.io/did-method-web/) — `.well-known/did.json` resolution

## 関連 ADR

- `90-docs/adr/2604231811-atproto-extension-service-layers.md` — 15-Layer Taxonomy (Layer 1 PDS / Layer 2 AppView / Layer 9 Client App の定義)
- `90-docs/adr/2604231800-atproto-permission-spec-integration.md` — OAuth permission spec 準拠
- `90-docs/adr/2604231821-atproto-oauth-wire-format-snake-case.md` — OAuth wire format
- `90-docs/adr/0022-auth-topology-consolidation.md` — 2-token model

## 実装 citations

- `50-infra/cloudflare/workers/atproto/wrangler.jsonc:29` — disabled `APPVIEW_SERVICE` binding
- `50-infra/cloudflare/workers/atproto/src/dispatch.ts:331-363` — `pipethroughAppView` (A3 書き換え対象)
- `50-infra/cloudflare/workers/atproto/src/dispatch.ts:497-501` — `meta.layer === "appview"` forward
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts:909-950` — `handleAppViewRpc` (A2 削除対象)
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts:996-1044` — `handleYoroAppView`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts:1076-1090` — yoro `/xrpc/*` route
- `60-apps/etzhayyim-project-auth/worker/src-ts/did.ts` — DID doc `service[]` build (A5)
- `90-docs/platform/260413-pds-appview-topology-shannon-analysis.md` — Candidate C topology (η=0.95) — 本 ADR で Candidate C を domain 分離版にアップグレード
