# news.etzhayyim.com Two-Worker Split Design

## Goal

`news.etzhayyim.com` の現状は 1 つの worker に以下が同居している。

- SvelteKit SSR/public page rendering
- `/xrpc/...` の XRPC backend
- jobs / scheduler / ingestion / translation / quality evaluation

これを **UI worker** と **backend worker** の 2 worker に分離し、公開配信面と業務処理面の責務・デプロイ・スケーリング・障害影響範囲を切り分ける。

## Current State

現状の混在点:

- [`60-apps/etzhayyim-project-news/wasm/news-core-component/etzhayyim.json`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-news/wasm/news-core-component/etzhayyim.json) で `news.etzhayyim.com` と `news-core.etzhayyim.com` を同一 worker に割り当て
- [`60-apps/etzhayyim-project-news/wasm/news-core-component/kotodama.toml`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-news/wasm/news-core-component/kotodama.toml) で `/api/...` と static 配信を同居
- [`60-apps/etzhayyim-project-news/wasm/news-core-component/svelte/src/lib/server/connect.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-news/wasm/news-core-component/svelte/src/lib/server/connect.ts) と [`60-apps/etzhayyim-project-news/wasm/news-core-component/svelte/src/lib/connect.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-news/wasm/news-core-component/svelte/src/lib/connect.ts) がどちらも相対パス `/xrpc/...` を前提
- [`60-apps/etzhayyim-project-news/wasm/news-core-component/main.go`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-news/wasm/news-core-component/main.go) が query/command に加えて生成・翻訳・品質評価・進化まで同一 app に保持

この構成だと、SSR の変更が backend deploy を巻き込み、逆に jobs や graph 起因の不安定化が public page latency に波及する。

## Design Principles

- `news.etzhayyim.com` の公開入口は UI worker を正とする
- backend worker は XRPC / job / internal API 専用に寄せる
- public mutation 用 REST は増やさない。業務 API は XRPC を維持する
- SSR worker は read-mostly。write-heavy/job-heavy 処理を持たない
- SEO/ISR cache と editorial/job runtime を分離する
- 同一 app semantic は維持するが、deployable unit は 2 つに分ける

## Target Topology

```text
Browser / Crawler
  -> news.etzhayyim.com                (UI worker)
      - SvelteKit SSR
      - ISR cache
      - static assets
      - BFF route (/xrpc public query subset)
      - optional signed internal fetch to backend

  -> news-api.etzhayyim.com            (backend worker, private/public limited)
      - XRPC CommandService / QueryService
      - jobs, scheduler, ingest, translate, quality, evolve
      - Cypher / KV / W Protocol / cross-actor
      - admin/internal routes
```

推奨ホスト:

- `news.etzhayyim.com`: public UI
- `api.news.etzhayyim.com` または `news-api.etzhayyim.com`: backend public/internal endpoint
- `news-core.etzhayyim.com`: 既存互換 alias として段階的に backend 側へ寄せる

## Worker Responsibilities

### 1. UI Worker

責務:

- SvelteKit SSR
- ISR / cache revalidation
- article detail, listing, category, localized landing pages
- SEO metadata, sitemap, robots, JSON-LD response shaping
- browser-facing BFF

保持してよいもの:

- `QueryService` のうち public read に必要な呼び出し
- edge cache
- locale negotiation
- feature flag / AB test / ad slot shaping

持たないもの:

- article ingest / generation / translation / evaluation
- scheduler / cron / queue drain
- direct Cypher write
- internal admin command

### 2. Backend Worker

責務:

- `NewsCommandService`
- `NewsQueryService` の authoritative implementation
- jobs (`/jobs/...`, `/scheduler/...`) と cron entrypoint
- RSS collection, dedupe, normalize, generate, translate, quality gate
- W Protocol / cross-actor / graph / KV access

追加ルール:

- public に開く query は allowlist で制限
- command 系は UI worker 経由ではなく admin/internal caller のみ許可
- org/capability/clearance enforcement は backend 側を source of truth とする

## API Boundary

### Public contract

外部 client からの標準入口は引き続き `/xrpc/...` だが、実体は UI worker 上の BFF とする。

```text
Browser
  -> news.etzhayyim.com/xrpc/etzhayyim.news.v1.NewsQueryService/ListArticles
      UI worker validates + caches + proxies
        -> news-api.etzhayyim.com/xrpc/etzhayyim.news.v1.NewsQueryService/ListArticles
```

### Query split

public query と internal query を分ける。

- public query
  - `ListArticles`
  - `GetArticle`
  - `ListFeeds` の public subset
- internal query
  - quality queue
  - draft view
  - editorial metrics
  - source diagnostics

### Command split

command は backend worker だけが受ける。

- `IngestArticle`
- `GenerateArticle`
- `CollectRSS`
- `EvaluateArticle`
- `EvaluateBatch`
- `TranslateArticle`
- `TranslateToAll`
- `Evolve`

必要なら proto 上も次へ整理する。

- `NewsPublicQueryService`
- `NewsEditorialQueryService`
- `NewsCommandService`
- `NewsJobsService`

少なくとも deploy boundary と auth boundary は proto 名称でも見えるようにした方がよい。

## Routing Model

### External routing

- `news.etzhayyim.com/*` -> UI worker
- `news.etzhayyim.com/xrpc/etzhayyim.news.v1.NewsQueryService/*` -> UI worker が受ける
- `api.news.etzhayyim.com/xrpc/*` -> backend worker
- `api.news.etzhayyim.com/jobs/*` -> backend worker
- `api.news.etzhayyim.com/scheduler/*` -> backend worker

### Internal call pattern

UI worker から backend worker への呼び出しは以下のいずれか。

1. Cloudflare Service Binding
2. zone 内 internal hostname fetch
3. signed fetch with shared secret + strict origin allowlist

第一候補は **Service Binding**。理由:

- same-zone の公開 URL hairpin を避けられる
- auth を公開 internet 依存にしなくてよい
- low latency
- route 漏れを防ぎやすい

## Caching Model

### UI worker cache

- HTML: ISR / Cache API / CDN cache
- article detail JSON proxy: short TTL + stale-while-revalidate
- list pages: category/lang 別に edge cache

### backend worker cache

- authoritative source として KV/Cypher を読む
- backend 自身は heavy compute の near-cache は持ってよいが、public HTML cache は持たない

### Purge flow

記事 publish/update 時:

1. backend worker が article projection を更新
2. backend worker が purge event を発行
3. UI worker cache tag または key を purge
4. 次回 request で UI worker が再 fetch / 再 SSR

## Auth and Security

### Browser -> UI worker

- 未認証 public read を許可
- editorial console を持つなら Clerk/session 検証は UI worker で開始してよい

### UI worker -> backend worker

- Service Binding を基本
- backend では `x-etzhayyim-internal-worker` のような internal caller assertion を要求
- public endpoint と internal endpoint を path か host で分離

### Admin / job / scheduler

- backend worker のみ
- public internet から直接叩ける route を最小化
- cron trigger / queue consumer / internal automation は backend 側へ集中

## Deployment Model

## Deployable units

### `news-ui-worker`

- SvelteKit + adapter-cloudflare
- routes:
  - `/`
  - `/{lang}`
  - `/{lang}/articles/{id}`
  - `/sitemap.xml`
  - `/robots.txt`
  - `/xrpc/...` public query proxy

### `news-backend-worker`

- kotodama app runtime
- routes:
  - `/xrpc/...`
  - `/jobs/...`
  - `/scheduler/...`
  - `/healthz`
  - `/metrics`

## Data ownership

データ所有権は backend worker に一元化する。

- KV buckets
- Cypher graph projection
- event log
- quality queue

UI worker はデータ owner ではなく projection consumer。

## Failure Isolation

分離で改善する点:

- RSS collect や translation burst が UI latency を悪化させにくい
- SSR build/deploy が scheduler/job runtime に影響しない
- backend degradation 時も UI worker 側で stale cache/fallback page を返せる
- UI worker の軽微変更を高頻度 deploy しやすい

残るリスク:

- backend 障害時に cache miss の SSR は degraded になる
- query proxy hop が 1 段増える
- purge 設計が甘いと stale 表示が長引く

## Recommended Migration Plan

### Phase 1: Boundary extraction

- Svelte 側の `workerCall()` / `browserCall()` を backend base URL or binding 経由へ抽象化
- public query 一覧を allowlist 化
- backend host を `api.news.etzhayyim.com` として追加

### Phase 2: Route split

- `news.etzhayyim.com` の public route を UI worker に移す
- `/jobs/*`, `/scheduler/*`, internal `/xrpc/*` を backend 専用化
- `news-core.etzhayyim.com` を backend alias に寄せる

### Phase 3: Query/BFF hardening

- UI worker に short-TTL cache を実装
- backend query response を SEO 用 view model に整形
- purge/revalidate event を導入

### Phase 4: Contract cleanup

- proto を `PublicQuery` / `EditorialQuery` / `Command` / `Jobs` に整理
- auth policy と caller type を明文化
- `/xrpc` 以外の legacy route を縮小

## Concrete File/Module Refactor Direction

現 repo 上では次の分割が自然。

- 現 `wasm/news-core-component/main.go`:
  - backend worker 側へ残す
- 現 `wasm/news-core-component/svelte/`:
  - `news-ui-worker` として独立
- 現 `wasm/news-core-component/etzhayyim.json`:
  - UI worker 用と backend worker 用に分離
- 現 `wasm/news-core-component/kotodama.toml`:
  - backend worker 専用の route に縮小

追加で必要なもの:

- UI worker 側の backend binding/config
- cache purge 契約
- internal caller auth middleware

## Non-Goals

- domain model 自体の再設計
- news app を miniapp-only に直ちに移行すること
- jobs を別の 3 個目 worker に今すぐ分離すること

ただし将来的には backend worker の中でも次の 2 分割はあり得る。

- `news-api-worker`
- `news-jobs-worker`

今回はまず `UI` と `backend` の 2 分割を正とする。

## Decision

`news.etzhayyim.com` は次の構成を採用する。

- **UI worker = public web + SSR + cache + query BFF**
- **backend worker = XRPC authority + jobs + data ownership**

この分離により、public media surface と editorial pipeline surface の責務境界が明確になり、deploy・latency・障害隔離・認可設計をそれぞれ独立に扱える。
