# etzhayyim-project-news

News media platform (`news.etzhayyim.com`)。**wRPC stream-native reactive pipeline (Design E)**。Follow-based upstream RSS worker から AT commit を受信 → 品質評価 → 翻訳 → ATPost。Batch command 0、Transport 1 種 (AT commit stream on wRPC)。

設計: `90-docs/260324-news-wrpc-stream-reactive-design.md`

## Runtime

**TS Native + Lexicon Contract**。Business logic: `wasm/news-core-component/src/app.ts` / `src/worker.ts`。

| 項目            | 値                                                                                    |
| --------------- | ------------------------------------------------------------------------------------- |
| Language        | TypeScript (`@etzhayyim/kotodama-host-sdk` host, TS Native migration)                      |
| Build           | `etzhayyim deploy` (app.ts が直接 wrangler entrypoint)。`src/app.ts` は legacy 経路        |
| UI mode         | `appview` (Protocol Canvas card)                                                      |
| Architecture    | **wRPC stream-native reactive** (Design E)                                            |
| Host            | `@etzhayyim/kotodama-host-sdk` (WIT host + write buffer)                                   |
| Input           | `subscribe-repos.handle-repo-commit` — Follow 先 upstream からの AT commit (reactive) |
| Output (stream) | `serve.handle-stream("stream-articles")` — wRPC stream to subscribers                 |
| Output (social) | `ATPost(writerDID, text, opts)` — 1 call = record + post                              |
| Read            | `G()` (SQL) for card/digest                                                           |
| Config          | `wasm/news-core-component/kotodama.jsonld` + `wasm/news-core-component/src/*.ts`      |

## Reactive Pipeline (Design E)

```
upstream RSS workers → Follow → AT commit → handleComAtprotoSyncSubscribeReposCommit → evaluate → translate → ATPost
                                                                                      ↓
                                                              handle-stream → subscriber apps/UI
```

### 3 Layer Architecture

| Layer            | WIT                                      | Role                                                |
| ---------------- | ---------------------------------------- | --------------------------------------------------- |
| **1. Input**     | `com-atproto:sync/subscribe-repos@1.0.0` | AT commit event (Follow-filtered by :FOLLOWS edges) |
| **2. Output**    | `etzhayyim:serve/serve@1.0.0`              | `handle-stream("stream-articles")` wRPC push        |
| **3. Evolution** | `com-atproto:sync/subscribe-repos@1.0.0` | `on-heartbeat` engagement + self-evolution          |

### handleComAtprotoSyncSubscribeReposCommit (Layer 1 — pipeline entry)

```ts
sdk.app.onCommit(async (commit) => {
  if (commit.action !== "create") return;
  if (isArticleCollection(commit.collection)) {
    return processInboundArticle(commit); // evaluate → translate → ATPost
  }
  if (commit.collection === "app.bsky.feed.like") return; // engagement (Layer 3)
});
```

### processInboundArticle

1. Parse commit payload (title, summary, category, language, writer_did)
2. LLM quality evaluation (murakumo, score 0-100)
3. score >= 70 → LLM translate (12 languages) → `ATPost(writerDID, translated)`
4. Push to active `stream-articles` subscribers

### generateAndPostArticle (Heartbeat — every ~10 min)

1. Fetch recent 10 articles in target category from yata (grounding context)
2. LLM analysis generation (murakumo claude-opus-4-6) — structured analysis with sources_cited, not generic brief
3. LLM quality evaluation (same `evaluateQuality()` as inbound — no hardcoded score)
4. score >= 70 → translate to 11 languages
5. `socialPostAnalysis()` — embed with lead insight extracted from analysis body

### stream-articles (Layer 2 — wRPC output)

```go
app.HandleStream("", "stream-articles", streamArticles,
    kotodama.RequireCallerRole("subscriber"),
    kotodama.RequireTrustLevel("low"),
)
```

Subscribers connect via `InvokeStream("did:web:news.etzhayyim.com", "stream-articles", {category, language})`. wRPC LEB128 framing, credit-based backpressure, GovernanceGate enforced, WrpcStreamAuditBlock on close.

## MCP Tools (auto-registered)

`app.Command()` + `AsAgentTool()` で宣言された commands は MCP tools として自動公開。`createWorkerExport()` が `identityRegister()` + `capabilityDeclare()` → PDS → yata graph。

| MCP Tool Name                                  | Description                                             |
| ---------------------------------------------- | ------------------------------------------------------- |
| `news-core.GenerateDigest`                     | Generate per-category daily digest                      |
| `news-core.news.list`                          | List latest news articles                               |
| `news-core.news.detail`                        | Show article details                                    |
| `news-core.news.evolve`                        | Show evolution metrics dashboard                        |
| `news-core.news.fitness`                       | Show fitness growth history                             |
| `news-core.card.action`                        | Handle card interaction actions                         |
| `news-core.com.etzhayyim.apps.news.listIntelSources` | List primary/official global intel sources              |
| `news-core.com.etzhayyim.apps.news.analyzeIntel`     | Convert source evidence into an attributed intel report |
| `news-core.com.etzhayyim.apps.news.publishIntel`     | Publish prepared intel as a writer-DID post             |
| `news-core.com.etzhayyim.apps.news.liveAudioIngest`  | Start public live-news/radio/HLS audio capture + STT → intel |

Discovery: `POST mcp.etzhayyim.com/mcp` → `{"method":"tools/list","params":{"app":"news-core"}}`。
Invocation: `POST mcp.etzhayyim.com/mcp` → `{"method":"tools/call","params":{"name":"news-core.GenerateDigest","arguments":{...}}}`。

## Writer Entity System (DID per Information Source)

**各情報ソースは独自の AT Protocol bot DID を持つ writer entity。** `ATPost(writerDID)` で record author = DID provenance が直接紐付く。`init()` の `ensureWriterDIDs()` で全 writer の path-based DID を `DIDCreate()` で PDS に登録 (冪等)。DID 未登録だと `ATPost` が PDS controller 検証で失敗する。

### DID Pattern

```
did:web:news.etzhayyim.com:writer:{source-id}
```

### Source Type Classification

| source-type         | 説明                                                           | 例                                      |
| ------------------- | -------------------------------------------------------------- | --------------------------------------- |
| `rss`               | RSS/Atom フィード                                              | GIGAZINE, Reuters, Nature               |
| `broadcast`         | Public live news/radio audio stream                           | NHK radio, public radio, agency stream  |
| `press-release`     | 公式プレスリリース / IR                                        | OEM IR, studio announcements            |
| `regulator`         | 政府規制当局                                                   | MLIT, METI, PMDA, FDA                   |
| `industry-body`     | 業界団体                                                       | JAMA, SEAJ, SEMI, JARA                  |
| `standards-body`    | 標準化団体                                                     | JIS, ISO, JEDEC, SEMI Standards         |
| `clinical-registry` | 臨床試験登録                                                   | jRCT, ClinicalTrials.gov                |
| `statistics`        | 公式統計                                                       | CIPA, JNTO visitor stats                |
| `trade-fair`        | 展示会/見本市                                                  | JIMTOF, trade fair official             |
| `platform`          | プラットフォーム公式                                           | YouTube, Spotify                        |
| `rights-holder`     | IP 権利者                                                      | publisher, studio, production committee |
| `manufacturer`      | OEM / メーカー直接                                             | product pages, firmware notices         |
| `llm-generated`     | AI 生成記事                                                    | etzhayyim AI Writer                          |
| `llm-analysis`      | AI 分析記事 (既存記事をグラウンディングコンテキストとして合成) | etzhayyim AI Writer                          |

### Built-in Writer Entities (48 sources)

| Category          | Writers                                                                                     | DID 例                                   |
| ----------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------- |
| tech (8)          | GIGAZINE, ITmedia, PC Watch, Publickey, TechCrunch JP, Ars Technica, The Verge, Hacker News | `did:web:news.etzhayyim.com:writer:gigazine`   |
| ai (4)            | AI 新聞, MIT Tech Review JP, The Batch, AI News                                             | `did:web:news.etzhayyim.com:writer:aishinbun`  |
| anime (4)         | Anime!Anime!, コミックナタリー, アニメイトタイムズ, Crunchyroll                             | `did:web:news.etzhayyim.com:writer:animeanime` |
| game (5)          | 4Gamer, デンファミニコゲーマー, インサイド, AUTOMATON, Kotaku                               | `did:web:news.etzhayyim.com:writer:4gamer`     |
| car (4)           | くるまのニュース, clicccar, Motor-Fan, Electrek                                             | `did:web:news.etzhayyim.com:writer:kurumanews` |
| business (5)      | 東洋経済, ダイヤモンド, 日経ビジネス, Reuters, Bloomberg                                    | `did:web:news.etzhayyim.com:writer:reuters`    |
| semiconductor (4) | EE Times JP, TECH+, Semiconductor Engineering, SemiAnalysis                                 | `did:web:news.etzhayyim.com:writer:semie`      |
| politics (3)      | NHK 政治, 朝日新聞 政治, Politico                                                           | `did:web:news.etzhayyim.com:writer:nhkpol`     |
| science (3)       | ナゾロジー, Nature News, Science Daily                                                      | `did:web:news.etzhayyim.com:writer:nature`     |
| entertainment (3) | 音楽ナタリー, 映画ナタリー, Variety                                                         | `did:web:news.etzhayyim.com:writer:variety`    |
| sports (2)        | スポーツ報知, ESPN                                                                          | `did:web:news.etzhayyim.com:writer:espn`       |
| world (3)         | NHK 国際, BBC World, Al Jazeera                                                             | `did:web:news.etzhayyim.com:writer:bbc`        |
| llm (1)           | etzhayyim AI Writer                                                                              | `did:web:news.etzhayyim.com:writer:llm`        |

### Adding a New Source (Follow-based)

```go
// Follow upstream RSS worker — no redeploy needed
kotodama.Follow("rss-tech-nanoid")
// → handleComAtprotoSyncSubscribeReposCommit receives article commits reactively
```

## Lexicon (AT Protocol Record Kinds)

| Kind (dot notation) | AT Lexicon NSID             | 説明                                         |
| ------------------- | --------------------------- | -------------------------------------------- |
| `news_article`      | `com.etzhayyim.apps.news.article` | 記事レコード (ATPost で writer_did = author) |
| `news_source`       | `com.etzhayyim.apps.news.source`  | 情報ソース定義 (category, writer DID)        |
| `news_writer`       | `com.etzhayyim.apps.news.writer`  | Writer entity メタデータ                     |
| `news_digest`       | `com.etzhayyim.apps.news.digest`  | カテゴリ別 daily/weekly ダイジェスト         |

## Data Model

### `intel.report` (AT Record via `com.etzhayyim.apps.intel.report`)

| Column           | Type | Description                                            |
| ---------------- | ---- | ------------------------------------------------------ |
| title            | TEXT | Intel headline                                         |
| summary          | TEXT | concise source-grounded summary                        |
| classification   | TEXT | `high-confidence-open-source` or `needs-corroboration` |
| sourceFamily     | TEXT | source type: regulator/official/press-release/etc.     |
| collectionMethod | TEXT | `primary-source-xrpc` or `open-source-xrpc`            |
| analyticLens     | TEXT | topic lens such as `news-intel/security`               |
| entities         | JSON | extracted org/place/entity hints                       |
| facts            | JSON | factual claims extracted from source text              |
| findings         | JSON | analytical implications separated from facts           |
| props            | JSON | sourceUrl/sourceId/credibility/priority metadata       |

### `articles` (AT Record via ATPost)

| Column         | Type    | Description                                                                                        |
| -------------- | ------- | -------------------------------------------------------------------------------------------------- |
| article_id     | TEXT PK | nanoid                                                                                             |
| title          | TEXT    | headline                                                                                           |
| summary        | TEXT    | short description                                                                                  |
| content        | TEXT    | full article body                                                                                  |
| category       | TEXT    | tech/ai/anime/game/car/business/semiconductor/politics/science/entertainment/sports/world + C1-C11 |
| language       | TEXT    | ja/en/es/hi/...                                                                                    |
| source         | TEXT    | feed name or "translated:{lang}"                                                                   |
| url            | TEXT    | source URL                                                                                         |
| published_at   | TEXT    | RFC3339                                                                                            |
| quality_score  | TEXT    | 0-100 (evaluated on receive)                                                                       |
| translation_of | TEXT    | source article_id (empty if original)                                                              |
| canonical_lang | TEXT    | source language                                                                                    |
| writer_did     | TEXT    | Writer entity DID = AT Record author                                                               |
| source_type    | TEXT    | rss/press-release/regulator/llm-generated/...                                                      |
| org_id         | TEXT    | RLS                                                                                                |
| user_id        | TEXT    | RLS                                                                                                |
| actor_id       | TEXT    | RLS (= writer_did)                                                                                 |

### `digests` (AT Record via WRecord)

| Column                  | Type    | Description                |
| ----------------------- | ------- | -------------------------- |
| digest_id               | TEXT PK | nanoid                     |
| category                | TEXT    | category or "all"          |
| period                  | TEXT    | daily/weekly               |
| summary                 | TEXT    | digest summary text        |
| article_count           | INTEGER | articles in digest         |
| top_articles            | TEXT    | JSON array of top articles |
| generated_at            | TEXT    | RFC3339                    |
| org_id/user_id/actor_id | TEXT    | RLS                        |

## Categories

### General (12)

tech, ai, anime, game, car, business, semiconductor, politics, science, entertainment, sports, world

### Specialist Tracks (C1-C11)

| Track | Category                | Primary Source Types                   |
| ----- | ----------------------- | -------------------------------------- |
| C1    | automotive              | OEM/supplier IR, MLIT, JAMA, JSAE      |
| C2    | semiconductor-equipment | Equipment vendor IR, SEAJ, SEMI, JEDEC |
| C3    | robotics-fa             | Robot vendor IR, JARA, IFR             |
| C4    | anime-ip                | Rights-holder, broadcaster, AJA        |
| C5    | medical-devices         | PMDA, MHLW, FDA, jRCT                  |
| C6    | precision-optics        | CIPA, camera/lens manufacturers        |
| C7    | industrial-automation   | PLC/SCADA vendor, automation consortia |
| C8    | machine-tools           | JMTBA, JIMTOF, JIS/ISO                 |
| C9    | music-vtuber            | Agency/label, JASRAC, platform         |
| C10   | fashion-textile         | Brand/manufacturer, METI, trade fair   |
| C11   | tourism-inbound         | JTA, JNTO, transport, DMO              |

## Commands (5)

| Command          | Type      | Description                                 |
| ---------------- | --------- | ------------------------------------------- |
| `GenerateDigest` | scheduled | カテゴリ別 daily/weekly ダイジェスト生成    |
| `news.list`      | card      | 最新記事一覧 (Protocol Canvas)              |
| `news.detail`    | card      | 記事詳細 (Protocol Canvas)                  |
| `news.evolve`    | card      | 進化サイクル実行 + メトリクスダッシュボード |
| `news.fitness`   | card      | フィットネス成長履歴                        |

**Eliminated (Design E)**: CollectRSS, IngestArticle, GenerateArticle, EvaluateArticle, EvaluateBatch, TranslateArticle, TranslateToAll, Heartbeat, Evolve, RegisterWriterProfiles — all replaced by `handleComAtprotoSyncSubscribeReposCommit` reactive pipeline.

## Shinka (joucho 情緒 cadence)

joucho 情緒 cadence heartbeat (`resolveHeartbeatCadence`)。joucho 5 軸 (joy/calm/stress/gratitude/focus) で mood 判定 → mood-driven cadence で投稿/engage/drill/validate を自律決定。InboxBuffer で Follow 先 commit + reaction を蓄積 → content source 選択。follower KPI reward (wellness/dojo 上昇 → like/love)。

### Fitness Score (0.0-1.0)

| 指標                 | 重み | 目標    |
| -------------------- | ---- | ------- |
| Article count        | 15%  | >= 100  |
| Fresh articles (24h) | 20%  | >= 10   |
| Quality avg          | 20%  | >= 75   |
| High quality rate    | 10%  | >= 50%  |
| Translation rate     | 10%  | >= 80%  |
| Category coverage    | 10%  | >= 7/12 |
| Base stability       | 5%   | —       |
| Eval coverage        | 10%  | 100%    |

## Quality Guardrails

| Guardrail                 | Implementation                                                                                          |
| ------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Dedup**                 | headline 一致チェック (`G("newsArticle").Match(Eq{"title": headline})`)。同一 headline の重複投稿を防止 |
| **Grounding context**     | LLM 分析記事は yata から同カテゴリ直近 10 記事を取得し、事実ベースの分析を生成                          |
| **Quality evaluation**    | 全記事 (inbound + LLM 生成) に `evaluateQuality()` 適用。ハードコード score 禁止                        |
| **Translation threshold** | score >= 70 のみ 11 言語に翻訳                                                                          |

## Shannon Efficiency

| Metric                  | Before (Design A)    | After (Design E)                                                |
| ----------------------- | -------------------- | --------------------------------------------------------------- |
| η (N=100)               | 0.05%                | **97.4%**                                                       |
| Transport types         | 3                    | **1**                                                           |
| Write calls per article | 2 (WRecord + ATPost) | **2** (ComAtprotoRepoCreateRecord + ATPost = Design E Tier 1+2) |
| src/app.ts lines        | ~550                 | **~280**                                                        |
| Batch commands          | 7                    | **0**                                                           |
