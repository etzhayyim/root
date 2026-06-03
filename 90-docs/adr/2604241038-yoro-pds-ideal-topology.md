---
id: adr-2604241038-yoro-pds-ideal-topology
title: "ADR: yoro + PDS + AppView 理想トポロジー — Single-Responsibility Workers + NSID-prefix ルーティング契約"
status: active
doc_type: adr
topic: service-topology
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - atproto / yoro / bsky / actor Worker の責務境界
  - NSID-prefix routing 契約 (PDS dispatch の単一 SSoT)
  - Worker 間 trust plane (viewer DID 伝播方法)
  - DID 正規化 (root vs path-DID) の層別 rule
  - client facing endpoint の決定木
related:
  - adr-2604231811-atproto-extension-service-layers
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
  - adr-2604231821-atproto-oauth-wire-format-snake-case
  - adr-2604240914-oauth-rs-binding-revocation-introspection
  - adr-0022-auth-topology-consolidation
  - adr-0024-auth-accounts-worker-topology
  - adr-0081-worker-direct-hyperdrive-persistence
  - adr-0056-bpmn-as-actor
supersedes: []
superseded_by: []
---

# Context

直近 2 週間で auth / AppView / revocation の ADR を 6 本 land し、PDS + yoro
周辺の構造は実装レベルでは "正しい" 方向に動いてはいる。ただし **全体の
topology は refactor の重ね塗りで曖昧**になっており、以下の痛みが出ている:

## 具体的な痛み (2026-04-24 監査)

### A. PDS 肥大化

`50-infra/cloudflare/workers/atproto/src/dispatch.ts` は 1000 行超で、
NSID prefix ごとの pipethrough branch を直接持っている:

| NSID prefix | pipethrough 先 | 現状の位置 |
|---|---|---|
| `com.etzhayyim.vault.*` | `VAULT_SERVICE` (binding) | `dispatch.ts:447-468` |
| `com.etzhayyim.apps.yabai.*` (8 NSID) | `dispatcher.etzhayyim.com:8080` (BPMN) | `dispatch.ts:376-440` |
| `app.bsky.*` | `APPVIEW_URL` (public HTTP, disabled binding) | `dispatch.ts:330-402` |
| `com.atproto.*` | 自前 handler (PDS local) | `handlers/pds/*` |
| その他 | ??? (inline if / switch) | 散在 |

新しい layer を増やすたびに `dispatch.ts` に if を足す構造。routing が
コードの形で散っており、"どの NSID がどこに行くか" の一覧が書かれた場所が
ない。

### B. yoro は長らく Client App + AppView の兼業

ADR-2604231828 A2 で剥離したが (今日 commit `62798063cde`)、依然として:

- `app.all("/xrpc/*", ...)` route が残り `com.etzhayyim.convo.* / com.etzhayyim.signal.* /
  chat.bsky.convo.*` を `atproto.etzhayyim.com` にプロキシしている
- `yoro.etzhayyim.com` host が public に XRPC endpoint を持っている状態
- ブラウザ側 code (`svelte/src/lib/graph/feed.ts`) は
  `@etzhayyim/wproto` 経由で `atproto.etzhayyim.com` に話しているが、**一部古い code
  は `yoro.etzhayyim.com/xrpc/*` を直接叩いている可能性**がある (grep 残存)

### C. bsky.etzhayyim.com は暫定 proxy、まだ自立していない

`67b922f5242` で AppView handlers を新 Worker に migrate したが、**pnpm
install / wrangler deploy / DNS route まだ未実行**。現状:

- `bsky.etzhayyim.com` DNS route は wrangler.jsonc に書いてあるが live にはなって
  いない
- PDS `pipethroughAppView` は `APPVIEW_URL=https://bsky.etzhayyim.com` を向いて
  いるが、その URL が 404 を返すので全 request が PDS local handler に
  fall through = AppView 分離は実質未稼働

### D. Internal trust plane が多重化

`x-etzhayyim-authenticated-did` が viewer DID の forwarding メディア。受け手の
検証ロジックが Worker ごとに微妙に違う:

| Worker | 検証方法 | 出典 |
|---|---|---|
| yoro (旧 AppView) | hostname が `yoro.etzhayyim.com` なら **drop** | `app.ts:172-183` (削除済) |
| bsky (新 AppView) | `x-etzhayyim-internal-trust` shared secret 一致時のみ受理 | `handlers/appview.ts:35-52` |
| PDS 内部 (service binding) | `x-magatama-verified=true` かつ binding 存在 | `auth/verify.ts:472-493` |
| BPMN dispatcher | `x-internal-trust` (別 header!) | `dispatch.ts:408-411` |

4 通りの trust 判定 pattern。1 つに統一できていない。

### E. DID 正規化が層ごとに割れている

2026-04-24 に観測された bug (本 ADR の motivation 1 つ):

```
ユーザ post:
  at://did:web:sh1n5h1x.etzhayyim.com:shigeo-kageyama-mob-psycho-100/
      app.bsky.feed.post/3mk7ebsxqdg2x  (path-DID author)

getPostThread  → 返る (rkey-only fallback)
getAuthorFeed  → 返る (repo LIKE 'did:web:sh1n5h1x.etzhayyim.com:%' fallback)
getProfile     → postsCount: 0  ← 集計 MV が stale
yoro 表示      → 0              ← ?? 演算子で 0 が最終表示
```

`vertex_repo_record.repo` は raw path-DID、`mv_actor_social_stats` は raw
repo で GROUP BY、`mv_profile_page_stats` は `normalize_actor_did(repo)` で
root 集約、yoro frontend の `postsCountDisplay = actor.postsCount ?? feedItems.length`
は nullish-coalescing で 0 がそのまま出る。**4 層に 4 種の DID-normalization
ロジックが散在**している。

### F. Client → XRPC endpoint の resolution が単一でない

yoro browser code:

- `@etzhayyim/wproto` AtpAgent は `atproto.etzhayyim.com` に固定で話す
- SSR load() は `PDS_SERVICE` binding 経由で PDS に話す (internal)
- Bot snapshot renderer は `PDS_SERVICE` binding 経由で PDS に話す (internal)
- etzhayyim CLI は `atproto.etzhayyim.com` に public HTTP で話す
- Claude Code chat agent は `atproto.etzhayyim.com` に public HTTP で話す (+ `etzhayyim agent-token`)

路線自体は統一できているが、**atproto.etzhayyim.com に全部押しつけ**ており、PDS
過負荷 (C) + PDS ロジック肥大 (A) を加速する構造。

# Decision

PDS + yoro + AppView の境界を **Worker = 1 layer = 1 namespace** の原則で
再整理し、以下の 5 つを contract として明文化する。

## 原則

1. **1 Worker = 1 layer (ADR-2604231811)** — 15-layer taxonomy の 1 層だけを
   担当する。兼業禁止
2. **Public domain = layer identity** — 外部 client 可視の domain は
   layer を直接表現する (`atproto`/`bsky`/`chat`/`signal`/`vault`/...)
3. **NSID prefix routing は表駆動** — `dispatch.ts` の if 連鎖を `ROUTING_TABLE`
   配列に畳み、コードは table lookup のみ
4. **Internal trust = 1 header + 1 verification** — 全 downstream Worker が
   同じ `x-etzhayyim-internal-trust` HMAC header を同じ方式で検証
5. **DID normalization は graph 側で 1 回** — profile / stats MV は root に
   正規化、post / record は raw を保持。frontend + middle tier は 正規化
   しない

## 目標トポロジー

```
                                 ┌─────────────────────┐
                                 │  Browser / Client   │
                                 │  (yoro / 3rd-party) │
                                 └──────────┬──────────┘
                                            │
   ┌────────────────────────────────────────┼────────────────────────────────┐
   │ Public XRPC / OAuth surface            │                                │
   ▼                                        ▼                                ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│atproto   │ │ bsky     │ │ chat     │ │ signal   │ │ vault    │ │ plc /did │ │murakumo  │
│.etzhayyim.com  │ │.etzhayyim.com  │ │.etzhayyim.com  │ │.etzhayyim.com  │ │.etzhayyim.com  │ │.etzhayyim.com  │ │.etzhayyim.com  │
│L1 PDS    │ │L2 AppView│ │L7 Chat   │ │L11 Key   │ │L12 Vault │ │L14 DID   │ │L13 Infer │
│+L4 Entry │ │          │ │          │ │ Dir      │ │          │ │ Dir      │ │ Fleet    │
└─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘
      │            │            │            │            │            │            │
      │ dispatch   │            │            │            │            │            │
      │ (NSID      │            │            │            │            │            │
      │  prefix    │            │            │            │            │            │
      │  table)    │            │            │            │            │            │
      ▼            ▼            ▼            ▼            ▼            ▼            ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│               RisingWave (graph DB) + HYPERDRIVE binding                             │
│  vertex_* / edge_* / mv_*_stats                                                      │
│  Write side: PDS (com.atproto.*) + actor Workers (com.etzhayyim.apps.*) direct INSERT      │
│  Read side:  AppView / Chat / Actor-Query / Coverage read-only SELECT                │
└──────────────────────────────────────────────────────────────────────────────────────┘

        ┌────────────────────────────────────────────────────────────┐
        │ Client App layer (Layer 9, separate from PDS)              │
        │                                                            │
        │   yoro.etzhayyim.com       Svelte SPA + SEO snapshot only        │
        │   (any 3rd-party)    Alternate client talks to atproto.*    │
        └────────────────────────────────────────────────────────────┘

        ┌────────────────────────────────────────────────────────────┐
        │ Actor Workers (Layer 10, N instances)                      │
        │                                                            │
        │   shinshi / animeka / yabai / lawfirm / kaikei / ...       │
        │   Each owns `com.etzhayyim.apps.<actor>.*` NSID                  │
        │   Receives viewer DID from PDS via trusted pipethrough     │
        └────────────────────────────────────────────────────────────┘
```

## Contract 1 — Worker 責務 (single responsibility)

| Worker | Domain | Layer | 公開 XRPC | Write 対象 | Read 対象 |
|---|---|---|---|---|---|
| **atproto.etzhayyim.com** | PDS + Entryway | 1 + 4 | `com.atproto.*` (local) + `/oauth/*` + `/.well-known/oauth-*` | repo commit / session / identity | commit log (`vertex_repo_commit`) + repo MST |
| **bsky.etzhayyim.com** | AppView | 2 | `app.bsky.{actor,feed,graph,notification}.*` | ❌ (read-only) | `vertex_repo_record` + feed/engagement MVs |
| **chat.etzhayyim.com** | Chat Service | 7 | `chat.bsky.convo.*` + `com.etzhayyim.convo.*` | `vertex_message` / `vertex_convo` | 同左 |
| **signal.etzhayyim.com** | Key Directory | 11 | `com.etzhayyim.signal.*` | `vertex_signal_prekey` | 同左 |
| **vault.etzhayyim.com** | Secret Vault | 12 | `com.etzhayyim.vault.*` | D1 ciphertext only | 同左 |
| **plc.etzhayyim.com** | DID Directory (plc) | 14 | `com.atproto.identity.resolveDid` (plc) + `com.etzhayyim.plc.*` | D1 plc operation log | 同左 |
| **did.etzhayyim.com** | DID Directory (etzhayyim) | 14 | `com.etzhayyim.identity.*` (etzhayyim method) | `vertex_etzhayyim_identity` | 同左 |
| **authn.etzhayyim.com** | Entryway AuthN | 4 | `/oauth/token` / `/sign-in` / `com.etzhayyim.auth.*` | session JWT / passkey / did doc | `AUTH_DB` D1 |
| **authz.etzhayyim.com** | Entryway AuthZ | 4 | `/manage` / `com.etzhayyim.authz.*` | api_key / linked method / org | `AUTH_DB` D1 + graph org tables |
| **murakumo.etzhayyim.com** | Inference Fleet | 13 | `com.etzhayyim.apps.murakumo.*` | inference log | cluster meta |
| **dispatcher.etzhayyim.com** | Process Orchestrator | 15 | BPMN-declared NSIDs (ADR-0056) | BPMN process state | 同左 |
| **yoro.etzhayyim.com** | Client App | 9 | **なし (SPA only)** — XRPC route 完全撤去 | ❌ | ❌ |
| **{actor}.etzhayyim.com** | Actor Worker × N | 10 | `com.etzhayyim.apps.{actor}.*` (内部 pipethrough 経由) | per-actor vertex/edge | 同左 |

**禁止**:
- 1 Worker が複数 layer を兼業する (ADR-2604231828 で yoro が違反していた型)
- Actor Worker が公開 XRPC route を直接持つ (PDS pipethrough 経由のみ)
- yoro.etzhayyim.com が `/xrpc/*` を serve する (Layer 9 違反)

## Contract 2 — NSID prefix routing (PDS dispatch の単一 SSoT)

`50-infra/cloudflare/workers/atproto/src/dispatch.ts` の if 連鎖を廃し、
**1 つの `ROUTING_TABLE` 配列** を正とする:

```ts
// 50-infra/cloudflare/workers/atproto/src/routing-table.ts (new)
export const NSID_ROUTING_TABLE: Array<{
  prefix: string;
  target: { kind: "local" } | { kind: "http"; env: string } | { kind: "binding"; env: string };
  trust: "public" | "internal";
}> = [
  // Layer 1 PDS local — canonical AT Protocol surface.
  { prefix: "com.atproto.",            target: { kind: "local" },                     trust: "public"   },
  // Layer 2 AppView.
  { prefix: "app.bsky.",               target: { kind: "http", env: "APPVIEW_URL" },  trust: "internal" },
  // Layer 7 Chat.
  { prefix: "chat.bsky.convo.",        target: { kind: "http", env: "CHAT_URL" },     trust: "internal" },
  { prefix: "com.etzhayyim.convo.",          target: { kind: "http", env: "CHAT_URL" },     trust: "internal" },
  // Layer 11 Key Directory.
  { prefix: "com.etzhayyim.signal.",         target: { kind: "http", env: "SIGNAL_URL" },   trust: "internal" },
  // Layer 12 Secret Vault.
  { prefix: "com.etzhayyim.vault.",          target: { kind: "http", env: "VAULT_URL" },    trust: "internal" },
  // Layer 14 DID Directory.
  { prefix: "com.etzhayyim.plc.",            target: { kind: "http", env: "PLC_URL" },      trust: "internal" },
  { prefix: "com.etzhayyim.identity.",       target: { kind: "http", env: "DID_etzhayyim_URL" }, trust: "internal" },
  // Layer 13 Inference Fleet.
  { prefix: "com.etzhayyim.apps.murakumo.",  target: { kind: "http", env: "MURAKUMO_URL" }, trust: "internal" },
  // Layer 15 Process Orchestrator — BPMN dispatched NSIDs.
  //   Allowlist is data, lives in a separate `BPMN_DISPATCHED_NSIDS` Set.
  //   Kept out of prefix table because match is exact, not prefix.
  // Layer 10 Actor Workers — longest-prefix match last.
  { prefix: "com.etzhayyim.apps.",           target: { kind: "http", env: "__ACTOR_URL__" }, trust: "internal" },
  //   __ACTOR_URL__ is resolved from the NSID itself: the 3rd segment
  //   (com.etzhayyim.apps.shinshi.*) maps to `https://shinshi.etzhayyim.com`.
];
```

`dispatchXRPC()` は この table を順番に scan し、最初に prefix match した
entry でルーティングする。新 layer / actor 追加 = table に 1 行足すだけ。

**Exact-match allowlist** (prefix では拾えないもの) は別 Set で管理:

```ts
// BPMN-dispatched NSIDs (ADR-0056). Exact match only — actor Worker
// fallback would otherwise catch them.
export const BPMN_DISPATCHED_NSIDS = new Set<string>([
  "com.etzhayyim.apps.yabai.flagEntity",
  "com.etzhayyim.apps.yabai.getFlags",
  // ...
]);
```

**禁止**: `dispatch.ts` 本体に `if (nsid.startsWith("...")) ...` を増やす
(全て table に書く)。

## Contract 3 — Internal trust plane

viewer DID の Worker 間 forwarding は **1 方式に統一**:

### HMAC-signed header (新、統一後)

PDS が downstream に出す 3 header:

```
x-etzhayyim-viewer-did:       did:web:alice.etzhayyim.com
x-etzhayyim-viewer-issued-at: 1745712345
x-etzhayyim-viewer-signature: <HMAC-SHA256(APPVIEW_INTERNAL_SECRET, "did|issued-at")>
```

downstream Worker:

1. 3 header の存在を確認
2. `issued-at` が 5 分以内
3. `APPVIEW_INTERNAL_SECRET` で HMAC を再計算、一致 → trust
4. 不一致 or 不在 → viewer=anonymous (reject しない、ただの downgrade)

### 廃止する方式

| 旧方式 | 理由 |
|---|---|
| `x-magatama-verified: true` header | spoofable、ADR-0023 P4 で deprecated と明記済み |
| `x-internal-trust` (plain-text secret) | HMAC でない、replay 可能 |
| hostname-based drop (yoro の `PUBLIC_YORO_HOSTS`) | coincidental defense、trust layer になっていない |
| `APPVIEW_SERVICE` service binding の "binding 存在" を trust の根拠にする | 環境依存、テストで偽装可能 |

### Secrets 一本化

`APPVIEW_INTERNAL_SECRET` を **全 downstream Worker で共有** (Secrets Store
entry 1 つ)。key rotation は Secrets Store の update + Worker 再 deploy で
実行。

## Contract 4 — DID 正規化 layer 分け

| 層 | DID 形 | 理由 |
|---|---|---|
| **Record table** (`vertex_repo_record` / `vertex_repo_commit` / edge tables) | **raw** (path-DID のまま保持) | AT URI の identity を壊さない、getPostThread などの完全一致 lookup が成立 |
| **Count / Stats MV** (`mv_actor_social_stats` / `mv_profile_page_stats` / `mv_world_coverage_live`) | **root (3-segment)** | `postsCount` 等は profile root = actor の単位で集計するのが user-facing 正解 |
| **Middle tier** (PDS dispatch / bsky handler) | raw のまま pass-through | 正規化責務を持たない |
| **Client frontend** (yoro) | server 返値をそのまま表示。`actor.postsCount ?? feedItems.length` のような複合 fallback 禁止 | 正規化/集計は server が行う契約 |

### 対応 migration

- `mv_actor_social_stats` の GROUP BY を `normalize_actor_did(repo)` に変更
  (現在 raw `repo` で GROUP BY → path-DID が見えない)
- `mv_profile_page_stats` は既に `normalize_actor_did()` 経由だが、
  上流 MV が raw だと合わない → 上流を直せば連動
- feed handler は **変更不要** (`repo LIKE 'did:web:x.etzhayyim.com:%'` で既に
  sub-actor を集約)
- yoro `AgentProfile.svelte:460` の `??` 演算子を `actor.postsCount > 0 ?
  actor.postsCount : feedItems.length` に修正

## Contract 5 — Client → server endpoint 単一化

**yoro + 3rd-party client の XRPC 到達点は `atproto.etzhayyim.com` 1 つだけ**に
する。以下を禁止:

- `yoro.etzhayyim.com/xrpc/*` への直接アクセス (yoro は Layer 9 Client App、
  `/xrpc/*` route を持たない)
- `{actor}.etzhayyim.com/xrpc/*` への直接アクセス (actor Worker は internal のみ、
  PDS pipethrough 経由で叩く)
- browser code から `bsky.etzhayyim.com/xrpc/*` を直接呼ぶ (PDS の
  pipethroughAppView を介する)

**例外**: Client App が viewer identity を提示せず (anonymous) read-only で
叩く場合、`bsky.etzhayyim.com` に直接アクセスしてよい (federation-ready の布石)。
ただし yoro frontend はこのパスを **使わない** (atproto.etzhayyim.com 経由で統一)。

### DID Document `service[]` (ADR-2604231839 の補強)

全 did:web user / actor の DID Doc は以下の service 宣言を持つ:

```json
{
  "service": [
    {"id":"#atproto_pds",  "type":"AtprotoPersonalDataServer", "serviceEndpoint":"https://atproto.etzhayyim.com"},
    {"id":"#bsky_appview", "type":"BskyAppView",               "serviceEndpoint":"https://bsky.etzhayyim.com"},
    {"id":"#bsky_chat",    "type":"BskyChatService",           "serviceEndpoint":"https://chat.etzhayyim.com"}
  ]
}
```

3rd-party client がこの DID Doc を resolve すれば atproto / bsky / chat を
自力で見つけられる。yoro は atproto 経由で済ます (自分の宣言を無視)。

# Migration

既存 ADR の Phase を本 ADR の contract に対応付ける:

| Step | Contract | 依存 ADR | 現状 |
|---|---|---|---|
| 1 | Contract 1 — bsky.etzhayyim.com 自立 | 2604231828 Phase 1-3 | ⏳ deploy 未実行 (コード ready) |
| 2 | Contract 2 — NSID routing table 抽出 | 本 ADR 新規 | ❌ 未実装 (`dispatch.ts` にベタ書き) |
| 3 | Contract 3 — HMAC trust header 統一 | 本 ADR 新規 | ❌ 4 通りの方式が並存 |
| 4 | Contract 4 — MV root 集約 | 本 ADR 新規 | ❌ 上流 MV は raw repo で GROUP BY |
| 5 | Contract 5 — yoro `/xrpc/*` 完全撤去 | 2604231828 A2 | ⚠️ app.bsky.* は外したが convo/signal/chat proxy 残存 |
| 6 | chat.etzhayyim.com 新設 (Layer 7 専用 Worker) | 本 ADR 新規 | ❌ 現在は PDS に内包 |
| 7 | signal.etzhayyim.com public route 化 | ADR-2604231811 Layer 11 | ⏳ Worker 存在、PDS 内で handling |
| 8 | DID Doc `service[]` 全 entry 更新 | ADR-2604231839 / 2604231828 | ⏳ 一部 |

## Phase 配列 (実施順)

### Phase α — Stop the bleeding (即時、operational) ✅ landed 2026-04-24/25

- α1: **bsky.etzhayyim.com 実デプロイ** (`wrangler deploy` on `etzhayyim-appview`)
  ✅ live at version `d085c7bf`. smoke `sh1n5h1x.etzhayyim.com postsCount=1476`.
  Initial deploy `132f93d5` exposed the RW parameterized-LIMIT incompat
  → second-stage fix `4c059628` (β2 lesson, see below).
- α2: yoro `postsCountDisplay` の `??` bug 修正 ✅ shipped via PR #1115.
- α3: MV root 正規化 migration `20260424014529_mv_actor_social_stats_root_normalization`
  ✅ applied (out-of-band via `apply-pending.sh`). `mv_actor_social_stats`
  + `mv_actor_canonical_did` + `mv_profile_core_stats` rebuilt with
  `normalize_actor_did(repo)`.

### Phase β — Routing table 抽出 (構造改善、1 PR) ✅ landed pre-2026-04-24

- β1: `routing-table.ts` 新規作成、既存 `dispatch.ts` の pipethrough を
  table 経由に書き換え。行数大幅減。
- β2: `BPMN_DISPATCHED_NSIDS` を別 Set に分離 ✅ since retired
  2026-04-24 — all callers migrated to `resolveExactMatchEntry`.
- β3: test: NSID → target の mapping を完全網羅する table-driven test
  ✅ `routing-table.test.ts` (16 cases).

### Phase γ — Trust plane 統一 (1 PR) ✅ landed via PR #1115

- γ1: `middleware/trust.ts` 新規 ✅
- γ2: PDS dispatch 全 pipethrough を HMAC header 経由に変更 ✅. Currently
  in **14-day observation window** (started 2026-04-24).
  - Tally log: `90-docs/260424-legacy-trust-tally.log`.
  - Day 2 / 14 status: 4 consecutive zero-hit samples
    (matched_true=0 / matched_false=0).
  - LaunchAgent `com.etzhayyim.legacy-trust-tally.plist` fires daily 09:17
    local through 2026-05-08; one-shot cleanup at
    `70-tools/scripts/cleanup-legacy-trust-headers.sh` (DRY_RUN
    verified 2026-04-24).
- γ3: downstream Worker 全てに trust middleware を install ✅
  (atproto / appview / chat / signal).
- γ4: 旧方式全廃 ⏳ — gated on the γ2 14-day window closing clean.

#### Phase γ2 automation status (2026-04-24)

γ2 is in the 14-day observation window and is the first cutover on this
repo run as a **one-button cutover**: every gate, probe, and rollback
artifact is wired up before the flip so the operator never touches more
than a single `wrangler deploy` command.

| Artifact | Path | Role |
|---|---|---|
| Runbook | `90-docs/260424-legacy-trust-headers-cutover-runbook.md` | Declares the flip (`LEGACY_TRUST_HEADERS: on → off`), the 3 gates, the rollback, and the 14-day post-flip window. Ephemeral — deleted at cleanup. |
| Observation probe (script) | `70-tools/scripts/legacy-trust-tally-probe.sh` | 60s `wrangler tail` sample of `etzhayyim-appview` Worker, counts `[trust][legacy] hit ... matched=true\|false`, appends one row per day to `90-docs/260424-legacy-trust-tally.log`. |
| Observation scheduler | `50-infra/launchd/com.etzhayyim.legacy-trust-tally.plist` | macOS LaunchAgent firing the probe daily at 09:17 local. Chosen over Claude's `/schedule` because the γ2 gate spans 14 days and Claude's runtime caps scheduled tasks at 7d. |
| Preflight validator | (not needed for γ2; see γ siblings) | The γ2 flip has a single binary gate (0 hits for 14d). The sibling strict-mode cutover has one: `50-infra/cloudflare/workers/atproto/scripts/oauth-strict-mode-preflight.sh`. |
| Pre-written cleanup script | `70-tools/scripts/cleanup-legacy-trust-headers.sh` | DRY_RUN-capable. On the T+14d cleanup day: drops `LEGACY_TRUST_HEADERS` env var from 4 wranglers, removes the `emitLegacy` branch from `dispatch.ts`, simplifies `trustedViewerDid()` in the AppView to HMAC-only. One invocation produces the commit-ready diff. |
| Post-flip cutover smoke | `70-tools/scripts/sh1n5h1x-profile-smoke.sh` | Not γ2-specific — verifies the sibling `mv_actor_social_stats` root-normalization fix. The pattern applies: end-to-end assertion that the cutover actually fixed the target bug. |

The same 5-artifact kit (runbook / probe / scheduler / cleanup / smoke)
is the template for future ephemeral cutovers. A γ3+ cutover starts by
copying these files + editing the probe regex + the cleanup transforms,
not by re-inventing the observation cadence.

Design constraint surfaced while building this: **Claude scheduled
tasks are not the right home for multi-week observation windows.**
7-day cap + session binding rule them out. macOS launchd / systemd
timers are the load-bearing piece; Claude's cron is at most a same-day
reminder.

### Phase δ — Chat / Signal / Murakumo を public worker に分離

- δ1: `chat.etzhayyim.com` new Worker (Layer 7) — PDS から convo 関連を move out
- δ2: `signal.etzhayyim.com` を public XRPC route (現在 internal のみ)
- δ3: `murakumo.etzhayyim.com` を public route (Layer 13 正式化)

### β2 lesson (2026-04-24, appview initial rollout)

Budget two deploys for any new Worker whose XRPC handlers query
RisingWave directly — the first deploy will almost always expose a
PG-vs-RW parse-incompatibility that has to be fixed before the
topology is actually live.

The etzhayyim-appview rollout that covered this ADR's Phase 3 split
shipped in two passes on 2026-04-24:

1. **Initial deploy** (version `132f93d5`) — route claimed,
   HYPERDRIVE bound, Worker returning profile DID correctly. But
   `postsCount=0` for every actor because the `.limit(1)` in the
   mv_actor_social_stats query generated `LIMIT $N` and RW's
   sql_parser rejected the parameterized LIMIT on MV SELECTs
   specifically. The handler's fallback path used strict
   `repo = actorDid` and missed path-DID posts, exactly the bug
   the upstream MV migration was supposed to fix.
2. **Fix + redeploy** (version `4c059628` → `ffdfd6f2`) — swap
   Kysely's `.executeTakeFirst()` / `.limit(1)` for a `sql`
   template that inlines `LIMIT 1`. postsCount went 0 → 1425 on
   sh1n5h1x.etzhayyim.com. feed.ts:263 had the same latent bug for
   viewer-context reads; patched in the same session.

Generalization: **any MV query in a new Worker needs an inline
`LIMIT N` literal, not a parameterized one.** Kysely generates the
parameterized form by default. Treat it as the first thing to grep
for during code review of a new RW-backed Worker; catch it before
the first deploy if you can, expect to redeploy if you can't.

The wrangler-tail warn line we caught this on —

```
(warn) [appview:getProfile] social stats query failed: error: Failed
to prepare the statement ... expects an integer ... after LIMIT, but
found non-const expression
```

is the canonical signature. Future Worker deploys against RW should
grep for this pattern before declaring the Phase green.

### Phase ε — yoro 最終浄化

- ε1: yoro `/xrpc/*` route を完全削除 (convo/signal/chat proxy も撤去 — 各
  client は atproto.etzhayyim.com 経由で本家を叩く)
- ε2: yoro の `PDS_SERVICE` binding を read-only pattern に閉じ込め (SSR +
  SEO snapshot 専用、XRPC 本番パスにしない)
- ε3: yoro package.json から `@etzhayyim/graph-schema` を remove (AppView 依存
  は appview Worker に閉じる)

### Phase ζ — DID Doc service[] 完全同期

- ζ1: `etzhayyim dns-sync` の副作用として DID Doc publisher を追加
- ζ2: 全 user / actor DID Doc を一斉更新 (service 配列 3 entry)
- ζ3: DID Doc validation test

# Consequences

## Positive

- **新 Worker 追加の成本が下がる** — `routing-table.ts` に 1 行 + Worker deploy
  だけで済む (今は dispatch.ts に if 追加 + deploy)
- **"どの NSID がどの Worker に行くか" が 1 ファイルで見える** — debugging
  速度が体感 3x
- **Trust plane の脆弱性が 1 箇所に集約** — rotation / audit が楽
- **yoro = Layer 9 に純化** — Svelte SPA deploy の blast radius が最小化
- **MV 層で DID 正規化が一度だけ** — `postsCount: 0` bug のようなものが
  構造的に起きなくなる
- **AT Protocol federation-ready** — DID Doc service[] 宣言で 3rd-party
  AppView / Chat と互換可能

## Negative

- **Phase β-ζ は全部合計で 5 deploy 程度** — タイミング調整が必要
- **chat.etzhayyim.com 新設は PDS の convo handler を外科的に切り出し**。既存
  client 全て atproto.etzhayyim.com 経由で叩いている前提が壊れないように
  pipethrough で吸収
- **DID Doc 一斉更新 (Phase ζ) は署名鍵を持つ authn Worker を経由** — 一度
  にやると rate limit リスク。段階配布 (100 DID/hour) 推奨

## Neutral

- `atproto.etzhayyim.com` 単一入口の原則は維持 (external client には単純)
- Actor Worker 群 (Layer 10、189 instance) は本 ADR で一切触らない — 既に
  Layer 10 として正しく動いている
- BPMN dispatcher (ADR-0056) は Layer 15 として本 ADR の外 — table に 1 行
  加えるだけで routing 統合される

# Non-Goals

- Worker 数の最小化 (Shannon 最小 η を追求しない — responsibility 分離優先)
- RisingWave graph schema 変更 (別 ADR、別 topology)
- etzhayyim CLI の `atproto.etzhayyim.com` 以外への直結化 (client simplification 優先)
- DPoP nonce の RS 側以外への拡大 (ADR-2604240914 が locus)
- Actor Worker の public route 化 (internal のまま、PDS pipethrough 維持)

# Alternatives Considered

## A1. 現状維持 (ad-hoc refactor を続ける)

- pros: 作業量 0
- cons: dispatch.ts が 1500 行 → 2000 行と育ち続ける、新 layer 追加が恐怖
  感を伴う作業になる。**却下**

## A2. PDS に全部詰める (bsky / chat / signal / vault を PDS 内 handler に戻す)

- pros: deploy 1 Worker で済む
- cons: ADR-2604231811 / 2604231828 が明示的に却下した設計。AT Protocol
  self-hosting guide 非準拠、federation 不能、scaling ボトルネック。**却下**

## A3. Actor Worker も public route 化 (`{actor}.etzhayyim.com/xrpc/*` を公開)

- pros: yoro などが actor に直接話せる
- cons: 189 Worker × 公開 endpoint = auth / rate limit / audit が 189 面。
  PDS pipethrough の内部 trust model が崩れる。**却下**

## A4. 全部 AT Protocol service endpoint resolver で解決 (DID Doc service[] 経由で client が直接各 Worker に接続)

- pros: federation 的に最もクリーン
- cons: 現 yoro client は `atproto.etzhayyim.com` 固定前提。client code 大幅書き
  換え + DID Doc publish 完全稼働が前提 → ε/ζ Phase の後にならないと
  無理。**将来方向として採用、本 ADR の end state が整ってから次 ADR で
  実装**

## A5. NSID routing を runtime DB lookup にする (deps.toml を直接 PDS が読む)

- pros: 新 actor 追加で PDS redeploy 不要
- cons: hot path で毎 request DB lookup = latency 追加。static table + PDS
  redeploy で 1 次情報の reliability が勝る。**却下**

# References

## 前段 ADR

- ADR-2604231811 (15-layer taxonomy) — **Worker = 1 layer の根拠**
- ADR-2604231828 (AppView domain split) — Phase 1-3 で既実装、本 ADR は
  Phase 4+ の位置
- ADR-2604231821 (OAuth snake_case) — Entryway (L4) の wire format 契約
- ADR-2604240914 (OAuth server lifecycle) — revoke / introspect
- ADR-2604231839 (DID Doc custom service) — Phase ζ の根拠
- ADR-0022 / 0023 (auth topology) — Trust plane の 2/4-layer 基盤
- ADR-0081 (Worker-direct Hyperdrive) — actor Worker の write path 契約
- ADR-0056 (BPMN-as-actor) — Layer 15 の取り扱い
- ADR-0087 (MCP facade) — actor Worker の MCP export 契約

## 実装 citations (痛みの現物)

- `50-infra/cloudflare/workers/atproto/src/dispatch.ts` — A/B/C の根拠
- `50-infra/cloudflare/workers/atproto/src/auth/verify.ts:472-493` — D の根拠
- `30-graph/graph-schema/migrations/0015_actor_social_stats_mv.ts:36` — E の根拠 (raw repo GROUP BY)
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/routes/profile/[handle]/AgentProfile.svelte:460` — E の user-facing 表面
- 2026-04-24 観測 post: `at://did:web:sh1n5h1x.etzhayyim.com:shigeo-kageyama-mob-psycho-100/app.bsky.feed.post/3mk7ebsxqdg2x`
