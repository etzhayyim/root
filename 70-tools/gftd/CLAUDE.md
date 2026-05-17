# 70-tools/gftd — CLI and Build Tooling

App が import する Go パッケージ。新規 app の標準は TS native + `@gftd/magatama-host-sdk` (WIT contract)。

## Package Index

| Package | Import Path | 説明 |
|---|---|---|
| `cdn` | `github.com/etzhayyim/root/70-tools/cdn` | S3/CDN upload client (SigV4) |

### CLI Tools

| Tool | 場所 | 説明 |
|---|---|---|
| `gftd` | `cmd/gftd/` | build/deploy CLI (TS native DEFAULT → Cloudflare Worker)。`gftd authn signin` で OAuth2 PKCE 認証。`buildWranglerJSON()` で wrangler.jsonc 生成 → `npx wrangler deploy` |

**CLI read/write path**:
- **Read commands** (`apps`, `actors-jokyo`, `apps-kyumei-koji`, `deps`, `monitor-did`, `coverage world`, `coverage domain`): Hyperdrive direct primary、PDS XRPC 自動 fallback。B2 SQL (`r2sql.go`) は deprecated (2026-04-11) — 新規コードは Hyperdrive direct または PDS XRPC を使用。
- **Write commands** (`seed`, `murakumo`, `actors shinka`): PDS XRPC のみ (PDS → graph SQL write path → IcebergWriter WAL)。
- **Agent invocation** (`xrpc`): Claude Code chat agents が deployed App の任意の XRPC endpoint を呼ぶ。`setAuthHeaders()` による Bearer token + X-Active-DID 認証。`70-tools/gftd/gftd/xrpc.go`

#### gftd auth (CRITICAL)

`gftd auth` — authn.etzhayyim.com OAuth2 Auth Code + PKCE 認証。PDS API 呼び出しに必要。

| Subcommand | 動作 |
|---|---|
| `gftd authn signin` | Browser → authn.etzhayyim.com OAuth2 PKCE (localhost:9876) → AT Protocol JWT 保存 |
| `gftd authn token` | JWT を stdout 出力。`curl -H "Authorization: Bearer $(gftd authn token)"` |
| `gftd authn whoami` | 認証情報表示 (sub, email, active DID, expiry) |
| `gftd authz dids` | 認証ユーザが制御する DID 一覧 (kagami graph `DIDDocument.controller` query) |
| `gftd authz switch <did>` | Active DID を切替 (account root actor / sub-actor DID として操作)。shorthand: `gftd authz switch moj` → `did:web:moj.etzhayyim.com` |
| `gftd authz switch --reset` | account root の default human sub-actor に戻す |
| `gftd authn signout` | `~/.gftd/auth.json` 削除 |
| **`gftd agent-token --lxm <nsid>`** | **Programmatic agent 向け 60s Service Auth JWT (→ §`gftd agent-token`)**。`com.atproto.server.getServiceAuth` を wrap、`lxm` 1 method に scope |
| **`gftd agent organism status`** | **Local artificial organism の稼働確認入口 (→ §`gftd agent organism status`)**。health / viability / process / knowledge graph fitness を確認し、WebUI も起動できる |

**DID 切替モデル**: gftd の正規モデルは `account = actor = org DID`。human / service / team / legal などはすべて root actor 配下の sub-actor DID。`gftd authz switch` は root actor 自体またはその sub-actor を active DID として切替え、`X-Active-DID` header で PDS に送信する。`setAuthHeaders(req)` helper が Bearer token + active DID を一括設定。

**Token 解決優先順** (`resolveGFTDToken()`): `GFTD_TOKEN` env (API key `sk_live_*` or JWT) → `~/.gftd/auth.json` (id_token 優先、fallback: access_token)

**4 層認証 (PDS `authenticate()`):**

| Level | Token source | 経路 |
|---|---|---|
| `internal` | `x-magatama-verified: true` header | user Worker → PDS (service binding RPC, token 不要) |
| `internal` | ES256 Service Auth JWT (DID-signed) | Agent/infra → PDS |
| `session` | API key (`sk_live_*` / `sk_test_*`) | CLI (`GFTD_TOKEN`), SDK, LLM Agent |
| `session` | AT Protocol JWT (HS256, authn.etzhayyim.com 署名) | 開発者 CLI (`gftd authn signin`), browser Passkey |

**API Key 管理**: `gftd authz create-api-key` / `gftd authz list-api-keys` / `gftd authz revoke-api-key`。UI: `yoro.etzhayyim.com/settings/developer`。XRPC: `ai.gftd.auth.createApiKey` / `listApiKeys` / `revokeApiKey`

#### gftd code-quality

`gftd code-quality` — Run cargo-machete, cargo tree -d, go vet, go mod tidy, jscpd, magatama-lint, frontend-lint, sql-injection across workspaces. Outputs unified score (0-100).

**magatama-lint rules (CRITICAL)**:

| Rule ID | Severity | 検出対象 |
|---|---|---|
| `raw-sql-exec` | critical | `SqlExec()` / `SqlSuspend` — **禁止**: G() builder or WRecord() を使用 |
| `raw-sql-query` | high | `SqlQueryMap()` — **禁止**: G() builder を使用 |
| `raw-sql-string` | high | `"MATCH (` string literal — G() builder を使用 |
| `sql-sprintf` | critical | `fmt.Sprintf` + SQL — injection risk。`safeLabel()` ガードまたは G() builder 必須 |
| `sql-full-scan` | critical | SQL WHERE に promoted column identity filter なし — B2 SQL 全件スキャン。repo/did/rkey/nanoid 等の promoted column 必須 |
| `large-table-count-star` | critical | `COUNT(*) FROM <10M+ row table>` — ADR-0033 違反。`db.CountFromStats()` / `rw_catalog.rw_table_stats` 経由に置換する。対象 table: edge_links_to / edge_links_to_domain / vertex_page / vertex_legal_entity / vertex_repo_record |
| `kebab-collection` | high | kebab-case collection kind — camelCase 必須 |
| `snake-collection` | info | snake_case collection kind — camelCase 必須 (AT Protocol standard) |
| `gexecraw-write` | critical | `GExecRaw(INSERT/UPDATE/DELETE/MERGE)` — **禁止**: `ComAtprotoRepoCreateRecord()` for domain write, `G()` for read |
| `dot-collection` | high | dot-separated collection (`oshi.video`) — camelCase (`oshiVideo`) を使用 |
| `did-double-prefix` | high | `did:web:${var}` で `var ≠ appId/nanoid` かつ `startsWith("did:")` / `ensureDid()` ガードなし |
| `pds-hardcode` | critical | `appId: "pds"` — repo-derived appId を使用 |
| `init-schema` | critical | DDL/initSchema — kagami はスキーマレス (schema-on-read) |
| `sql-write` | critical | SQL INSERT — `ComAtprotoRepoCreateRecord()` を使用 |
| `kv-usage` | critical | KvGet/KvPut — W Protocol Event Stream を使用 |
| `dosqlexec` | critical | DOSqlExec — `G()` for read, `ComAtprotoRepoCreateRecord()` for write |
| `xrpc-usage` | info | `/xrpc/` は唯一の API surface (AT Protocol native, η=83%)。全コードは `/xrpc/{NSID}` を使用 |
| `batch-polling` | high | `cmdCollect*`, `cmdEvaluateBatch`, `cmdTranslateToAll` — Design E reactive pipeline (ComAtprotoSyncSubscribeRepos) に移行 |
| `dual-write` | high | `WRecord(` + `ATPost(` in same function — Shannon 冗長。Design E: AppBskyFeedPost for social, ComAtprotoRepoCreateRecord for domain data |
| `domain-data-social-mix` | critical | domain/internal data in `AppBskyFeedPost()` — Design E 違反: public social post 専用。domain data は `ComAtprotoRepoCreateRecord()` を使用 |
| `social-via-domain-write` | high | social action (`post`/`like`/`repost`/`follow`) via domain write — Design E: social は AppBskyFeedPost/AppBskyFeedLike 等を使用 (AT Record = federable) |
| `fallback-impl` | high | `func fallbackXxx(` — hardcoded fallback data bypassing real data path。G() graph read + error handling を使用 |
| `stub-impl` | high | `var default/sample/mock/fake/dummy/staticXxx = []` — hardcoded stub data array。G() graph read or ComAtprotoRepoCreateRecord() を使用 |
| `missing-governance` | high | `magatama.jsonld` に `governance` block なし — yoro profile governance 表示不可 |
| `missing-convo-system-prompt` | high | `magatama.jsonld` に `convoSystemPrompt` なし — DM agent 会話無効 |
| `vanity-did-repo` | critical | `actorDID = "did:web:{vanity}.etzhayyim.com"` — AT Protocol: repo = nanoid DID。`` `did:web:${appNanoid}.etzhayyim.com` `` を使用 |
| `vanity-did-postAs` | critical | `postAs("did:web:{vanity}.etzhayyim.com", ...)` — vanity DID で投稿禁止。selfRepo or identityCreate() の nanoid DID を使用 |
| `vanity-did-dispatch` | critical | dispatch payload に vanity DID — nanoid DID を使用 (Invoke 先は除外) |
| `sync-serve-call` | critical | `sdk.app.serve()` 直接呼出 — 削除。`createWorkerExport()` が `serveAsync()` を await + error handling 付きで呼出。sync `serve()` は `void rpc()` で silent fail |
| `missing-export-default` | critical | `export default createWorkerExport()` 欠落 — CF Worker entry point 必須 |
| `hardcoded-appid` | critical | `const appId = "xxx"` — Shannon 冗長 (entropy=0)。SDK が `APP_NANOID` env var から自動取得 (`magatama.jsonld` → `gftd deploy` → env) |
| `hardcoded-actor-did` | critical | `const actorDID = ...` — appId 派生の冗長。`sdk.pds.selfRepo` or env `APP_NANOID` を使用 |
| `legacy-create-component-host-sdk` | high | `function createComponentHostSDK` — `createWorkerExport()` (引数なし) に移行。`createDefaultHostSDK` が env から自動構築 |
| `legacy-hardcoded-appdef` | high | `appDef: { id: "xxx" }` in app.ts — env vars から自動解決。手書き禁止 |
| `payload-string-collection` | critical | `payload: "ai.gftd..."` bare string — `{ collection: "...", recordJson: JSON.stringify(...) }` を使用 |
| `broken-dispatch-brace` | critical | dispatch payload の `}` 欠落 — `payload: { text: \`...\` } });` |
| `non-async-await` | critical | non-async function 内で `await` 使用 — `async` keyword 必須。sync 関数の `await` は未解決 Promise を返す |

**sql-injection rules (PDS index.ts)**:

| Rule ID | 検出対象 |
|---|---|
| `esc-interpolation` | `${esc(` — parameterized `$param` に移行済み |
| `template-sql` | template literal in SQL — parameterized `$param` に移行済み |
| `did-double-prefix` | `did:web:${var}` で `var ≠ appId/nanoid/cl(r.rkey)` かつ `startsWith("did:")` / `ensureDid()` ガードなし |

**frontend-lint rules (Design E compliance, `.svelte`/`.ts` in `60-apps/*/svelte/src/`)**:

| Rule ID | Severity | 検出対象 |
|---|---|---|
| `direct-app-fetch` | high | `fetch(\`https://${...}.etzhayyim.com/api/\`)` — atproto.etzhayyim.com 経由に変更 (Data Gateway Consolidation) |
| `xrpc-frontend` | info | `/xrpc/` は唯一の API surface (AT Protocol native)。全 frontend は `/xrpc/{NSID}` via atproto.etzhayyim.com を使用 |

#### gftd coverage (World Coverage Analysis)

`gftd coverage` — 全世界カバレッジ分析。403 ドメインの世界総数に対する coverage % / gap % / remaining 数を算出。

**Read path**: Hyperdrive direct query → RisingWave。`graphar.vertex_*` / `graphar.edge_*` (P10v2 per-label tables)。

**Subcommands**:

| Subcommand | 動作 |
|---|---|
| `gftd coverage` | World coverage (default) — Hyperdrive direct で `catalog.graphar.vertex_*` から App/DID/Profile カウント |
| `gftd coverage domain` | Domain coverage reconciliation — `mv_domain_coverage_live` read model (0014 + 20260415131000 restore)。Live reconciliation 11/12 domains。設計: `90-docs/260411-domain-expansion-agent-loop-design.md` |
| `gftd domain-ingest` | Canonical domain write path — local datasets / Common Crawl export を PDS に投入。Runbook: `90-docs/260423-domain-ingest-runbook.md`, 設計: `90-docs/adr/0057-common-crawl-domain-ingest-coverage-topology.md` |
| `gftd coverage test` | Test coverage — Rust/Go/TS workspace のテスト実行 + line coverage |
| `gftd coverage actors` | Actor metadata completeness (η) — per-actor score, grade, missing fields, LLM healing |

**`gftd domain-coverage` は `gftd coverage domain` に改名。** 旧コマンドは deprecated alias として残存 (stderr warning あり)。

**DB default (Go CLI local):** `postgres://root@127.0.0.1:14566/dev?sslmode=disable`  
(`GFTD_DATABASE_URL` / `DATABASE_URL` が未指定時)

**Flags (world coverage)**:

| Flag | Default | 説明 |
|---|---|---|
| `--r2sql` | `true` | **Deprecated (2026-04-11)**: Hyperdrive direct query (P10v2 per-label tables)。false 時は PDS XRPC にフォールバック |
| `--pds` | `https://atproto.etzhayyim.com` | PDS base URL (B2 SQL fallback 時に使用) |
| `--json` | `false` | JSON output |
| `--top` | `30` | top N workers by DID count |
| `--domain` | `""` (all) | filter by domain (e.g. `dns`, `hanrei`, `autorace`) |
| `--offline` | `false` | offline mode (local magatama.jsonld scan only, no PDS query) |
| `--root` | git root | repo root override |

**403 World domains (22 sectors, 7-depth levels, full list in `world_coverage.go`)**:

| Sector | Domains | Key examples | Scale |
|---|---|---|---|
| 産業・製造 | 19 | seizo (工程1T/yr), hinshitsu_kensa (100B/yr), BOM (500M) | ~1.2T |
| 個品シリアル | 14 | SGTIN (1T), shokuhin_lot (1T), IMEI (20B) | ~2.1T |
| 建物・BIM | 10 | haikan (300B), densen (225B), kouzoutai (150B) | ~995B |
| トランザクション | 4 | kessai (1T/yr), invoice (500B/yr), nimotsu (200B/yr) | ~2.2T |
| 契約 | 12 | riyo_kiyaku (10B), subscription (5B), koyo (3.5B) | ~33B |
| 金融 | 12 | kabushiki_chumon (100B/yr), bank_account (10B) | ~116B |
| 医療 | 8 | yobou_sesshu (15B), iryo_seikyu (10B/yr) | ~35B |
| デジタル・ネットワーク | 15 | MAC (20B), IoT (18B), phonenumber (15B) | ~93B |
| 車両・道路インフラ | 30 | vehicle (1.5B), douro_hyouji (1B), nirin (500M) | ~10B |
| 人間・社会 | 12 | natural_person (8.1B), life_event (5B/yr) | ~30B |
| 農業・食品 | 7 | kachiku (30B), shukaku_cycle (5B/yr) | ~35B |
| コンテンツ・フィクション | 27 | photos (5T/yr), webpage (50B), character (500M) | ~5T |
| 知財 | 8 | patent (200M), chosakuken (100M), shohyo (70M) | ~450M |
| 法・証拠 | 17 | saiban_shoko (500M), hourei (10M), hanrei_global (50M) | ~2B |
| エネルギー | 9 | energy_consumption (10B/yr), souden_infra (500M) | ~11B |
| 宇宙・天体 | 9 | tentai_star (1.8B), satellite (10K) | ~1.8B |
| ソフトウェア・アプリ | 28 | code_file (100B), sw_license_key (10B), app_review (10B) | ~196B |
| 脅威インテリジェンス | 42 | leaked_credential (15B), malware_sample (2B), exposed_service (500M) | ~20B |
| 廃棄・リサイクル | 18 | e_waste (50B/yr), haiki_manifest (5B/yr) | ~69B |
| アダルト (restricted) | 6 | adult_content (500M), adult_age_verification (100M) | ~615M |
| 製薬プロセス | 6 | gmp_batch (500M/yr), yugai_jisho (20M) | ~526M |
| その他 (教育/自然/行政) | 90 | shiken_seiseki (5B/yr), shikaku (2B) | ~20B |

**Monetization Priority (S→E tier, 3-axis scoring: Ad×Agent×Data)**:
- **S tier (即収益化)**: gtin, shohin, okaimono, oryori, software, ios_app, android_app, game_store, music, minpaku
- **A tier (高CPA)**: loan, insurance, real_estate, creditcard, kuruma, apparel, kagu, isin
- **B tier (Agent先行)**: shikaku, hanrei, kaigo, maps_poi, iryo, koza, chotatsu

**動作モード**:
- **Live** (default): `gftd authn signin` 後に Hyperdrive direct (`catalog.graphar.vertex_*`) で legacy app compatibility label, `:DID`, `:Profile` をカウント。`did:web:{app}.etzhayyim.com` prefix でドメイン分類。失敗時は PDS XRPC へ自動 fallback
- **Offline**: `60-apps/*/wasm/*/magatama.jsonld` スキャンでローカル app 数をカウント (PDS/B2 SQL 不要)

**Output (text)**: domain ごとに `COLLECTED` / `GAP` / `REMAINING` 列を表示 + bar chart。末尾に Gap Tier Summary (coverage ≥50% / 10-50% / 1-10% / <1% でドメインをグループ化 + 全 tier 合計 remaining 数) + `World Coverage Rate` および `World Gap %` を表示。

**Output (JSON)**: `wcDomainResult` に `gap` (float64, %) と `remaining` (int) フィールドを追加。

#### gftd coverage test

`gftd coverage test` — Run tests and collect line coverage across Rust/Go/TypeScript workspaces. Outputs per-directory test counts + optional line coverage percentage.

**Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--lang` | `""` (all) | comma-separated languages: `rust,go,ts` |
| `--coverage` | `true` | collect line coverage (requires `cargo-llvm-cov` / `go tool cover` / `@vitest/coverage-v8`) |
| `--json` | `false` | JSON output |
| `--timeout` | `600` | per-language timeout in seconds |
| `--workspace-dir` | git root | workspace root override |

**Language runners**:

| Language | Discovery | Test Runner | Coverage Tool |
|---|---|---|---|
| **Rust** | `Cargo.toml` with `[workspace]` under `30-graph`, `20-actors`, `40-engine/kami-engine` | `cargo test --workspace -- --format=json` | `cargo llvm-cov --workspace --json` (fallback: no coverage) |
| **Go** | `go.mod` in `70-tools/gftd/gftd` | `go test -json ./...` | `go test -coverprofile` + `go tool cover -func` |
| **TypeScript** | `package.json` with vitest/jest in `50-infra/cloudflare/workers/atproto`, `40-engine/svelte/appshell`, etc. | `npx vitest run --reporter=json` | `--coverage` + Istanbul summary |
| **Playwright** | `playwright.config.ts` + `@playwright/test` in `60-apps/ai-gftd-project-yoro/.../svelte` | `npx playwright test --reporter=json` | N/A (E2E + performance budget tests) |

**Output fields**: `test_count`, `pass_count`, `fail_count`, `skip_count`, `line_coverage_pct`, `duration`

#### gftd coverage actors (Actor Metadata Completeness)

`gftd coverage actors` — Actor metadata completeness (η) 分析 + Murakumo LLM 自律 healing。Design: `90-docs/260409-shinka-coverage-healing-design.md`

**Read path**: Hyperdrive direct query → RisingWave `graphar.vertex_actor`。

**Subcommands**:

| Subcommand | 動作 |
|---|---|
| `gftd coverage actors` | η summary (default) |
| `gftd coverage actors list` | Per-actor coverage scores (--grade, --limit) |
| `gftd coverage actors eta` | System-wide η metric |
| `gftd coverage actors inspect` | Missing fields for specific actor (--did) |
| `gftd coverage actors heal` | Trigger healing for worst N actors via Murakumo LLM |

**Critical Fields (5, weighted)**:

| Field | Weight | 説明 |
|---|---|---|
| `wit_imports` | 25% | WIT contract imports |
| `convo_system_prompt` | 25% | DM convo system prompt |
| `capabilities` | 20% | MCP capabilities |
| `performer_type` | 15% | Actor type (service/system) |
| `operator` | 15% | Operator organization |

**Grades**: critical (3+ missing), incomplete (1-2 missing), complete (all present)

**Heal flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--limit` | `10` | Max actors to heal per cycle |
| `--dry-run` | `false` | Generate fixes but don't write |
| `--murakumo` | `true` | Use Murakumo LLM |
| `--model` | `qwen3-30b-a3b` | LLM model |
| `--concurrency` | `4` | Parallel healing |
| `--did` | `""` | Heal specific actor only |

**Healing per field**: `convo_system_prompt` → Murakumo LLM 生成、`wit_imports` → default imports、`capabilities` → Murakumo LLM 推論、`performer_type` → `"service"`、`operator` → `"amanomibashira"` (宗教法人・任意団体・blockchain 登記。日本国 宗教法人法 上の登記宗教法人ではない)

#### gftd docs-gen

`gftd docs-gen` — factual schema を Parquet/local sources から自動生成。Shannon 原則: 事実系コンテンツのみ (labels/collections/deps)。ルール系は CLAUDE.md に残す。

| Subcommand | 動作 |
|---|---|
| `gftd docs-gen schema` | magatama.jsonld + G() scan → JSON or schema.auto.md |

**Flags (schema)**:

| Flag | Default | 説明 |
|---|---|---|
| `--dir` | `.` | magatama.jsonld を含む component ディレクトリ |
| `--all` | `false` | `60-apps/ai-gftd-project-*/wasm/*/` を全スキャン → schema.auto.md を各 component に書き出し |
| `--format` | `json` | `json` or `md` |
| `--out` | stdout | 出力ファイルパス (`--all` 時は無視) |

**データソース**:

| ソース | 取得内容 |
|---|---|
| `magatama.jsonld` | app / nanoid / DID / collections / performerType |
| `wrangler.jsonc` | service bindings (HYPERDRIVE, PDS_SERVICE 等) |
| `src/*.ts` | `G("Label")` パターン → graph labels |
| `wit/world.wit` | WIT imports |

**MCP tool**: `gftd.schema` — `tools/call gftd.schema { project: "autorace" }` で kagami live query (labels + collections)。PDS `mcp-adapter.ts` の BUILTIN_TOOLS に登録済み。

#### gftd source-graph (CRITICAL)

`gftd source-graph` — 3-Layer Hybrid source-level annotation graph + policy enforcement。Shannon 冗長度 ~8%。設計: `90-docs/260324-source-graph-hybrid-design.md`

**3 Layers**:
- **L1: WIT + magatama.jsonld** (既存 artifact、自動) — import/export, performerType, DID, collections
- **L2: AST** (`go/ast` + TS/Rust regex、自動) — WRecord kinds, SQL labels, Commands, Invoke, Serve
- **L3: `@gftd:` コメント** (差分手書き) — authority, contract, sensitivity, cross-app intent

**Subcommands**:

| Subcommand | 動作 |
|---|---|
| `gftd source-graph scan` | 3-layer scan → JSON graph |
| `gftd source-graph violations` | 8 violation rules 検出 + source_graph_score |
| `gftd source-graph sql` | kagami 投影用 SQL MERGE 文生成 |
| `gftd source-graph dot` | Graphviz DOT 出力 |

**Annotation directives** (`// @gftd:<directive> <value>`):

| Directive | Scope | AST 不可分の理由 |
|---|---|---|
| `@gftd:authority <kind>/<id>` | file | 法的権限は code に現れない |
| `@gftd:contract <cat>/<id>` | file | 契約根拠は code に現れない |
| `@gftd:sensitivity <level>` | file | データ分類は L1 jsonld で部分カバー、残りは宣言 |
| `@gftd:owner <did>` | file | 責任 DID (DID 生成と異なる) |
| `@gftd:calls <did>#<method>` | func | AST の Invoke() と補完 (intent 宣言) |
| `@gftd:writes/reads <coll>` | func | AST の WRecord/G() と補完 |
| `@gftd:rule <rule-id>[,...]` | file/func | 適用ルール宣言 |
| `@gftd:ref <doc-path>` | file | 設計 doc 参照 |
| `@gftd:supersedes <path>` | file | 置換元ファイル |
| `@gftd:visibility <level>` | file/func | public/internal/restricted |
| `@gftd:import <wit>` | file/func | WIT 依存 (L1 と補完) |
| `@gftd:lexicon <nsid>` | file/func | AT Lexicon 対応 |

**Violation rules (8)**:

| Rule | Severity | 検出 |
|---|---|---|
| `wit-import-drift` | warning | `@gftd:import` 宣言が `world.wit` に未存在 |
| `sensitivity-escalation` | error | confidential source が public DID 呼出 |
| `authority-gap` | info | sovereign 宣言に treaty なし |
| `dead-supersedes` | warning | supersedes 先ファイル不存在 |
| `shannon-redundancy` | warning | 同一 collection に複数 app が書込 |
| `rule-no-dual-write` | error | no-dual-write ルールに writes 2+ |
| `dead-ref` | warning | ref 先ドキュメント不存在 |
| `circular-dependency` | error | calls グラフに循環 |

**Score model**: `25% auto_extract_rate + 25% violation_free_rate + 20% annotation_coverage + 15% authority_coverage + 15% reference_integrity`

#### gftd actors migrate-to-plc (ADR-0014 Phase 5)

`gftd actors migrate-to-plc --actor <name>` — Thin CLI client for did:web → did:plc migration. Calls PDS XRPC endpoint `ai.gftd.plc.migrateActor` which signs genesis op via rotation key (ADR-0010 D1 custody) and registers DID with plc.etzhayyim.com.

**Flow**:
1. CLI validates actor exists in `deps.toml [[mitama_actors]]`
2. POST `atproto.etzhayyim.com/xrpc/ai.gftd.plc.migrateActor` with `{actor, handle, dryRun}`
3. PDS side: load rotation key → build + sign genesis op → compute `did:plc:{24-char}` → POST to `plc.etzhayyim.com`
4. CLI patches deps.toml: `did = "did:plc:..."` + insert `legacy_did_web = "did:web:..."` (6-month grace)

**Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--actor` | (required) | actor name in deps.toml |
| `--handle` | auto | handle for alsoKnownAs (default: `{actor}.etzhayyim.com`) |
| `--apply` | `false` | write changes to deps.toml (default: preview) |
| `--pds` | `https://atproto.etzhayyim.com` | PDS XRPC base URL |
| `--offline` | `false` | mock PDS response (local dev / CI) |
| `--json` | `false` | emit JSON response |
| `--deps` | `deps.toml` | source path |

**Example** (offline dry-run):
```bash
$ gftd actors migrate-to-plc --actor adr --offline
  actor:       adr
  current DID: did:web:adr.etzhayyim.com
  handle:      adr.etzhayyim.com
  PDS:         https://atproto.etzhayyim.com
  mode:        offline + dry-run (mock response, no write)

  ── Response
    new DID:     did:plc:adraaaaaaaaaaaaaaaaaaaaa
    genesis CID: bafysimulated000000000000000000000000000
    PLC URL:     https://plc.etzhayyim.com/did:plc:adraaaaaaaaaaaaaaaaaaaaa
    legacy DID:  did:web:adr.etzhayyim.com (grandfathered 6 months)
```

**Usage in Phase 5 pilot**:
```bash
# Preview (no write, no PDS call)
gftd actors migrate-to-plc --actor legal-aid --offline

# Dry-run (PDS call, no write)
gftd actors migrate-to-plc --actor legal-aid

# Apply (PDS call + write deps.toml)
gftd actors migrate-to-plc --actor legal-aid --apply

# Verify
gftd identifier-audit --deps deps.toml | grep legal-aid
```

**PDS XRPC endpoint** (server-side implementation, still todo):
```
POST /xrpc/ai.gftd.plc.migrateActor
Request:  { "actor": "legal-aid", "handle": "legal-aid.etzhayyim.com", "dryRun": false }
Response: { "did": "did:plc:abcdef...", "genesisCid": "bafy...", "plcUrl": "...", "handle": "...", "legacyDid": "did:web:..." }
```

Server side needs: rotation key load from D1 (ADR-0010), dag-cbor encode, ES256K sign, sha256 hash, POST to plc.etzhayyim.com.

Source: `70-tools/gftd/gftd/actor_migrate_plc.go`。ADR: `90-docs/adr/0014-self-hosted-did-plc.md`。

#### gftd dns-sync (ADR-0013)

`gftd dns-sync` — ADR-0013 Phase 3 tool。deps.toml `[[mitama_actors]]` + `[[legacy_nanoids]]` を Cloudflare DNS records に同期。管理対象は `gftd:adr-0013:` comment prefix を持つレコードのみ (手動 record は不可侵)。

**管理対象 record**:
- `_atproto.{handle}.etzhayyim.com` TXT `"did={did}"` — AT Protocol handle verification (90 entries)
- `{legacy_nanoid}.etzhayyim.com` CNAME `{handle}.etzhayyim.com` — Phase 3 grace (90 entries, 2026-10-01 削除予定)

**Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--apply` | `false` | 実際に DNS records を変更 (default は dry-run) |
| `--json` | `false` | JSON plan output (CI 組込用) |
| `--no-cf` | `false` | offline mode — Cloudflare API skip、desired records を print のみ |
| `--zone-name` | `etzhayyim.com` | CF zone name |
| `--include-nanoid` | `true` | legacy nanoid CNAMEs を含める |
| `--include-txt` | `true` | _atproto TXT records を含める |
| `--deps` | `deps.toml` | source path |
| `--emit-routing-map` | `""` | 指定 PATH に `legacy-nanoid-map.ts` を出力して exit (`50-infra/cloudflare/workers/routing-gateway/src/legacy-nanoid-map.ts`) |
| `--populate-bindings` | `""` | 指定 PATH の `wrangler.jsonc` `services` array を 93 Service Bindings (PDS_WORKER + PLC_DIRECTORY + 90 actor) で置換して exit。idempotent |

**Token resolution** (同 `deploy.go resolveCloudflareToken()`):
`CLOUDFLARE_API_TOKEN` → `CF_API_TOKEN` → `GFTD_CLOUDFLARE_API_TOKEN` → `~/Library/Preferences/.wrangler/config/default.toml` OAuth → backup files

**Output** (plan diff):
```
── CREATE (180)
  TXT     _atproto.adr.etzhayyim.com                   "did=did:web:adr.etzhayyim.com"        missing
  CNAME   adr1m4d0.etzhayyim.com                       adr.etzhayyim.com                      missing
  ...
── UPDATE (0)
── DELETE (0)
```

**Use cases**:
- 初回 bulk sync: `gftd dns-sync --apply` で 180 records を一括投入
- 定期 drift check: `gftd dns-sync --json | jq .actions` で CI 監視
- 新規 actor 追加後: `gftd dns-sync --apply` で自動 provisioning
- Offline preview: `gftd dns-sync --no-cf` で desired records 確認 (CF 認証不要)
- routing-gateway map 同期: `gftd dns-sync --emit-routing-map=50-infra/cloudflare/workers/routing-gateway/src/legacy-nanoid-map.ts` で 90 entry の TS map を auto-generate (deps.toml SSoT、`go test TestEmitRoutingMapTS` で deterministic 検証済)
- routing-gateway bindings 同期: `gftd dns-sync --populate-bindings=50-infra/cloudflare/workers/routing-gateway/wrangler.jsonc` で `services[]` を 93 entry (PDS_WORKER + PLC_DIRECTORY + 90 actor WORKER_*) で置換。CI workflow `routing-gateway-drift` job で drift detect

Source: `70-tools/gftd/gftd/dns_sync.go`。ADR: `90-docs/adr/0013-dns-routing-consolidate.md`。

#### gftd deps kv-sync (ADR-0014 Phase 5)

`gftd deps kv-sync` — populate Cloudflare KV namespace `DEPS_REGISTRY` から PDS handlers/plc が actor lookup できるように `[[mitama_actors]]` を bulk PUT。

**Schema** (per actor key):
```
key:   actor:{name}
value: { name, did, handle, nanoid?, legacyDidWeb?, description? }

key:   actors:index
value: ["adr", "bengoshi", ...]  (sorted)
```

**Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--apply` | `false` | bulk PUT 実行 (default: dry-run) |
| `--diff` | `false` | 既存 KV state を CF API で fetch し add/update/delete/keep plan を表示 |
| `--no-cf` | `false` | offline mode (CF API skip、desired payload を print) |
| `--json` | `false` | JSON plan output |
| `--account-id` | env `CF_ACCOUNT_ID` | Cloudflare account id |
| `--namespace-id` | env `CF_DEPS_REGISTRY_KV_ID` | KV namespace id for DEPS_REGISTRY |
| `--deps` | `deps.toml` | source path |

**`--diff` 注記**: key 存在有無のみで add / update / delete を分類 (value fetch は 90+ round-trip コスト回避のため省略)。desired に残る既存 key は conservative に `update` 扱い → bulk PUT は idempotent なので安全。CI drift 検出用途は `--no-cf --json` (workflow job `kv-sync-drift`) が offline なので高速。

**Use case** — PDS deploy 後、`handlers/plc/index.ts`'s `lookupActor()` が runtime に actor metadata をひける状態にする:

```bash
# Local preview
gftd deps kv-sync --no-cf

# Diff vs live KV (add/update/delete plan)
gftd deps kv-sync --diff --account-id=$CF_ACCOUNT_ID --namespace-id=$CF_DEPS_REGISTRY_KV_ID

# Production (CF Workers KV bulk PUT, ≤10K entries/req)
gftd deps kv-sync --apply --account-id=$CF_ACCOUNT_ID --namespace-id=$CF_DEPS_REGISTRY_KV_ID
```

90 actor → 91 KV keys (90 actor:{name} + 1 actors:index)。determinic order (test 6/6 pass)。

Source: `70-tools/gftd/gftd/deps_kv_sync.go`。Consumer: `50-infra/cloudflare/workers/atproto/src/handlers/plc/index.ts` `DEPS_REGISTRY` binding。

#### gftd identifier-audit (ADR-0019)

`gftd identifier-audit` — ADR-0019 (atproto-native 5-layer identifier topology) 違反検出。deps.toml から `[[mitama_actors]]` + `[[legacy_nanoids]]` を text scan parse (外部 TOML lib 不要)。

| Flag | 説明 |
|---|---|
| `--json` | JSON output (total_actors / legacy_nanoids_count / violations / by_severity / by_rule) |
| `--severity` | filter by `critical` / `high` / `medium` / `low` |
| `--deps` | path to deps.toml (default: `deps.toml` in CWD) |

**検出 rule**:

| Rule ID | Severity | 検出 |
|---|---|---|
| `mnemonic-nanoid` | high | nanoid が name の leet 変換 (例: `k4m13ng1` ← kami) |
| `did-web-grandfathered` | medium | did:web 使用 (Phase 5 opt-in migration 候補) |
| `missing-legacy` | medium | `nanoid` field あるが `[[legacy_nanoids]]` entry 無し |
| `handles-missing` | high | `handles[]` と `domain` 両方 無し |
| `handles-schema-legacy` | low | `domain` のみで `handles[]` 未設定 (ADR-0019 schema 未対応) |
| `orphan-legacy` | low | `[[legacy_nanoids]]` entry に対応する `[[mitama_actors]]` 無し |

**Output (2026-04-14 baseline)**:
- 90 actors / 90 legacy_nanoids
- 20 mnemonic-nanoid (high) — Phase 4 で全削除目標
- 90 did-web-grandfathered (medium) — Phase 5 個別 opt-in
- 90 handles-schema-legacy (low) — Phase 2.5 で `handles[]` 一括追加可

Source: `70-tools/gftd/gftd/identifier_audit.go`。ADR: `90-docs/adr/0019-atproto-native-identifier-topology.md`。

#### gftd dodaf

`gftd dodaf` — DoDAF v2-aligned Rule Registry (Parquet + RisingWave). Stores all Claude-facing rules as structured data queryable by file context and tags. Data: `80-data/dodaf/{tv1_standards,av2_dictionary,ov5_activities}.parquet`. MCP surface: `gftd.dodaf.tv1.query` / `gftd.dodaf.av2.get` / `gftd.dodaf.rules.context`.

| Subcommand | 動作 |
|---|---|
| `gftd dodaf init` | Initialize Parquet files with platform seed data (TV-1, AV-2, OV-5) |
| `gftd dodaf tv1 query --tags <t1,t2> --path <file> --severity <s>` | Query TV-1 technical standards/constraints |
| `gftd dodaf av2 get <term>` | Look up AV-2 integrated dictionary entry |
| `gftd dodaf rules context --path <file> --tags <t1,t2>` | All-views context query (TV-1 + AV-2 + OV-5) |
| `gftd dodaf add --view tv1 --id <id> --title <t> --rule <r>` | Add new entry to a DoDAF view |
| `gftd dodaf validate` | Scan CLAUDE.md files for ## CRITICAL: sections not in TV-1 registry |
| `gftd dodaf seed` | Push registry to kagami (enables MCP `gftd.dodaf.*` tools) |

**DoDAF view → Parquet mapping**:

| Parquet | DoDAF View | 用途 |
|---|---|---|
| `tv1_standards.parquet` | TV-1 Technical Standards | constraints, rules, prohibited/permitted patterns |
| `av2_dictionary.parquet` | AV-2 Integrated Dictionary | lexicon, term definitions, aliases |
| `ov5_activities.parquet` | OV-5 Operational Activity | permitted/prohibited actions with reason + alternative |

→ CLAUDE.md constraints は `gftd dodaf tv1 query` / MCP `gftd.dodaf.tv1.query` で取得。CLAUDE.md はポインタのみ。

#### gftd shannon

`gftd shannon` — Shannon 情報理論に基づく 4 層構造分析。冗長度スコアリング + DSM + BayesNet + 情報ボトルネック + エントロピー最小化。

**統一原理**: DSM で依存構造を表現し、Bayes で不確実性を伝播させ、POMDP で観測と制御を最適化する。

**Subcommands**:

| Subcommand | 動作 |
|---|---|
| `gftd shannon scan` | 全 9 検査実行 → レポート (--json, --top N) |
| `gftd shannon violations` | 冗長性違反の一覧のみ (--json) |
| `gftd shannon dsm` | DSM 依存構造行列 (N×N adjacency + Cuthill-McKee 帯域最小化 + 循環検出) |
| `gftd shannon bayesnet` | ベイズ変更伝搬ネットワーク (条件付き確率 + 高リスクパス探索) |
| `gftd shannon bottleneck` | 情報ボトルネック検出 (fan-in × fan-out + 相互情報量 MI) |
| `gftd shannon minimize` | エントロピー最小化提案 (merge/split/move) |

**9 Redundancy Checks (scan/violations, 加重平均)**:

| Check | Weight | 測定対象 |
|---|---|---|
| `claude_md_duplication` | 25% | CLAUDE.md 間の行レベル重複 (SHA-256 hash 比較) |
| `code_clone_cross` | 15% | Go/TS cross-project 関数 body hash 重複 |
| `collection_write_fan` | 15% | 同一 collection への multi-app write |
| `wit_type_duplication` | 10% | WIT record/enum 型の重複定義 |
| `config_redundancy` | 10% | wrangler.jsonc vars の同一 key=value が 3+ files |
| `dead_code_entropy` | 10% | entropy=0 コード (empty/stub/TODO-only funcs, Go/Rust/TS) |
| `doc_code_drift` | 10% | CLAUDE.md evidence link の stale 検出 |
| `stale_symbol_entropy` | 10% | stale WIT binding + CLAUDE.md strikethrough |
| `rust_duplication` | 5% | Rust 関数 body hash 重複 |

**DSM** (`gftd shannon dsm`): N×N 依存構造行列。Reverse Cuthill-McKee 帯域最小化。DFS 循環検出。Connected components クラスタリング。`score = 100 × (1 - bandwidth/N)`。Flags: `--json`, `--top N`, `--no-reorder`。

**BayesNet** (`gftd shannon bayesnet`): Edge type 別結合強度 (invoke=0.8, writes=0.5, subscribe=0.4, reads=0.3, follow=0.1)。`container/heap` Dijkstra で最大確率パス探索。Flags: `--json`, `--top N`, `--max-depth D`。

**Bottleneck** (`gftd shannon bottleneck`): `bottleneck_score = sqrt(fan_in × fan_out) / max_fan`。MI ≈ H(in) + H(out) - H(in,out)。Severity: critical (≥0.7, fan≥5) / high / medium / low。Flags: `--json`, `--top N`, `--min-fan M`。

**Minimize** (`gftd shannon minimize`): Per-app coupling/cohesion entropy 分解。3 種提案: merge (同 project 相互結合), split (高エントロピー module の重み付き分割), move (70%+ cross-project edges)。Flags: `--json`, `--top N`, `--threshold T`。

**共通 Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--json` | `false` | JSON output |
| `--top` | `15` | hotspot / proposal 表示件数 |
| `--workspace-dir` | git root | workspace root override |

#### gftd mokuteki (目的関数 Shannon 最適評価)

`gftd mokuteki` — 目的関数 (Global Well-Becoming Generative Society) に基づく 4 層 Shannon 最適評価。Kyu/Dan rank 出力。

**4-Layer Framework**:

| Layer | Weight | 名前 | 内容 |
|---|---|---|---|
| **A** | 30% | 構造 | DSM bandwidth, graph connectivity, Shannon redundancy, hypergraph coupling, type system |
| **B** | 25% | 不確実性 | BayesNet propagation, causal DAG acyclicity, information bottleneck, state-space diversity |
| **C** | 20% | 制御 | POMDP observation, constraint optimization, MPC lookahead, bandit sensing |
| **D** | 25% | 実装 | Event sourcing (Design E), immutable log (AT Protocol), policy as code, typed schema (WIT), attestation (DID+profile) |

**Well-Becoming 5 軸 (Layer cross-map)**:

| 軸 | Weight | Source |
|---|---|---|
| Engagement (参与) | 25% | Layer A×0.5 + Layer D×0.5 |
| Competence (能力) | 25% | Layer A×0.6 + Layer B×0.4 |
| Contribution (貢献) | 20% | Layer B×0.4 + Layer C×0.6 |
| Growth (成長) | 20% | Layer C×0.5 + Layer A×0.5 |
| Resilience (回復) | 10% | Layer B×0.5 + Layer D×0.5 |

**Rank Ladder**: Kyu 6 (0) → Kyu 1 (1500) → Dan 1 (2000) → Dan 10 (12000)。max 12000 pts。

**Subcommands**:

| Subcommand | 動作 |
|---|---|
| `gftd mokuteki` | 4 層評価 → terminal text (--json 可) |
| `gftd mokuteki kashika` | HTML dashboard (ブラウザ自動オープン)。DSM 行列クリック展開。`--format terminal/svg/dot/json` |
| `gftd mokuteki store` | 評価 → Parquet 保存 (ZSTD、Iceberg append-only catalog) |
| `gftd mokuteki query [SQL]` | RisingWave で Parquet 履歴クエリ。`$TABLE` = snapshots glob |
| `gftd mokuteki history` | Iceberg snapshot 一覧 |

**Data Store**: `data/mokuteki/` — Iceberg-like ローカルストア

| Path | 内容 |
|---|---|
| `data/mokuteki/catalog.json` | Iceberg catalog (format_version=1, schema, snapshots[]) |
| `data/mokuteki/snapshots/*.parquet` | Per-evaluation Parquet (ZSTD, 33 columns flat) |

**33 Parquet columns**: `evaluated_at`, `total_score`, `rank_name`, `total_apps`, `layer_a/b/c/d_score`, `engagement/competence/contribution/growth/resilience`, `dsm_bandwidth`, `graph_connectivity`, `shannon_redundancy`, `hypergraph_coupling`, `type_system`, `bayesnet_propagation`, `causal_dag`, `info_bottleneck`, `state_space_diversity`, `pomdp_observation`, `constraint_opt`, `mpc_lookahead`, `bandit_sensing`, `event_sourcing`, `immutable_log`, `policy_as_code`, `typed_schema`, `attestation`

**Query examples**:
```bash
gftd mokuteki query                              # default: 4 Layer + 5 軸 latest 20
gftd mokuteki query 'SELECT * FROM $TABLE WHERE total_score > 8000'
gftd mokuteki query 'SELECT evaluated_at, dsm_bandwidth, bayesnet_propagation FROM $TABLE'
```

**Dependencies**: RisingWave FE (MySQL :9030) via Hyperdrive

#### gftd actors shinka (Agentic Domain Knowledge)

`gftd actors shinka` — LLM (Ollama or Murakumo) で Actor のドメイン知識・サブ DID・ナレッジグラフを agentic に生成。

**LLM Backend**: Ollama (default) or Murakumo OpenAI-compatible API (`--murakumo` flag)

**Flow**: PDS `ai.gftd.actor.list` → for each Actor: LLM generate → PDS write (actor.update + actor.create × N sub-DIDs + createRecord × N knowledge edges)

| Flag | Default | 説明 |
|---|---|---|
| `--pds` | `https://atproto.etzhayyim.com` | PDS base URL |
| `--ollama` | `http://127.0.0.1:11434` | Ollama API base |
| `--murakumo` | `false` | Murakumo OpenAI-compatible API を使用 |
| `--murakumo-url` | `https://murakumo.etzhayyim.com` | Murakumo API base URL |
| `--model` | `gemma3:4b` | LLM model (`GFTD_SHINKA_MODEL` env) |
| `--concurrency` | `4` | 並列 actor 処理数 |
| `--limit` | `50` | 処理 actor 数上限 |
| `--filter` | `""` | nanoid/projectId substring filter |
| `--dry-run` | `false` | LLM 生成のみ、PDS 書込なし |
| `--json` | `false` | JSON output |

**Output per actor** (LLM generated):
- `domain_summary` — 2-3 文のドメイン説明 → `ai.gftd.actor.update` (description)
- `sub_dids` — 3-8 sub-entities → `ai.gftd.actor.create` (path-based DID)
- `knowledge_edges` — 5-15 relationships (EXPERTISE_IN/DEPENDS_ON/PRODUCES/CONSUMES/REGULATES/SERVES) → `com.atproto.repo.createRecord` (knowledgeEdge)

#### gftd cohort (ADR-0026 Agent-Only Reverse Identity Topology)

`gftd cohort` — cohort generative actor lifecycle CLI (Phase A genesis / Phase B evidence / Phase C fission)。`70-tools/gftd/gftd/cohort.go`。

| Subcommand | 動作 |
|---|---|
| `gftd cohort seed` | POST `ai.gftd.cohort.seed` — 単一 segment から cohort 生成 (idempotent by segment_hash) |
| `gftd cohort gen` | typed flags (`--pcfL1 --role --industry --seniority --locale -k 50`) から JSON-LD を組立て seed |
| `gftd cohort bootstrap` | `deps.toml [[cohort_actors]]` を全件 POST (`--dry-run` default) |
| `gftd cohort list` | `ai.gftd.cohort.listCohorts` 経由で actor 列挙 (`--kind --pcfL1 --locale --derived-from --did`) |
| `gftd cohort evidence` | `ai.gftd.cohort.listEvidence` 経由で evidence 列挙 (`--cohort --min-posterior --judge`) |
| `gftd cohort fission` | POST `ai.gftd.cohort.fission` — Phase C fission (posterior≥0.95 + judge=true gate) |
| `gftd cohort lineage` | `derived_from` chain を upward 探索 (`--did --depth N`) |
| `gftd cohort forest` | cohort + 子孫 ascii tree (`--pcfL1 --rooted <did>`) |
| `gftd cohort stats` | client-side aggregate (`--by pcfL1,role,industry,seniority,locale --kind cohort\|fissioned`) |
| `gftd cohort coverage` | 2D matrix (`--axes row,col`) で空 cell 可視化 |
| `gftd cohort gap` | matrix の count<N cell を列挙 |
| `gftd cohort snapshot` | 4-axis aggregate を `data/cohort-coverage/<ts>.json` に保存 |
| `gftd cohort diff` | 2 snapshot 間の axis 別 delta (`--json`) |
| `gftd cohort drift` | snapshot dir 内の最古/最新を auto-pick して diff (`--window <days>`) |
| `gftd cohort emit` | POST `ai.gftd.cohort.emitEvidence` — vertex_repo_record + edge_cohort_evidence_about を直接 INSERT (Phase B) |
| `gftd cohort lineage-stats` | `ai.gftd.cohort.lineageStats` 経由で `mv_cohort_lineage_depth` を rank 表示 (`--pcfL1 --min-children`) |
| `gftd cohort repair-edge` | POST `ai.gftd.cohort.repairEdge` — `vertex_cohort_actor.derived_from` から `edge_cohort_derived` を backfill (`--did --limit --dry-run`) |
| `gftd cohort dashboard` | 1 行 health check — total / cohort / fissioned / fissionEnabled rate / 4 axis cardinality / ADR-0028 phase trigger |

**Auth**: 通常 `gftd authn signin` + `GFTD_TOKEN` 経由。programmatic agents は `gftd agent-token --lxm ai.gftd.cohort.seed` で 60s scoped JWT を mint。

**設計**: `90-docs/adr/0026-agent-only-reverse-identity-topology.md` + `90-docs/260414-cohort-coverage-evaluation-baseline.md` (running iteration log)。

#### gftd murakumo fleet (Fleet Management)

`gftd murakumo fleet` — Nomad-backed Mac Mini fleet の管理。sh スクリプト (`deploy-fleet.sh`, `setup-nomad-fleet.sh`) は廃止、Go CLI に統合。

| Subcommand | 動作 |
|---|---|
| `deploy` | daemon.py を全ノードに scp + venv確認 + Nomad rolling restart |
| `versions` | CoordinatorDO から per-worker daemon_version 一覧を表示 |
| `jotai` / `status` | Fleet status (XRPC + Nomad combined) |
| `nodes` | Nomad node status |
| `drain` | ノード graceful drain |
| `undrain` | Drained ノード再有効化 |
| `restart` | Rolling restart of inference job |
| `logs` | Allocation logs for a node |
| `watch` | Continuous fleet monitoring |

**`gftd murakumo fleet deploy` flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--nodes` | all | comma-separated node names |
| `--skip-restart` | `false` | Nomad rolling restart をスキップ |
| `--dry-run` | `false` | 実行内容の事前確認 |
| `--concurrency` | `4` | 並列 SSH 数 |

**Deploy flow**: scp daemon.py → mkdir + cp → venv確認 → pip install deps → Nomad `job run` (DEPLOY_VERSION 更新で rolling restart)

**Daemon version tracking**: daemon.py `VERSION` → heartbeat `daemon_version` → CoordinatorDO → `gftd murakumo fleet versions` で確認

**Daemon path**: `/usr/local/share/murakumo/daemon.py` (Nomad HCL + deploy 統一)

#### gftd performance-test

#### gftd kaizen (Domain Coverage)

`gftd kaizen` — Domain coverage analysis。全 app の domain 実装品質を 9 軸で評価。

**Subcommands / Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--json` | `false` | JSON output |
| `--apps` | `false` | per-app details 表示 |
| `--grade` | `""` | filter by grade (S/A/B/C/D) |
| `--limit` | `0` | limit output apps |
| `--fix` | `false` | gftd code exec で kaizen agent 実行 (worktree 禁止) |

**9-axis Domain Scoring (0-100, S≥70)**:

| Axis | Max | Measurement |
|---|---|---|
| Graph labels | 30 | `MATCH (n:DomainLabel)` — generic Record 以外 |
| Collection kinds | 20 | `ai.gftd.apps.X.specific_kind` — generic record 以外 |
| Custom commands | 15 | テンプレ CRUD 以外の domain 固有 command |
| Business rules | 15 | if/switch/transform 分岐数 |
| Data structures | 10 | interface/const array/Map 定義 |
| Governance | 5 | template governance と異なる domain-specific RACI |
| Data sources | 5 | RSS/API URL (外部データ取得) |
| DID paths | 5 | `comAtprotoIdentityCreate("path")` |
| Writer entity | 3 | WriterEntity pattern |

**`gftd code-quality` にも `domain_coverage` check として統合済み。**

#### gftd performance-test

`gftd performance-test` — PDS XRPC エンドポイントのパフォーマンス計測。latency (p50/p95/p99)、RPS、grade (S/A/B/C/D/F) を出力。

**Subcommands**:

| Subcommand | 動作 |
|---|---|
| `gftd performance-test run` | 全 14 エンドポイントに並行リクエスト → 計測レポート (default) |
| `gftd performance-test report` | 保存済み JSON レポートの表示 |

**Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--target` | `https://atproto.etzhayyim.com` | PDS base URL |
| `--concurrency` | `5` | 並行リクエスト数/エンドポイント |
| `--duration` | `10` | テスト時間 (秒/エンドポイント) |
| `--endpoints` | all | カンマ区切りフィルタ (名前 or カテゴリ) |
| `--json` | `false` | JSON output |
| `--save` | `""` | レポート保存先 |
| `--warm-up` | `2` | 計測前ウォームアップ数 |
| `--timeout` | `30` | リクエストタイムアウト (秒) |

**Grade**: S (<20ms) / A (<50ms) / B (<200ms) / C (<500ms) / D (<2s) / F (>2s or errors)

**Endpoints** (14): GetTimeline, GetDiscoverFeed, GetAuthorFeed, GetPostThread, SearchPosts, GetProfile, SearchActors, GetSuggestions, GetFollowers, GetFollows, ListNotifications, GetUnreadCount, ListRecords, Health

#### gftd process-mining

`gftd process-mining` — PDS XRPC handler の静的解析 + パフォーマンスボトルネック検出。handler TS ファイルを解析し、unfiltered scan / uncached query / N+1 / sequential waterfall を自動検出。

**Subcommands**:

| Subcommand | 動作 |
|---|---|
| `gftd process-mining scan` | 全 4 handler ファイル解析 → レポート (default) |
| `gftd process-mining bottlenecks` | critical/high ボトルネックのみ抽出 |
| `gftd process-mining flow <method>` | 特定ハンドラのリクエストフロー図表示 |

**Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `--workspace-dir` | git root | workspace root |
| `--json` | `false` | JSON output |
| `--severity` | all (`bottlenecks`: critical,high) | severity フィルタ |
| `--handler` | all | handler フィルタ (feed,repo,infra,gftd) |

**検出パターン**:

| Type | Severity | 説明 |
|---|---|---|
| `unfiltered_scan` | critical | buildLabelSql に WHERE フィルタなし — 全ノードスキャン |
| `uncached_query` | medium | aiGftdYataSql instead of aiGftdYataSqlCached — 毎リクエスト kagami hit |
| `n_plus_1` | critical | for ループ内 await — N 回 sequential SQL |
| `sequential_waterfall` | high | Promise.all なしの複数クエリ |
| `unfiltered_sql` | high | WHERE 句なし MATCH |

#### gftd haisen (配線図)

`gftd haisen` — App 間配線図。magatama.jsonld + source-graph AST から Invoke/Write/Read/Subscribe edges を抽出。

| Subcommand | 動作 |
|---|---|
| `gftd haisen scan` | 全 app スキャン → JSON graph (apps, edges, stats) + PCB layout 座標 (`--layout`, default on) |
| `gftd haisen edges` | edge 一覧 (--type, --from, --to filter) |
| `gftd haisen orphans` | 配線なし孤立 app 一覧 |
| `gftd haisen coupling` | collection-mediated coupling (N apps が同一 collection を共有) |

**Edge types**: invoke (cross-actor), writes (collection write), reads (SQL), subscribe (ComAtprotoSyncSubscribeRepos), follow

#### gftd kashika (可視化)

`gftd kashika` — haisen/SoS JSON を複数形式に変換。

| Subcommand | 出力形式 |
|---|---|
| `gftd kashika terminal` | ANSI terminal table |
| `gftd kashika dot` | Graphviz DOT |
| `gftd kashika mermaid` | Mermaid diagram |
| `gftd kashika html` | HTML (kami-web WASM WebGPU rendering) |

**Input**: `--source haisen` (default) or `--source sos`。stdin pipe 対応。

#### gftd systemofsystem (SoS 俯瞰)

`gftd systemofsystem` — System-of-Systems (DoDAF SV-1)。haisen + infra topology + deploy-state を統合。

| Subcommand | 動作 |
|---|---|
| `gftd systemofsystem scan` | JSON sosReport (systems, interfaces, layers, stats) |
| `gftd systemofsystem layers` | 4-Layer summary (edge/infra/dispatch/data) |
| `gftd systemofsystem interfaces` | System 間 interface 一覧 |
| `gftd systemofsystem health` | coupling/cohesion score + verdict |

**4-Layer model**: edge (dispatcher) → infra (pds, kagami, yoro, repo, murakumo, maps) → app (account-level Workers) → data (B2)

#### gftd deps scoring (CRITICAL)

`gftd deps score` は remote (`deps.etzhayyim.com`) から取得。`gftd deps export` は local graph を生成し local scoring を実行する。

- `gftd deps export --project-dir 60-apps/ai-gftd-project-deps/wasm/wit-deps-visualizer/svelte` — graph 生成 + local scoring
- `--refresh-graph=false` で graph 再生成をスキップし既存 graph で再計算

**scoring 注意点**:
- `contract_score` / `capability_export_score` は **component 数** ベース (import/export 行数ではない)
- `gftd:*` import は `deps_link_score` の分母に入る。不要な `gftd:*` import は score を悪化させる
- `magatama:*` import は `deps_link_score` 対象外
- `resource_flow_score` は `gov-resource-flow/` or `resource-flow/` substring match (prefix 不問)
- `shannon_score` (5% weight) = `import_entropy` (60%) + `duplicate_import` (40%)。WIT import の情報理論的冗長性を測定

#### gftd agent-token (Scoped Service-Auth JWT for Programmatic Agents)

`gftd agent-token` — mint a short-lived, NSID-scoped service-auth JWT for programmatic agents (Claude Code sessions, CI jobs, scripts). Wraps the standard `com.atproto.server.getServiceAuth` endpoint so the caller never touches signing keys.

**Design rationale**: Claude Code sessions are stateless (no session memory across messages) and run commands via shell. Long-lived bearer tokens in env vars are risky; DPoP / OAuth refresh flows are awkward in bash. The cleanest fit is atproto's built-in **Service Auth with `lxm` claim**:

- Caller authenticates once via `gftd authn signin` or a long-lived API key (`sk_live_*`)
- Per command, Claude mints a **60s, single-NSID JWT** via `getServiceAuth`
- Resulting JWT has `iss` = caller DID, `lxm` = exactly one NSID → audit trail + blast radius bounded
- PDS enforces scope on the receiving side via existing Permission-Set machinery (no new graph schema)

**Flow**:

```bash
gftd authn signin                                    # once, human
export GFTD_TOKEN=$(gftd authz create-api-key --name "claude-jun" -q)   # once, store

# Per command (stateless):
AT_TOKEN=$(gftd agent-token \
  --lxm com.atproto.repo.applyWrites \
  --aud did:web:atproto.etzhayyim.com \
  --ttl 60)
curl -H "Authorization: Bearer $AT_TOKEN" https://atproto.etzhayyim.com/xrpc/com.atproto.repo.applyWrites -d '{...}'
```

**Flags**:

| Flag | Default | Description |
|---|---|---|
| `--lxm <nsid>` | (required) | NSID to bind the JWT to. Token is valid for exactly this one method |
| `--aud <did>` | `did:web:<pds-host>` | Audience DID. Derived from `--pds` host when omitted |
| `--pds <url>` | `$GFTD_PDS_URL` or `https://atproto.etzhayyim.com` | PDS base URL |
| `--ttl <sec>` | `60` | Token lifetime in seconds. Clamped to [1, 3600] by PDS |
| `--sub <did>` | `""` | Informational subject repo DID (currently ignored by PDS; useful for logging) |
| `-v` | `false` | Print target URL + HTTP status to stderr |

**Source**: `70-tools/gftd/gftd/agent_token.go`

#### gftd agent organism status

`gftd agent organism status` — local artificial organism / active inference loop の標準 status entrypoint。直接 `magatama-agent-status` を叩かず、通常はこのコマンドから health / viability / process / knowledge graph fitness を確認する。

```bash
gftd agent organism status
gftd agent organism status --json
gftd agent organism status --json | jq '.healthEvaluation'
gftd agent organism status --web
gftd agent organism publish --no-dry-run --submit-chain
```

Public verification surface:

```bash
curl -sSfL https://organism.etzhayyim.com/api/status | jq '.status, .checks'
```

`organism.etzhayyim.com` は Cloudflare Worker `50-infra/cloudflare/workers/organism-status`。localhost / RisingWave credentials / 1Password / Safe keys / write endpoints は公開せず、public IPFS、`https://geth.etzhayyim.com` の read-only `eth_call`、graph Worker service binding 経由の RisingWave live projection だけで ERC-8004、ActorRuntimeRegistry artifact/receipt、RW projection を確認する。5分ごとの Cloudflare Cron が same check を実行し、ログに monitor event を出す。

`gftd agent organism publish` は registration render → IPFS publish → optional Safe `setAgentURI` → proof update の標準 entrypoint。実 chain 更新は `--no-dry-run --submit-chain` が必要。

**Flags**:

| Flag | Default | Description |
|---|---|---|
| `--agent-did <did>` | `did:web:kami-agent.etzhayyim.com` | 評価対象 agent DID |
| `--json` | `false` | `magatama-agent-status --json` を passthrough し、機械判定用 JSON を出す |
| `--web` | `false` | `http://127.0.0.1:8765` の status WebUI を確認し、未起動なら foreground で起動 |
| `--url <url>` | `http://127.0.0.1:8765` | `--web` で確認・起動する WebUI base URL |
| `--open` | `false` | `--web` と併用して browser を開く |

**Runtime path**: repo root の `20-actors/magatama/py/.venv/bin/magatama-agent-status` / `magatama-agent-status-web` を優先し、なければ PATH、最後に Python module fallback を使う。`AGENT_DAEMON_ENV_FILE` 未指定時は `ops/local-agent/agent-daemon.env` を読む。

**Source**: `70-tools/gftd/gftd/agent.go`

**Why this is the right design for Claude agents specifically**:

| Property | Fit for Claude |
|---|---|
| **Stateless** | ✓ Every call re-mints from `~/.gftd/auth.json` or `GFTD_TOKEN` — no session state in conversation |
| **Bash-friendly** | ✓ `AT_TOKEN=$(gftd agent-token ...)` — no DPoP signing dance per request |
| **Secret isolation** | ✓ Private signing material stays in `~/.gftd/auth.json` or CF Secret Store, never appears in Claude's context window |
| **Scope bounded** | ✓ Single `lxm` per JWT — a runaway agent can only call one method with one token |
| **Audit trail** | ✓ `iss` on every commit identifies which agent wrote; `gftd authz list-api-keys` shows per-key usage |
| **Revocable** | ✓ `gftd authz revoke-api-key <id>` cuts off the agent mid-session without restarting Claude |

**Alternatives considered (and rejected)**:

| Option | Why not |
|---|---|
| Reuse session bearer token directly | No `lxm` scoping — full repo write access per request |
| App Password | Deprecated, no scope, not revocable per-action |
| OAuth 2.0 + DPoP | Per-request DPoP proof requires ES256 signing in bash per call; refresh token management in stateless Claude context is painful |
| Dedicated agent DID with local signing key | Overkill — `getServiceAuth` already handles the signing on the PDS, and the API key provides the root of trust |

#### gftd xrpc (Claude Agent XRPC Invocation)

`gftd xrpc` — invoke any XRPC endpoint on a deployed App or PDS. Designed for use by **Claude Code chat agents** to trigger commands without a browser.

**Auth**: `setAuthHeaders()` — Bearer token (`GFTD_TOKEN` env or `~/.gftd/auth.json`) + `X-Active-DID` header. Use `gftd authn signin` first.

**CRITICAL for Claude agents**: `gftd xrpc` currently sends the base session token on every call. For Claude Code sessions and other programmatic agents, **prefer minting a scoped Service Auth JWT first** via `gftd agent-token --lxm <nsid>` and piping it through `GFTD_TOKEN` for the duration of that one call. This bounds the blast radius to a single NSID and keeps the audit trail intact (see §`gftd agent-token` + root-claude-agent-scoped-auth critical rule in `deps.toml`).

```bash
AT_TOKEN=$(gftd agent-token --lxm ai.gftd.apps.media_gamers.graph.publishBatch --ttl 60) \
  GFTD_TOKEN=$AT_TOKEN gftd xrpc ai.gftd.apps.media_gamers.graph.publishBatch \
  -d '{"vertices":[...],"edges":[...]}' --app a7m8oocs
```

**Source**: `70-tools/gftd/gftd/xrpc.go`

**Flags**:

| Flag | Default | 説明 |
|---|---|---|
| `<nsid>` | (required) | AT Protocol NSID of the command/query to invoke |
| `-d <json>` | `""` | JSON body for POST requests (omit for GET) |
| `--app <nanoid>` | `""` | Route to `https://{nanoid}.etzhayyim.com/xrpc/{nsid}` |
| `--url <base>` | `""` | Override base URL entirely |
| `-X GET\|POST` | inferred | HTTP method (POST if `-d` given, else GET) |
| `--json` | `false` | Pretty-print JSON response |
| `-v` | `false` | Verbose: print URL + status to stderr |

**NSID auto-routing**: If neither `--app` nor `--url` is given, the NSID `ai.gftd.apps.{slug}.*` is matched against a built-in nanoid map. Known slugs: `media_gamers→a7m8oocs`. Falls back to PDS (`https://atproto.etzhayyim.com`) if no match.

**Examples**:

```bash
# Seed media-gamers entities (step by step)
gftd xrpc ai.gftd.apps.media_gamers.catalog.seedAll -d '{"step":"platforms"}' --app a7m8oocs
gftd xrpc ai.gftd.apps.media_gamers.catalog.seedAll -d '{"step":"developers"}' --app a7m8oocs
gftd xrpc ai.gftd.apps.media_gamers.catalog.seedAll -d '{"step":"publishers"}' --app a7m8oocs
gftd xrpc ai.gftd.apps.media_gamers.catalog.seedAll -d '{"step":"franchises"}' --app a7m8oocs

# Seed games in batches of 10
gftd xrpc ai.gftd.apps.media_gamers.catalog.seedGames -d '{"offset":0,"limit":10}' --app a7m8oocs

# Generate guides for a game
gftd xrpc ai.gftd.apps.media_gamers.catalog.generateAll -d '{"slug":"elden-ring"}' --app a7m8oocs

# Query (GET) with pretty JSON output
gftd xrpc ai.gftd.apps.media_gamers.catalog.getGame --app a7m8oocs --json

# PDS describe (no --app needed)
gftd xrpc com.atproto.server.describeServer --json
```

**Extending `knownApps`**: Add slug→nanoid entries to `knownApps` map in `xrpc.go` when new apps are registered.

#### gftd build / deploy flags

| Flag | build | deploy | 説明 |
|---|---|---|---|
| `-no-check` | yes | yes | svelte-check type validation をスキップ。missing module error を回避 |
| `-no-svelte` | yes | yes | svelte/pnpm build を完全スキップ (appview apps 標準) |
| `-dir` | yes | yes | component source directory (default: `.`) |

**Assets**: `svelte/` ディレクトリがある appview app は Vite build → `svelte/build/` を Workers Assets として配信。`svelte/build/` が存在しない場合は空ディレクトリを自動作成。**例外**: `uiType: "yoro"` は assets block を生成しない (zero UI)。

**TS Native (唯一のフレームワーク)**: `gftd deploy` は `src/app.ts` を wrangler entrypoint (`"main": "src/app.ts"`) として直接使用。ソースツリーから直接 deploy (staging なし)。app.ts が `export default createWorkerExport()` で CF Worker fetch handler を直接 export。全ルーティング (`/_commit`, `/_heartbeat`, `/_app/meta`, `?embed=1`, `/health`, XRPC) は `@gftd/magatama-host-sdk` の `handleRequest()` に集約。wrangler.jsonc はコンポーネントルートに `buildWranglerJSON()` で生成

**Deploy validation (自動チェック)**:
- `svelte/build/index.html` 不存在 → **build error** (`vite.config.ts` の `outDir` が `build` でない)
- `svelte/dist/index.html` 存在 + `svelte/build/` 不存在 → **build error** (outDir 修正を要求)
- `svelte/build/assets/` に `.css` ファイルなし → **warning** (Tailwind 未処理)

#### CRITICAL: Svelte Appview 必須チェックリスト

| 項目 | 必須値 | 誤り例 | 検出 |
|---|---|---|---|
| `vite.config.ts` `outDir` | `'build'` | `'dist'` | build error |
| `src/app.css` | `@tailwind base/components/utilities` | ファイルなし | warning (CSS 0 件) |
| `src/main.ts` | `import './app.css'` | CSS import なし | 白画面 |
| `sdk.app.command()` 第1引数 | NSID フルパス `ai.gftd.apps.{app}.{method}` | `""` + short name | XRPC_UNKNOWN_METHOD |
| `embed` route | `/assets/{hash}.js` (build output) | `/src/main.ts` (dev-only) | embed 白画面 |
| コンポーネント `package.json` | `@gftd/magatama-host-sdk: workspace:*` | なし | import 解決失敗 |
| deploy target | account-level Worker | — | — |

#### Profile registration + deploy announce (CRITICAL)

`gftd deploy` post-deploy で `registerProfileToYata()` が XRPC `com.atproto.admin.registerApp` (AT Protocol JWT 認証) 経由で yata に SQL MERGE を実行。legacy app 互換ラベルと `:Profile {did}` (display_name, description, nanoid, sensitivity) の 2 ノード (PascalCase — SQL 標準)。`-no-smoke` でもスキップしない。**Deploy announce**: profile 登録後に `postDeployAnnounce()` が app の `/_heartbeat` を POST → identity/capability 自動登録 + social evolution post (app 自身の DID で deploy 通知を自動投稿)。

**Version lineage**: `magatama.jsonld` に `version`, `template`, `source` を記録。deploy 時に Worker vars (`APP_VERSION`, `APP_TEMPLATE`, `APP_SOURCE`, `APP_DEPLOY_SHA`, `APP_DEPLOY_AT`) として注入 → runtime `/_app/meta` endpoint で取得可能。

**Evolution sync**: `--sync-evolution` で repo.etzhayyim.com の `/_internal/evolution/{nanoid}/meta.json` を確認し、進化済み app の main.go を取得 → monorepo に反映 → build + deploy。repo.etzhayyim.com は Internal token 認証が必要 (`MAGATAMA_INTERNAL_TOKEN` 環境変数)。

**Process group cleanup (CRITICAL)**: `gftd` が起動する全子プロセス (pnpm, esbuild, wrangler/workerd) は `SysProcAttr{Setpgid: true}` で own process group に配置される。gftd が SIGINT/SIGTERM で終了する際、全追跡中の child process group を `kill(-pgid, SIGKILL)` で確実に殺す。これにより gftd OOM kill 時の workerd orphan プロセス蓄積を防止する。実装: `procgroup.go` (`setProcGroup`, `trackChild`, `untrackChild`, `killAllChildren`)。大規模 workspace (864 projects) での `pnpm install` + `esbuild bundle` は `NODE_OPTIONS="--max-old-space-size=8192"` を推奨。

## Structured Data Policy

App の data access は **Design E 3-Tier Write** を標準とする (root CLAUDE.md L213 参照)。Social = `AppBskyFeedPost()` (public AT Record, federable)。Domain = `ComAtprotoRepoCreateRecord(kind, data)` (internal, non-federable) → PDS → graph SQL write path → RisingWave。State = `Preferences()` (server-side)。Read = `G()` (Kysely/graph SQL → RisingWave)。

| Layer | 標準 |
|---|---|
| **Social data (Tier 1)** | `AppBskyFeedPost()` → AT Record (public, Repo MST, federable, firehose)。post/like/follow/mention |
| **Domain data (Tier 2, DEFAULT)** | `ComAtprotoRepoCreateRecord(kind, data)` → W Protocol internal record (non-AT, non-federable,  PDS → graph SQL path → RisingWave)。Read: `G("kind").Match(Eq{...}).Query()` |
| **State (Tier 3)** | `Preferences()` → server-side state (non-record)。evolution config, heartbeat, user settings |
| **Entity/actor state** | W Protocol Event Stream (per-entity isolation は ComAtprotoRepoCreateRecord の scope で実現) |
| **Analytics / graph traversal** | SQL graph — `magatama.G("Label").Match(Eq{...}).Return("prop").Query()` (squirrel 互換 SQL builder) |
| **Blob / binary payloads** | app/project ごとの blob layer |
| **Read/Write (App)** | `@gftd/magatama-host-sdk` (TS Native, async/await)。Graph: `G()` builder |
| **Read/Write (native Go service)** | Hyperdrive direct 可 (PDS service binding 経由) |

## UI / Backend Separation (CRITICAL)

- Business logic は TS native (`src/app.ts` + `@gftd/magatama-host-sdk`)
- UI Worker は business logic を import しない
- `fullapp` の Svelte front door は business logic を import しない
- UI からの query/write は XRPC (`/xrpc/{NSID}`) 経由に限定する
- SQL access は `G()` builder を `src/app.ts` 内で使う

### Structured Data 標準

- operational data は W Protocol Event Stream (WRecord for writes, G() for reads) が source of truth
- 設計は WRecord kind = table/record type + standard CRUD via G() builder
- `org_id`, `user_id`, `actor_id` は record にも必須 (multi-tenant query)
- App code の access は `@gftd/magatama-host-sdk` (TS Native) に限定 (`G()` SQL builder via W Protocol)。DO SQLite 直接使用禁止
- durable state は WIT `actor-state`, `reminder`, `workflow`, `activity` host interface 経由

### Blob 標準

- binary/blob は app/project 側の storage layer で扱い、runtime command bus と混在させない
- AT record で media/blob を扱う場合は `CIDv1 + blobstore` 参照を正とし、inline `data_b64` payload を新規導入しない

### Quick Start (TS Native)

```typescript
// src/app.ts
import { createWorkerExport, asAgentTool, withCapabilityTags } from "@gftd/magatama-host-sdk";
export default createWorkerExport((sdk) => {
  sdk.app.command("ai.gftd.apps.{app}.myCommand", async (ctx, body) => {
    return JSON.stringify({ ok: true });
  }, asAgentTool("My command"), withCapabilityTags("domain"));
});
```

## App 間通信: W Protocol (AT + Signal over wRPC)

- **W Protocol が標準**: messaging / command / query は `WSend/WCreateChannel/WCreateDM/WListEnvelopes` 等の W Protocol SDK を使用
- control plane = app-owned AT bot DID + PDS (EnsureATService → EnsureATBotUser → EnsureATChannel)
- AT Record は W Protocol host が `kind` → `ai.gftd.w.{kind}` で自動生成。手動 `ATCreateRecord` は W Protocol 対象外の操作にのみ使用
- E2E 暗号化は W Protocol `AutoCrypto` が channel encryption_mode に基づき自動判定。Human=client-side, Bot=server-assisted
- 手動 KV bucket (`yoro-messages` 等) + JSON marshal は禁止。W Protocol host が KV/CAS/AT Record を自動管理
- 権威ソース: `10-protocol/wproto/CLAUDE.md`
