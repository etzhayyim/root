# 260327 News TS Native Migration Plan

対象: `news.etzhayyim.com` (`60-apps/etzhayyim-project-news/wasm/news-core-component`)

## Goal

- TinyGo guest (`main.go`) を段階的に廃止する。
- Business logic を TypeScript (`src/app.ts`) に移す。
- WIT は契約 SSoT として維持し、runtime は TS host-first で運用する。

## Current Status (2026-03-27)

- 既存本番ロジック: `main.go` (legacy)
- 追加済み TS Native エントリ:
  - `src/app.ts`
  - `src/worker.ts`
  - `build.mjs`
- 追加済み最小コマンド:
  - `GenerateDigest` (TS 実装)
  - `news.list`
  - `news.detail`
- 追加済み reactive 経路:
  - `/_commit`, `/_w/commit` で commit ingest
  - article ingest (`processInboundArticle`) + quality eval + translation/post

## Migration Phases

1. Phase 1 (done in this change): TS Native scaffold
- `src/app.ts` + `src/worker.ts` を追加
- `esbuild` build スクリプト追加
- `news.list` / `news.detail` を TS 実装で先行移植

2. Phase 2 (in progress): Reactive ingest + publish parity
- `handleComAtprotoSyncSubscribeReposCommit`
- `processInboundArticle`
- `evaluateQuality`
- `translateAndPublish`
- `socialPost` / `socialPostAnalysis`

3. Phase 3: Card/evolution parity
- `cmdCardListArticles`
- `cmdCardArticleDetail`
- `cmdCardEvolve`
- `cmdCardFitnessHistory`
- `cmdCardAction`
- `evaluateNewsFitness`

4. Phase 4: Writer DID + cleanup
- `ensureWriterDIDs`
- `writerSubDID`
- `loadWriters`
- `main.go` を read-only legacy 化して削除準備

## Function Migration Map

- Query/Read
  - `qryListArticles` -> `src/app.ts` `news.list`
  - `qryGetArticle` -> `src/app.ts` `news.detail`
- Digest
  - `cmdGenerateDigest` -> `GenerateDigest` (placeholder 実装済み)
- Reactive pipeline
  - `handleComAtprotoSyncSubscribeReposCommit` -> Phase 2
  - `processInboundArticle` -> Phase 2
- Evolution
  - `heartbeatHandler` / `evaluateAndEvolve` / `generateAndPostArticle` -> Phase 3

## Guardrails

- `main.go` は即削除しない。移植完了まで fallback として維持。
- `magatama.jsonld` の runtime/build 切替は、Phase 2 完了後に行う。
- DB schema/record key (`news_article`, `article_id`) は互換維持。
