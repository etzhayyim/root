# crawler v2 split design

`crawler` を `magatama host + WIT component model` のまま分割し、`wproto` からも呼べるようにする設計。

## Goal

- `tinygo` guest 依存を外す
- `crawler` の責務を split して cold-start blast radius を減らす
- `wproto` `w-command` / `w-query` から直接起動・照会できる
- Playwright / browser rendering のような JS-heavy 部分だけ TypeScript に逃がす

## Why not Deno

- 現在の repo には `magatama-go` 相当の Deno/WIT binding がない
- `magatama-engine` / build pipeline は TinyGo と Rust component が前提
- crawler の hot path は HTML fetch / parse / dedupe / projection で、Rust guest の方が適合する

結論として、`guest = Rust`, `browser rendering = TypeScript native provider` を採用する。

## Split

### 1. crawler-control

- 役割: public facade, job orchestration entry, W Protocol extension entry
- 言語: Rust component
- world: `gftd-actor` もしくは `gftd:w/w-extension`
- 理由:
  - `wproto` extension router と最も自然につながる
  - command/query の contract を typed WIT で保持できる
  - small state machine と graph projection 更新を Rust guest で安全に書ける

#### Responsibilities

- `StartJob`
- `CancelJob`
- `GetJob`
- `ListResults`
- `SearchProjection`
- queue/worker への dispatch
- job lifecycle event publish

### 2. crawler-frontier

- 役割: frontier, dedupe, per-host politeness, seed expansion
- 言語: Rust component
- world: provider world (`gftd-frontier-provider` 系)
- 理由:
  - 状態遷移が多く、graph/kv host import と相性が良い
  - `seen`, `scheduled`, `done`, `failed`, `host backoff` を deterministic に扱いたい

#### Responsibilities

- enqueue seed
- dequeue next URL batch
- mark success/failure
- host/domain budget 管理
- robots / sitemap discovery target 管理

### 3. crawler-fetch

- 役割: HTTP fetch, redirect handling, content sniffing, raw capture
- 言語: Rust native provider
- 理由:
  - network-heavy
  - WASM guest より native の方が timeout, compression, TLS, streaming 制御が容易
  - HTML/body の大きい payload を component boundary で何度もコピーしたくない

#### Responsibilities

- GET/HEAD
- response metadata normalization
- raw body persist to blob/B2
- fetch result envelope emit

### 4. crawler-render

- 役割: JS-required pages only browser rendering
- 言語: TypeScript native provider
- 理由:
  - Playwright ecosystem が最も成熟
  - anti-bot, browser context, screenshot/debug の開発速度が高い

#### Responsibilities

- browser-required 判定された URL の render
- rendered HTML / screenshot / trace persist
- anti-bot signal report

### 5. crawler-extract

- 役割: HTML parse, text extraction, link extraction, metadata extraction
- 言語: Rust component
- 理由:
  - parser/normalizer は pure compute で component guest 向き
  - host import から独立して単体テストしやすい

#### Responsibilities

- title / canonical / meta / og tags
- readable text
- outgoing links
- language / mime heuristics

### 6. crawler-indexer

- 役割: search projection, entity graph projection, downstream notification
- 言語: Rust component
- 理由:
  - graph write / projection write が中心
  - host の cypher import と親和性が高い

#### Responsibilities

- `CrawlResult` projection
- `Page`, `LINKS_TO`, `FetchEvent`, `BannerObservation` projection
- search 用 projection node/table 更新
- downstream app への event publish

## Runtime Topology

```text
Connect/HTTP
  -> crawler-control (Rust component)
     -> crawler-frontier (Rust component/provider)
     -> crawler-fetch (Rust native provider)
         -> optional crawler-render (TS provider)
     -> crawler-extract (Rust component)
     -> crawler-indexer (Rust component)
     -> search / resources / other apps
```

## W Protocol Integration

`crawler-control` を W Protocol extension として expose する。

### Extension kinds

- `crawler.job.start`
- `crawler.job.cancel`
- `crawler.job.status`
- `crawler.result.list`
- `crawler.result.search`

### Why extension route

- `wproto` は kind-based dispatch を extension router で処理できる
- extension world は `w-command` / `w-query` import をすでに持つ
- `crawler` を messaging plane 上の callable tool にできる

### Call flow from wproto

```text
caller app
  -> w-command.send(kind="crawler.job.start", payload)
  -> wproto extension router
  -> crawler-control extension-handler
  -> frontier/fetch/extract/index pipeline
  -> w-query or query envelope for status/result search
```

### Response model

- mutation 系は `w-command`
  - `crawler.job.start`
  - `crawler.job.cancel`
- read 系は `w-query`
  - `crawler.job.status`
  - `crawler.result.list`
  - `crawler.result.search`

## Storage Split

### Graph / KV in magatama host

- job metadata
- frontier state
- host politeness
- result metadata
- link graph

### Blob storage

- raw HTML
- rendered HTML
- screenshots
- trace/debug artifacts

### Search projection

`crawler-indexer` が `search` app とは直接 graph shared しない。

- option A: search projection node/table を crawler 側に持ち、`search` は federated query
- option B: crawler-indexer が `search` の command/query facade に push

推奨は A。理由は app graph 分離と整合しやすいから。

## Public Contracts

### Connect facade

- `/xrpc/gftd.crawler.v2.CrawlerCommandService/StartJob`
- `/xrpc/gftd.crawler.v2.CrawlerCommandService/CancelJob`
- `/xrpc/gftd.crawler.v2.CrawlerQueryService/GetJob`
- `/xrpc/gftd.crawler.v2.CrawlerQueryService/ListResults`
- `/xrpc/gftd.crawler.v2.CrawlerQueryService/SearchResults`

### W Protocol facade

- `kind = "crawler.job.start"`
- `kind = "crawler.job.cancel"`
- `kind = "crawler.job.status"`
- `kind = "crawler.result.list"`
- `kind = "crawler.result.search"`

## Language Decision Summary

| Component | Language | Reason |
|---|---|---|
| crawler-control | Rust component | WIT / wproto extension integration |
| crawler-frontier | Rust component | stateful scheduling + graph/kv |
| crawler-fetch | Rust native provider | network + streaming + native HTTP ergonomics |
| crawler-render | TypeScript native provider | Playwright ecosystem |
| crawler-extract | Rust component | pure compute/parser |
| crawler-indexer | Rust component | graph/search projection write |

## Directory Proposal

```text
60-apps/ai-gftd-project-www-crawler/
├─ provider/
│  ├─ crawler-control-rs/
│  ├─ crawler-fetch-rs/
│  ├─ crawler-render-ts/
│  └─ crawler-split-v2/          # orchestration/dev bundle
├─ wasm/
│  ├─ ai-gftd-wasm-crawler-control-<nanoid>/
│  ├─ ai-gftd-wasm-frontier-<nanoid>/
│  ├─ ai-gftd-wasm-extract-<nanoid>/
│  └─ ai-gftd-wasm-indexer-<nanoid>/
└─ docs/
   └─ 260319-crawler-split-wproto-design.md
```

## Migration Path

### Phase 1

- keep existing `crawler.gftd.ai`
- add `crawler-control` and `crawler-frontier`
- make `SearchResults` federated from `crawler-control`

### Phase 2

- move fetch path from current monolith into `crawler-fetch`
- route JS-required pages to `crawler-render`

### Phase 3

- move result projection to `crawler-indexer`
- remove v1 in-app frontier/timer execution

## Recommendation

- `crawler-control` を最初に Rust extension 化する
- `search` はまず `crawler-control` の federated query を読む
- `fetch` は native Rust provider に出す
- browser rendering だけ TypeScript に残す

これが、現行 platform と整合しつつ `tinygo` 依存と monolith 依存を両方減らす最短ルート。
