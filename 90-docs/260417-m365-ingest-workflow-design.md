# M365 Ingest Workflow + Actor Pipeline DSL (2026-04-17)

Ad-hoc `~/.etzhayyim/ingest/m365_mail_ingest.py` Python script を T1 actor manifest pipeline + derive-based routing に置き換える設計。Actor = `m365-ingest` (nanoid `m3650xin`, `did:web:m365-ingest.etzhayyim.com`)。

## 目的

| before | after |
|---|---|
| 手動 `python3 m365_mail_ingest.py upn` を UPN ごとに実行 | `cron */15 *` が `delta-sync-all-users` を自動起動、`com.etzhayyim.apps.m365Ingest.syncUser` XRPC で任意 UPN を on-demand |
| sync state = ローカル JSON (`~/.etzhayyim/sync_state.json`) | sync state = graph (`vertex_m365_sync_state`) |
| routing なし (DB 書き込みのみ) | `com.etzhayyim.apps.kyber.inbox.emailSignal` emit → kyber-inbox / yabai が subscribeRepos で後処理 |
| OAuth 考慮なし | `email-service-adapter` が per-user OAuth UI を担い、`m365-ingest` は tenant app token のみ使用 (RACI 分離) |

## アクター境界 (RACI)

| Actor | Role | Reads | Writes |
|---|---|---|---|
| `m365-ingest` (T1, 新規) | **R** — Graph API raw fetch + classification | `vertex_m365_user`, Graph `/users/*` | `vertex_m365_sync_state`, `com.etzhayyim.apps.kyber.inbox.emailSignal` |
| `email-service-adapter` (既存, `outlook.etzhayyim.com`) | **A** — OAuth UI + per-user consent | PDS `oauth_connection` | `oauth_connection` (不変) |
| `kyber-inbox` (既存, `inb0x4k2`) | **C** — signal/noise + dept routing | `emailSignal` (subscribeRepos) | `vertex_email_message` |
| `yabai` (既存, `y8b41k0x`) | **C** — threat scoring | `emailSignal` where `signalClass='yabai'` | `yabai.entity/evidence/risk` |

Shannon η: 1 responsibility / actor。ingest-only な actor を分離することで email-service-adapter の OAuth UI は PII tier 3 の consent flow に集中でき、`m365-ingest` は純粋に "tenant app token で fetch → normalize → write" に絞れる。

## Actor Manifest Pipeline DSL

`actor-manifest.jsonld` に `pipelines[]` 配列を宣言する。既存の yabai/T1 actors と同じ pattern。

### Trigger 種別

| type | field | 意味 |
|---|---|---|
| `cron` | `cron` (5-field crontab) | PDS Shared Executor が定期起動 |
| `xrpc` | `nsid` | 外部 XRPC call で起動 (input = XRPC body) |
| `subscribeRepos` | `collections[]` | AT Repo commit stream で起動 (input = commit event) |
| `webhook` | `path` | HTTP POST hook (内部用, 未使用) |

### Step `fn` 種別

| fn | 引数 | 戻り | 用途 |
|---|---|---|---|
| `graph.query` | `{ sql, params }` | `{ rows: unknown[] }` | Kysely raw SQL (read-only) |
| `graph.write` | `{ sql, params }` | `{ rowsAffected }` | INSERT / UPDATE / DELETE |
| `agent.chat` | `{ message, context?, model? }` | `{ text, usage }` | LLM 1-shot |
| `agent.converse` | `{ messages, tools?, options? }` | `{ content, finishReason }` | Multi-turn LLM |
| `derive:social` | `{ template, did?, embed? }` | `{ postUri, cid }` | `app.bsky.feed.post` 発行 |
| `host.<group>.<method>` | lexicon input schema | lexicon output schema | Host capability (`com.etzhayyim.host.*`) |
| `iterate` | `{ over, as, maxConcurrency?, do[] }` | `{ results[] }` | Array fan-out、bounded 並行 |
| `loop` | `{ while, maxIterations, do[] }` | `{ iterations }` | 条件付き反復 (e.g. pagination) |
| `pipeline.call` | `{ pipelineId, input }` | `{ output }` | 別 pipeline 呼出 (再帰 OK) |
| `pipeline.map` | `{ items, emit }` | `{ emitted }` | Array → `createRecord` fan-out |
| `branch` | `{ when, then[], else[] }` | `{ taken }` | 条件分岐 |
| `try` | `{ do[], catch[], finally[] }` | `{ ok, error? }` | エラー境界 |

### 変数解決

| 記法 | 意味 |
|---|---|
| `$did` | Pipeline を実行している actor の primary DID |
| `$runId` | Pipeline 実行単位の UUID |
| `$input.*` | Trigger payload (XRPC body / commit event / cron empty) |
| `$<stepId>` | 他 step の full output |
| `$<stepId>.<field>` | 特定フィールド参照 |
| `$loop.prev` | Loop 直前反復の output |
| `$loop.iteration` | Loop iteration counter (0-based) |
| `${expr}` | JavaScript-subset expression (classifier / hash / string ops) |

Expression subset (safe eval):
- Object / array access: `item.from.emailAddress.address`
- String ops: `split`, `slice`, `includes`, `toLowerCase`
- Ternary: `x ? y : z`
- Helpers: `hash(...)`, `signalEncrypt(...)`, `classifySenderKind(...)`, `folderSignalClass(...)`, `noiseScore(...)`, `slug(...)`, `nowIso()`

### 並行度

- `iterate.maxConcurrency`: executor が bounded worker pool で fan-out (default 1 = 直列)
- `loop` は常に直列 (pagination は順序依存)
- 1 pipeline の複数 step は依存関係 (`depends_on[]`) に基づき DAG 実行。指定なしは順次

### エラー処理

| 状況 | 挙動 |
|---|---|
| Step 失敗 | Pipeline abort、失敗内容を `vertex_pipeline_run` に記録 |
| Host capability 429 / 503 | Retry-After 尊重、exponential backoff (2s,4s,8s,16s,32s — 5回) |
| Host capability 401 | 1 回だけ token 再取得 retry、再失敗で abort |
| `try` 内部失敗 | `catch[]` 実行、`finally[]` は常時実行 |
| Overall timeout (executor 設定) | 全 step cancel、partial state は watermark 経由で次回再開 |

## `m365-ingest` の 3 pipeline

### 1. `enumerate-tenant-users` (cron `0 3 * * *`)

テナント内の `@etzhayyim.com` ユーザ一覧を `vertex_m365_user` にキャッシュ (1日1回)。

```
token  ←  host.m365.acquireAppToken
users  ←  host.m365.enumerateUsers(token=$token.access_token, upnDomainSuffix='@etzhayyim.com')
upsert ←  graph.write (INSERT...SELECT FROM UNNEST($users.users))
```

### 2. `delta-sync-all-users` (cron `*/15 * * * *`)

全ユーザの差分同期を fan-out で実行。Executor の bounded concurrency (=4) で throttling 回避。

```
users  ←  graph.query (vertex_m365_user LEFT JOIN vertex_m365_sync_state, stale first, LIMIT 50)
token  ←  host.m365.acquireAppToken
       ←  iterate (over=$users.rows, as=u, maxConcurrency=4,
             do = pipeline.call('sync-single-user', input={upn: $u.upn, since: $u.last_received_at}))
```

### 3. `sync-single-user` (xrpc `com.etzhayyim.apps.m365Ingest.syncUser`)

1 UPN の mailbox を pagination しながら ingest。`loop` step が `nextLink` を追跡。

```
token    ←  host.m365.acquireAppToken
folders  ←  host.m365.fetchMailFolders(token=$token.access_token, upn=$input.upn)
mark     ←  graph.write  (vertex_m365_sync_state status='running')
paginate ←  loop (while=$next.nextLink != null || $iteration == 0, maxIterations=500, do = [
              page             ←  host.m365.fetchMessagesPage(token=$token.access_token, upn=$input.upn, since=$input.since, nextLink=$loop.prev.nextLink),
              classify-and-write ←  pipeline.map(items=$page.messages, emit={ collection: 'com.etzhayyim.apps.kyber.inbox.emailSignal', record: {... signalEncrypt, folderSignalClass, classifySenderKind ...} }),
            ])
watermark ←  graph.write  (UPDATE vertex_m365_sync_state SET last_sync_at=NOW, last_received_at=$paginate.maxReceivedAt, status='idle')
```

## Routing (downstream)

`m365-ingest` は **`emailSignal` record を emit するだけ**。後続の routing は既存 actor が `subscribeRepos` で受信:

| Subscriber | Filter | 動作 |
|---|---|---|
| `kyber-inbox` | `com.etzhayyim.apps.kyber.inbox.emailSignal` | signal/noise classification → `vertex_email_message` INSERT + `kyber_dept` routing edge |
| `yabai` | `com.etzhayyim.apps.kyber.inbox.emailSignal` (where `signalClass='yabai'`) | `yabai.entity (Email)` + `yabai.evidence (FraudSignal)` + `yabai.risk (monitor)` |

新規 routing rule は downstream actor の manifest に追加するだけで、`m365-ingest` には触らない (open/closed 原則、Shannon η 維持)。

## Host capability: `com.etzhayyim.host.m365.*`

4 lexicons + 1 TS module。完全な contract SSoT (`00-contracts/lexicons/com/etzhayyim/host/m365/*.json`)。

| NSID | 方向 | 用途 |
|---|---|---|
| `com.etzhayyim.host.m365.acquireAppToken` | `procedure` | Client credentials flow、token cache (55min skew) |
| `com.etzhayyim.host.m365.enumerateUsers` | `query` | `/users?$filter=endsWith(upn,...)`, auto-pagination |
| `com.etzhayyim.host.m365.fetchMailFolders` | `query` | `/mailFolders` recursive (childFolders) |
| `com.etzhayyim.host.m365.fetchMessagesPage` | `query` | `/messages` 1 page (caller が `nextLink` ループ) |

TS impl: `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/capabilities/m365.ts` (`createM365Capability(cfg)`).

Wire-up: `createHostDispatcher(hostImports, { m365: createM365Capability({ tenantId, clientId, clientSecret }) })`.

### Secrets / env

| 変数 | 取得元 | 置き場 |
|---|---|---|
| `M365_TENANT_ID` | Azure AD portal | `wrangler.jsonc` vars (non-secret) |
| `M365_CLIENT_ID` | Azure AD portal | `wrangler.jsonc` vars (non-secret) |
| `M365_CLIENT_SECRET` | Azure AD portal | Cloudflare Secrets Store (`secrets_store_secrets[].secret_name = m365_client_secret`) |

Local dev: `~/.etzhayyim/m365-credentials.env` に同名で記載 (chmod 600)。

### Failure modes

| 状況 | 挙動 |
|---|---|
| 401 (token 期限切れ) | `cached = null` → 次回 `acquireAppToken()` で refresh、caller は retry |
| 429 / 503 | Retry-After に従って sleep、最大 5 回 exponential backoff |
| 404 user not found | caller (pipeline) が `vertex_m365_user.account_enabled = false` に更新、alert |
| Partial page failure | `loop` step の `try` で `catch → graph.write (mark error state)`、次回は同じ `since` から resume |

## Graph schema

Migration `20260417190000_vertex_m365_sync_state.ts`:

### `vertex_m365_user` (tenant user cache)

| column | type | 用途 |
|---|---|---|
| upn | VARCHAR | Primary business key |
| user_id | VARCHAR | Graph `/users/{id}` GUID |
| display_name | VARCHAR | — |
| mail | VARCHAR | Primary email (may differ from UPN) |
| account_enabled | BOOLEAN | Filter for active users only |
| upn_domain | VARCHAR | Indexed for `@etzhayyim.com` filter |
| first_seen_at / last_seen_at | VARCHAR | 入退社追跡 |

### `vertex_m365_sync_state` (per-upn watermark)

| column | type | 用途 |
|---|---|---|
| upn | VARCHAR | |
| data_kind | VARCHAR | `email` / `calendar` / `files` (extensible) |
| last_sync_at | VARCHAR | Pipeline 最終実行 |
| last_received_at | VARCHAR | データ上の watermark (次回 `$filter=receivedDateTime ge`) |
| record_count | BIGINT | 累計 |
| error_count / last_error / last_error_at | | Dead-letter |
| throttle_until | VARCHAR | 429 backoff (次 cron で skip) |
| status | VARCHAR | `idle` / `running` / `error` |
| run_id | VARCHAR | 現在進行中の pipeline run |

## Migration ロードマップ (Python script → T1 actor)

| Phase | 作業 | 状態 |
|---|---|---|
| 1 | Host lexicon + TS impl + dispatcher wiring | ✅ (このドキュメント時点) |
| 2 | Migration apply (`pnpm db:migrate`) + types regen (`pnpm db:gen`) | ⏳ |
| 3 | Seed `vertex_m365_user` 手動 1 回 (daily cron 前の bootstrap) | ⏳ |
| 4 | Wrangler secret `m365_client_secret` 登録 + ActorExecutor Worker に bind | ⏳ |
| 5 | Actor manifest 登録: `etzhayyim xrpc com.etzhayyim.actor.migrate -d '{"manifestPath":"20-actors/m365-ingest/actor-manifest.jsonld"}'` | ⏳ |
| 6 | `syncUser` を各 UPN で 1 回 invoke (initial full sync) | ⏳ |
| 7 | Delta cron 稼働確認、throttle / error rate モニタリング 1 週間 | ⏳ |
| 8 | Python script archive (`~/.etzhayyim/ingest/m365_mail_ingest.py` → `_archive/`) | ⏳ |

## 非機能要件

| 項目 | 設計値 |
|---|---|
| Cron 間隔 (delta) | 15 min |
| Per-run timeout | 30 min (長尾 mailbox 対応) |
| Bounded concurrency | 4 (per-mailbox 1500req/hr 考慮) |
| Token lifespan | 1h (55min cache skew) |
| Throttle backoff | 2s → 32s (5 attempts) |
| Daily user enum | 03:00 JST |
| Rate budget | ~4,600 req/day (13K/10min 上限の 1% 以下) |
| Storage growth | ~1KB × 4.6M rows = 4-8GB (1 tenant) |
| PII tier | 3 (per ADR-0014); Signal-enveloped subject/body |

## 関連

- `20-actors/m365-ingest/actor-manifest.jsonld` (declaration SSoT)
- `20-actors/m365-ingest/CLAUDE.md` (run-book)
- `00-contracts/lexicons/com/etzhayyim/host/m365/*.json` (4)
- `00-contracts/lexicons/com/etzhayyim/apps/m365Ingest/*.json` (3)
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/capabilities/m365.ts`
- `30-graph/graph-schema/migrations/20260417190000_vertex_m365_sync_state.ts`
- ADR-0014 PII Tier 3 + Cohort-First Pattern
- `90-docs/260408-actor-executor-p5p3-architecture-design.md` (T1/T2 executor topology)
