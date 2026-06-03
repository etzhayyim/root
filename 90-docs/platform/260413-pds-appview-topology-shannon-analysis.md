# PDS/AppView Topology — Shannon Analysis (2026-04-13)

## Platform Scale

| Metric | Count |
|---|---|
| Mitama actors (DID) | 62 |
| Projects (60-apps/) | 121 |
| Nono Workers (CF infra) | 11 |
| DID references in deps.toml | 92 |
| Lexicon JSON contracts | 2,440 |
| Unique NSIDs in PDS etzhayyim handler | 186 |
| Unique NSIDs in PDS feed handler | 59 |
| Unique NSIDs in PDS server handler | 174 |
| Unique NSIDs in PDS repo handler | 57 |
| CF Workers (infra) | 10 |

## Bluesky Reference Architecture (AT Protocol 公式)

```
Client (bsky.app)
  │ BskyAppAgent
  │ service: https://bsky.social (PDS, 別オリジン)
  │
  ▼
PDS (bsky.social) — 唯一の gateway
  │
  ├─ com.atproto.*       → PDS 直接処理 (repo CRUD, auth, sync)
  │
  ├─ app.bsky.*          → atproto-proxy: {DID}#bsky_appview
  │                        pipethrough → AppView (api.bsky.app)
  │                        + read-after-write merge
  │
  ├─ chat.bsky.*         → atproto-proxy: {DID}#bsky_chat
  │                        proxy → Chat Service (別サービス)
  │                        ※ chat message は repo に保存しない
  │                        ※ Chat Service が独自ストレージに保存
  │
  └─ Write (like/follow/post) → PDS 直接処理 (= createRecord → repo)
```

**Key facts:**
- Client は PDS にのみ接続。AppView/Chat Service の URL を知らない
- PDS が `atproto-proxy` ヘッダーで service routing
- `chat.bsky.*` も PDS 経由。ただし PDS は透過 proxy のみ (repo に保存しない)
- `app.bsky.*` read は AppView から返るが、PDS が read-after-write で local write をマージ
- Web frontend (bsky.app) と PDS (bsky.social) は別オリジン

## 5 Architecture Candidates — Shannon Comparison

### 変数定義

- **N** = unique NSID count (~476: etzhayyim 186 + feed 59 + server 174 + repo 57)
- **A** = actor/DID count (62 actors + path DIDs)
- **P** = project count (121)
- **W** = CF Worker count
- **H** = hop count (request path length)
- **R** = rewrite rule count (NSID mapping)
- **D** = code duplication (handler implementations)
- **η** = Shannon efficiency = 1 - (redundancy bits / total bits)

### Candidate A: Current (yoro gateway + NSID rewrite)

```
Client → yoro.etzhayyim.com (gateway + AppView + SPA)
  ├─ com.etzhayyim.yoro.*     → local handler (5 implemented) or PDS fallback
  ├─ com.etzhayyim.atproto.*  → rewrite → com.atproto.* → PDS proxy
  ├─ com.etzhayyim.convo.*    → transparent proxy → PDS
  └─ app.bsky.*         → PDS proxy (compat)
```

| Factor | Value | Bits |
|---|---|---|
| Workers | 2 (yoro + PDS) | — |
| Hop (read, implemented) | 1 (yoro → HYPERDRIVE) | 0 |
| Hop (read, fallback) | 2 (yoro → PDS → HYPERDRIVE) | 1 |
| Hop (write) | 2 (yoro → PDS) | 1 |
| NSID rewrite rules | ~10 (prefix mapping) | 3.3 |
| Handler duplication | 5 handlers exist in both yoro + PDS | 2.3 |
| Namespace overhead | 476 NSIDs × 2 prefixes (yoro + atproto) | 1.0 |
| Federation compat | Low (custom NSID, no atproto-proxy) | 3.0 |
| **η** | | **0.72** |

### Candidate B: AT Protocol 準拠 (PDS gateway + atproto-proxy)

```
Client → atproto.etzhayyim.com (PDS = gateway)
  ├─ com.atproto.*       → PDS direct
  ├─ app.bsky.* (read)   → atproto-proxy → yoro AppView
  ├─ app.bsky.* (write)  → PDS direct (createRecord)
  ├─ chat.bsky.*         → atproto-proxy → Convo Service
  └─ com.etzhayyim.*           → PDS direct or proxy
```

| Factor | Value | Bits |
|---|---|---|
| Workers | 2-3 (PDS + yoro AppView + optional Convo) | — |
| Hop (read) | 2 (Client → PDS → AppView) | 1 |
| Hop (write) | 1 (Client → PDS) | 0 |
| NSID rewrite rules | 0 (standard NSID, atproto-proxy routing) | 0 |
| Handler duplication | 0 (PDS pipethrough, AppView is sole handler) | 0 |
| Namespace overhead | 0 (app.bsky.* / com.atproto.* そのまま) | 0 |
| Federation compat | Full (AT Protocol standard) | 0 |
| SPA 配信 | yoro.etzhayyim.com は SPA のみ。XRPC は PDS origin | 0.5 |
| CORS overhead | Client (yoro.etzhayyim.com) → PDS (atproto.etzhayyim.com) cross-origin | 0.5 |
| **η** | | **0.93** |

### Candidate C: Hybrid (yoro SPA + PDS gateway + AppView service binding)

```
yoro.etzhayyim.com — SPA 配信のみ (static assets)
Client JS → atproto.etzhayyim.com (PDS = gateway, cross-origin)
  ├─ com.atproto.* → PDS direct
  ├─ app.bsky.*    → PDS pipethrough → yoro AppView Worker (service binding)
  └─ com.etzhayyim.*     → PDS direct or proxy
```

| Factor | Value | Bits |
|---|---|---|
| Workers | 2 (PDS + yoro AppView) | — |
| Hop (read) | 2 (Client → PDS → AppView, service binding <1ms) | 1 |
| Hop (write) | 1 (Client → PDS) | 0 |
| NSID rewrite | 0 | 0 |
| Handler duplication | 0 (pipethrough) | 0 |
| Namespace overhead | 0 | 0 |
| Federation compat | Full | 0 |
| CORS | 1 (cross-origin to PDS) | 0.5 |
| SPA/API 分離 | Clean (yoro = SPA, PDS = API) | 0 |
| **η** | | **0.95** |

### Candidate D: yoro 統合 (SPA + PDS proxy + AppView, 同一オリジン)

```
yoro.etzhayyim.com — SPA + XRPC endpoint
  ├─ /* (static)     → Workers Assets (SPA)
  ├─ /xrpc/app.bsky.* (read)  → yoro AppView local (HYPERDRIVE)
  ├─ /xrpc/app.bsky.* (write) → PDS proxy (service binding)
  ├─ /xrpc/com.atproto.*      → PDS proxy (service binding)
  ├─ /xrpc/chat.bsky.*        → PDS proxy → Convo handler
  └─ /xrpc/com.etzhayyim.*          → PDS proxy
atproto.etzhayyim.com — PDS (federation endpoint, external clients)
```

| Factor | Value | Bits |
|---|---|---|
| Workers | 2 (yoro + PDS) | — |
| Hop (read) | 1 (Client → yoro HYPERDRIVE) | 0 |
| Hop (write) | 2 (Client → yoro → PDS) | 1 |
| NSID rewrite | 0 (app.bsky.* そのまま使用) | 0 |
| Handler duplication | Feed/Actor read のみ yoro に実装、PDS にも残す (federation 用) | 1.0 |
| Namespace overhead | 0 (標準 NSID) | 0 |
| Federation compat | Full (PDS は app.bsky.* を直接処理可能) | 0 |
| CORS | 0 (同一オリジン) | 0 |
| Write hop overhead | yoro 経由は不要だが同一オリジン制約上やむなし | 0.5 |
| Read-after-write | yoro で実装必要 | 0.5 |
| **η** | | **0.90** |

### Candidate E: PDS 統合 (SPA + PDS + AppView 全統合)

```
atproto.etzhayyim.com — PDS + AppView + SPA 全統合
  ├─ /* (static)           → Workers Assets (SPA)
  ├─ /xrpc/com.atproto.*   → PDS direct
  ├─ /xrpc/app.bsky.*      → AppView direct (HYPERDRIVE)
  ├─ /xrpc/chat.bsky.*     → Convo handler direct
  └─ /xrpc/com.etzhayyim.*       → Platform handlers direct
yoro.etzhayyim.com → 301 redirect → atproto.etzhayyim.com
```

| Factor | Value | Bits |
|---|---|---|
| Workers | 1 (全統合) | — |
| Hop (read) | 1 (Client → HYPERDRIVE) | 0 |
| Hop (write) | 1 (Client → PDS direct) | 0 |
| NSID rewrite | 0 | 0 |
| Handler duplication | 0 | 0 |
| Namespace overhead | 0 | 0 |
| Federation compat | Full | 0 |
| CORS | 0 (同一オリジン) | 0 |
| Monolith risk | High (476 NSIDs in 1 Worker, 128MB memory limit) | 2.0 |
| Bundle size | ~391KB etzhayyim + 82KB feed + 65KB server + 80KB repo ≈ 618KB | 1.5 |
| Deploy blast radius | Any change affects entire stack | 1.0 |
| **η** | | **0.82** |

## Summary

| Candidate | Description | η | Read hop | Write hop | NSID rewrite | Federation | CORS |
|---|---|---|---|---|---|---|---|
| **A** | yoro gateway + com.etzhayyim.yoro.* rewrite (現状) | **0.72** | 1-2 | 2 | ~10 rules | Low | No |
| **B** | AT Protocol 準拠 (PDS gateway + atproto-proxy) | **0.93** | 2 | 1 | 0 | Full | Yes |
| **C** | Hybrid (yoro SPA only + PDS gateway + AppView binding) | **0.95** | 2 | 1 | 0 | Full | Yes |
| **D** | yoro 統合 (SPA + AppView + PDS proxy, 同一オリジン) | **0.90** | 1 | 2 | 0 | Full | No |
| **E** | PDS 全統合 (monolith) | **0.82** | 1 | 1 | 0 | Full | No |

## Recommendation

**Candidate C (η=0.95)** が最適。

理由:
1. **AT Protocol 完全準拠** — PDS が gateway、atproto-proxy で service routing
2. **Handler 重複ゼロ** — PDS は pipethrough、AppView が sole handler
3. **NSID rewrite ゼロ** — app.bsky.* / com.atproto.* をそのまま使用
4. **Federation 対応** — 外部 AT Protocol client が PDS に直接接続可能
5. **SPA/API 分離** — yoro.etzhayyim.com は static assets のみ、API は PDS origin
6. **CORS は 1 箇所** — Client → PDS の cross-origin のみ (CF Workers で容易)
7. **Service binding** — PDS → yoro AppView は same-account Workers RPC (<1ms)

**Candidate A (現状) は η=0.72 で最低。** NSID rewrite + handler 重複 + custom namespace が redundancy を生んでいる。

## Decision: Candidate C — Implemented (2026-04-14)

Migration A → C 完了。

### Implementation

| Step | Status | File |
|---|---|---|
| `@etzhayyim/wproto` NSID を `app.bsky.*` / `com.atproto.*` に戻す | ✅ | `10-protocol/wproto/src/service.ts` |
| `@etzhayyim/wproto` 接続先を `atproto.etzhayyim.com` (PDS direct) | ✅ | `10-protocol/wproto/src/client.ts` |
| PDS に `pipethroughAppView()` 実装 | ✅ | `50-infra/cloudflare/workers/atproto/src/dispatch.ts` |
| PDS に `APPVIEW_SERVICE` binding 追加 | ✅ | `50-infra/cloudflare/workers/atproto/wrangler.jsonc` |
| yoro から XRPC gateway/proxy/rewrite 全削除 | ✅ | `60-apps/.../yoro-ui-g00h5zto/src/app.ts` |
| yoro に `handleAppViewRpc()` (service binding entrypoint) | ✅ | `60-apps/.../yoro-ui-g00h5zto/src/app.ts` |
| CORS ヘッダー (PDS) | ✅ (既存) | `50-infra/.../middleware/index.ts` (origin reflect) |
| Frontend wrapper 簡素化 | ✅ | `svelte/src/lib/graph/feed.ts` |

### AppView Handlers (yoro Worker, HYPERDRIVE direct)

| NSID | Handler | File |
|---|---|---|
| `app.bsky.actor.getProfile` | `handleGetProfile` | `src/appview/profile.ts` |
| `app.bsky.actor.searchActors` | `handleSearchActors` | `src/appview/search.ts` |
| `app.bsky.feed.getTimeline` | `handleGetTimeline` | `src/appview/feed.ts` |
| `app.bsky.feed.getDiscoverFeed` | `handleGetDiscoverFeed` | `src/appview/feed.ts` |
| `app.bsky.feed.getAuthorFeed` | `handleGetAuthorFeed` | `src/appview/feed.ts` |
| その他 `app.bsky.*` read | 501 → PDS local fallback | — |

### Blast Radius

| 対象 | 数 | 影響 |
|---|---|---|
| T1 Actors | 57 | なし |
| T3 App Workers (sdk.pds.dispatch) | 189 | なし — PDS API 不変 |
| App wrangler (PDS_SERVICE binding) | 214 | なし — binding 先不変 |
| yoro Svelte (client-side) | 79 files | 自動切り替え — `@etzhayyim/wproto` が PDS direct |
| 他 app Svelte | 0 | なし — `@etzhayyim/wproto` client 未使用 |
| PDS dispatch.ts | 1 file | pipethrough 追加 (appview layer read のみ) |
| PDS wrangler.jsonc | 1 file | APPVIEW_SERVICE binding 追加 |

### Topology Diagram

```
Browser (yoro.etzhayyim.com SPA)
  │ @etzhayyim/wproto AtpAgent(service: atproto.etzhayyim.com)
  │ app.bsky.* / com.atproto.* (AT Protocol 標準)
  ▼
atproto.etzhayyim.com (PDS — sole gateway)
  ├─ com.atproto.repo.* → PDS direct (repo write)
  ├─ app.bsky.feed.like/follow → PDS direct (= createRecord)
  ├─ app.bsky.feed.getTimeline (read, layer=appview)
  │   → pipethroughAppView() → APPVIEW_SERVICE (service binding <1ms)
  │     → yoro Worker handleAppViewRpc() → HYPERDRIVE → RisingWave
  │   → 501? → PDS local handler fallback
  ├─ com.etzhayyim.convo.* → PDS direct (convo handler)
  ├─ com.etzhayyim.signal.* → PDS direct (signal handler)
  └─ com.etzhayyim.projector.* → PDS direct

210 App Workers (server-side, 変更なし)
  sdk.pds.dispatch() → PDS_SERVICE binding → PDS direct

57 T1 Actors (変更なし)
  PDS Shared Executor (内部実行)
```
