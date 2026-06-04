# Game/Anime Coverage 向上設計 (T1 + mitama)

**Date**: 2026-04-09
**Status**: `[DESIGN]`

## 1. 目的

`game` / `anime` 領域の coverage を、Worker依存の個別実装から **T1 actor manifest + mitama運用** に寄せて、以下を同時に満たす。

- coverage の可観測性を XRPC で統一
- cron / subscribeRepos の運用を PDS Shared Executor 側へ集約
- manifest 単位で rollout/rollback できる構成にする

## 2. 現状整理

### game 側

- `20-actors/media-gamers/actor-manifest.jsonld` は `executionTier: T1` で既に稼働。
- 既存で coverage 系 pipeline を持つ。
  - cron `0 */6 * * *`: `ActorCoverageSnapshot` 更新
  - xrpc `com.etzhayyim.apps.mediagamers.coverage.get`: 最新 snapshot + freshness 返却
- 追加で cron `0 */8 * * *` の guide/translation coverage もあり、運用上の土台はある。

### anime 側

- `media-anime` / `anime` は `60-apps` 側 runbook/worker設計が中心で、`20-actors/*/actor-manifest.jsonld` の T1 登録が未整備。
- `news` には `anime`/`game` category があり、実データ供給源としては強いが、T1 coverage endpoint の統一契約がない。

## 3. 問題点

1. game と anime で coverage 契約が揃っていない。
2. anime 側は mitama (`register/list/inspect/dormant/revive`) の管理対象外が多い。
3. coverage 名称の揺れ（例: `media_gamers` / `mediagamers`, `mediaanime` / `media_anime`）で集計・自動化が不安定。
4. `apps coverage` は `coverageStats` を見に行くが、T1標準は `coverage.get` であり、評価系CLIとmanifest設計にズレがある。

## 4. 設計方針

### 方針A: T1 coverage contract を game/anime 共通化

全対象 actor で下記2本を必須化する。

1. `cron` pipeline (`0 */6 * * *`)
- `graph.query`: repo別 nodeCount/latestTs
- `graph.query`: collection別 top N
- `graph.write`: `ActorCoverageSnapshot` upsert

2. `xrpc` pipeline (`com.etzhayyim.apps.<segment>.coverage.get`)
- 最新 snapshot
- freshnessRate (24h)

### 方針B: anime を T1 actor に寄せる

新規 actor を追加する。

- `20-actors/media-anime/actor-manifest.jsonld`
  - DID: `did:web:media-anime.etzhayyim.com`
  - `executionTier: T1`
  - capabilities: `graph.query`, `graph.write`, `agent.chat`, `derive:social` など最小集合
  - coverage pipeline は game と同一テンプレート

必要なら第2段階で `news` も T1 actor 化し、`anime`/`game` category coverage を同じ契約で外出しする。

### 方針C: category-level coverage を追加

`media-anime` と `media-gamers` に加え、`news` 由来のカテゴリ供給量を参照する補助クエリを入れる。

- `anime`: `articleSection` (`anime-news`, `anime-analysis`, `anime-episode`, `anime-character`) 別件数
- `game`: `game-news`, `game-analysis`, `guide`, `review` 別件数
- `lang` 別 coverage と translation rate も snapshot に含める

## 5. 収集メトリクス (必須)

`ActorCoverageSnapshot` の共通キー:

- `actorDid`
- `actorName`
- `nanoid`
- `nodeCount`
- `latestTs`
- `topCollections`
- `timestamp_ms`
- `collection` (`com.etzhayyim.apps.<segment>.coverageSnapshot`)

拡張キー (game/anime 向け):

- `domainBreakdown` (title/studio/staff/episode/gameTitle/guide/review など)
- `categoryCoverage` (`anime`/`game` 内サブカテゴリ埋まり率)
- `langCoverage` (言語別ノード比率)
- `freshnessRate24h`

## 6. KPI

最初の運用目標:

- `freshnessRate24h >= 0.85`
- `categoryCoverage >= 0.80`
- `langCoverage(ja,en) = 1.0`、主要多言語は `>= 0.70`
- snapshot 欠損 0（6時間バケット）

## 7. ロールアウト手順

1. anime T1 manifest 追加 (`20-actors/media-anime/actor-manifest.jsonld`)
2. `etzhayyim mitama -dir 20-actors/media-anime --dry-run`
3. `etzhayyim mitama -dir 20-actors/media-anime` で登録
4. `etzhayyim mitama inspect did:web:media-anime.etzhayyim.com` で登録内容確認
5. `com.etzhayyim.apps.mediaanime.coverage.get` を smoke 実行
6. `media-gamers` 側も同契約に合わせて key/collection の揺れを是正
7. 必要に応じて `news` を T1 actor 化し category coverage を統合

## 8. 互換性・リスク

- `mitama` read path は `val` 優先（schema差分に強い）が、集計SQLは promoted column 差分の影響を受けるため optional 列前提で設計する。
- 既存クライアントが `coverageStats` を参照している場合、`coverage.get` への移行期間は alias endpoint を併置する。
- 命名揺れ (`media_gamers` / `mediagamers`) は seed・collection・XRPC 名の3点セットで同時修正する。

## 9. 実装優先順位

1. `media-anime` T1 化 + `coverage.get` 実装
2. `media-gamers` との collection/nsid 命名統一
3. `apps coverage` の `coverage.get` 対応
4. `news` category coverage の T1 露出（必要時）

