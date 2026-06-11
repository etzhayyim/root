---
id: adr-2604261000-mcp-registry-via-kysely-schema
title: "ADR: MCP Tool Registry as Kysely Schema (replaces gen-tool-manifest.mjs codegen)"
status: proposed
doc_type: adr
topic: mcp-tool-registry-data-driven
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - mcp-tool-registry-storage
  - mcp-tools-list-data-source
  - per-actor-tool-runtime-toggle
related:
  - adr-0042
  - adr-0056-bpmn-as-actor
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0005-shannon-redundancy-prohibition
  - adr-0023-auth-shannon-optimal-4-layer
  - adr-2604231349-timestamp-numbering-policy
supersedes: []
superseded_by: []
amends:
  - adr-0042
---

# Context

ADR-0087 §D3 が `Lexicon → gen-tool-manifest.mjs → tool-manifest.ts (Zod
+ OpenAPI route + MCP tool entries)` の build-time codegen を新設する
としていた。同 ADR の目的は per-actor `/mcp` endpoint の実現で、
そのための **tool 一覧** (`tools/list` 応答 = `{name, description,
inputSchema}[]`) を生成物として bundle に焼き込む設計。

一方、repo には既に **runtime DB-driven actor registry** の前例が 2 つ
ある:

1. **ADR-0056 BPMN-as-actor** — `vertex_bpmn_process_def` +
   `vertex_bpmn_lexicon_binding` に `INSERT 2 rows` で新規 actor を追加。
   F5 watcher が 30s 毎に Zeebe deploy。新規 actor の追加コストは
   row 挿入のみ、Worker rebuild 不要。
2. **migration `20260423050934_vertex_kind_mcp_capability`** —
   `vertex_kind_mcp_binding (kind, mcp_url, description, tools_json,
   tools_fetched_at)` + `vertex_actor_capability` を既に作成済み。
   `tools_json` 列は `tools/list` snapshot の cache 列として設計され、
   kagami-resolver が walk-up lookup で参照。

ADR-0087 の codegen は **同じ tool 集合を 2 箇所** (lexicon JSON SSoT +
生成物 `tool-manifest.ts`) に投影する。Shannon η の観点で:

- ADR-0005 §Shannon 冗長禁止: 「同じ判断 / 同じ事実を複数 SSoT に
  本文として書かない」
- ADR-0056 の `INSERT N rows` 規約と整合しない (MCP 経路だけ codegen)
- runtime での per-tool enable/disable / per-org visibility / canary が
  生成物 bundle redeploy を要する

# Decision

ADR-0087 §D3 の codegen を **Kysely schema** に置換する。
新規 table `vertex_mcp_tool_def` を ADR-0056 と同形の `INSERT N rows`
規約で扱い、host-sdk `/mcp` は Kysely SELECT (60s 内蔵 cache) で
manifest を毎リクエスト構築する。

ADR-0087 §D1 (per-actor `/mcp` endpoint)・§D2 (`/.well-known/openapi.json`)
は維持。§D4 (`kotodama.jsonld.mcpFacade`) は段階的に
`mcpRegistry: { enabled }` flag に置換 (env var
`APP_MCP_REGISTRY=1` も同等)。

## D3' Kysely-backed registry

### Schema

```sql
CREATE TABLE vertex_mcp_tool_def (
  vertex_id        VARCHAR PRIMARY KEY,    -- at://did:web:{host}.etzhayyim.com/com.etzhayyim.mcp.toolDef/{slug}
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT,
  owner_did        VARCHAR,                -- = actor_did

  nsid             VARCHAR NOT NULL,       -- 'com.etzhayyim.apps.lawfirm.createCase'
  actor_did        VARCHAR NOT NULL,       -- 'did:web:lawfirm.etzhayyim.com'
  actor_host       VARCHAR,
  lexicon_type     VARCHAR,                -- 'procedure' | 'query'
  description      VARCHAR,                -- asAgentTool() 文字列
  input_schema     VARCHAR,                -- JSON Schema 2020-12 (string)
  output_schema    VARCHAR,
  lxm_scope        VARCHAR,                -- ADR-0023 strict-match (= nsid)
  visibility       VARCHAR DEFAULT 'public',
  version          INT     DEFAULT 1,
  enabled          BOOLEAN DEFAULT TRUE,
  source_path      VARCHAR,                -- repo-relative lexicon path
  schema_hash      VARCHAR,                -- sha256(desc||in||out)[:16]
  deployed_at      VARCHAR,

  org_id           VARCHAR DEFAULT 'anon',
  user_id          VARCHAR DEFAULT 'anon',
  actor_id         VARCHAR DEFAULT '',
  created_at       VARCHAR
);

CREATE INDEX idx_vertex_mcp_tool_def_nsid          ON vertex_mcp_tool_def(nsid);
CREATE INDEX idx_vertex_mcp_tool_def_actor_did     ON vertex_mcp_tool_def(actor_did);
CREATE INDEX idx_vertex_mcp_tool_def_enabled_actor ON vertex_mcp_tool_def(enabled, actor_did);
```

GraphAr-native conventions (vertex_id PK, RLS 3-col, promoted columns,
no JSON column type — RW lacks JSONB, `input_schema` / `output_schema`
は VARCHAR で JSON 文字列保持) を遵守。

Migration: `30-graph/graph-schema/migrations/20260425100000_vertex_mcp_tool_def.ts`。

### Sync pipeline

```
00-contracts/lexicons/com/etzhayyim/apps/**/*.json  (SSoT)
        │
        ▼  70-tools/scripts/contract/sync-mcp-registry.py
        │  (--apply / --strict / --only-drift)
        │
vertex_mcp_tool_def                            (runtime registry)
```

`sync-mcp-registry.py` は ADR-0056 の `sync-bpmn-actors.py` と同形:

- walk lexicons under `00-contracts/lexicons/com/etzhayyim/apps/**/*.json`
- procedure / query 以外は skip
- `vertex_id` 規約 = `at://did:web:{actor}.etzhayyim.com/com.etzhayyim.mcp.toolDef/{nsid.replace('.','-')}`
- `actor_did` = `did:web:{actor}.etzhayyim.com` (NSID 第 4 segment から導出)
- `schema_hash` で drift 検出 → INSERT or UPDATE
- DELETE 操作なし (`enabled=false` で論理削除、手動 / 別 ADR で物理削除)

### Runtime read (host-sdk)

`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/mcp-registry-loader.ts`:

```typescript
const rows = await db
  .selectFrom("vertex_mcp_tool_def")
  .select(["nsid", "description", "input_schema"])
  .where("actor_did", "=", actorDid)
  .where(eb => eb.or([eb("enabled", "is", null), eb("enabled", "=", true)]))
  .execute();

return {
  appName,
  mcpTools: rows.map(r => ({
    name: r.nsid,
    description: r.description ?? "",
    inputSchema: JSON.parse(r.input_schema ?? "{}"),
  })),
  knownNsids: new Set(rows.map(r => r.nsid)),
};
```

60s in-memory cache per `actor_did` (ADR-0023 graph authority cache と
同パターン)、concurrent request は in-flight promise を共有。

`tools/call` は既存 `app.handleXRPC(nsid, args)` に delegate。
runtime 入力 validation は handler 側の
`parseLexiconInput(nsid, body)` (生成 `LEXICON_INPUT_SCHEMA` 経由) が
担う。MCP 境界では追加 validator を導入しない (AJV 不要、bundle 増加なし)。

### Opt-in / migration

`createWorkerExport(setup, { mcpRegistry: {} })` で actor 単位で opt-in。
env var `APP_MCP_REGISTRY=1` でも有効化 (`etzhayyim deploy` が actor
migration 完了時に注入)。`mcpFacade` (codegen) と併用された場合は
**registry が勝ち**、OpenAPI 3.0 のみ codegen 経路を残す
(OpenAPI codegen の registry 化は本 ADR 範囲外、別 ADR)。

# Comparison (Shannon η)

| 軸 | w | A. ADR-0087 codegen | **B. Kysely registry (採用)** |
|---|---:|---:|---:|
| Tool registry SSoT 数 (ADR-0005) | 0.20 | 0.50 (lexicon + 生成物) | **0.95** (lexicon + DB row、生成物無) |
| 新規 tool 追加コスト | 0.15 | 0.55 (lexicon → CI build → deploy) | **0.95** (lexicon → contract sync) |
| Runtime per-tool toggle | 0.15 | 0.20 (require redeploy) | **0.90** (`UPDATE … SET enabled=false`) |
| ADR-0056 規約整合 | 0.10 | 0.40 | **0.95** (同 INSERT N rows) |
| ADR-0036 worker-direct 整合 | 0.10 | 0.55 | **0.85** (Kysely + Hyperdrive 直接) |
| 入力 validation depth | 0.10 | 0.85 (Zod + handler) | **0.80** (handler の parseLexiconInput) |
| Bundle size (host-sdk) | 0.05 | 0.55 (+~40 KB Zod + schema) | **0.85** (-30 KB、AJV 不要) |
| Cold start | 0.05 | 0.95 (静的) | **0.85** (60s cache 後) |
| TS 型安全 (MCP 境界) | 0.05 | 0.85 | **0.55** (失う、handler 層は不変) |
| Audit / observability | 0.05 | 0.55 | **0.85** (`vertex_repo_commit` schema 軸と整合) |
| **加重 η (sum / 1.00)** | | **0.55** | **0.88** |

## トレードオフの根拠

- **TS 型安全** で失うのは MCP `tools/list` 出力の型のみ。handler 側の
  入力型 (`LexiconInput<N>`) は `gen-lexicon-nsid-types.mjs` が引き続き
  生成するため、handler 内の `parseLexiconInput()` は完全に型安全のまま。
- **入力 validation** は handler の `parseLexiconInput()` が
  `LEXICON_INPUT_SCHEMA` (lexicon SSoT 由来) で実施。MCP 層で Zod / AJV
  を重ねる必要はない (二重 validation = ADR-0005 違反)。
- **Cold start** は 60s cache + in-flight promise sharing で
  steady-state は無視できる。Kysely + Hyperdrive 1 RTT (~5-15ms) が
  cache miss 時のオーバーヘッド。
- **Bundle size**: 生成物 `tool-manifest.ts` (1 actor あたり ~40 KB)
  と Zod が消える。AJV を入れない方針なので net 削減。

# Consequences

## Positive

- 新規 tool 追加が `lexicon JSON 1 file 追加 + etzhayyim contract sync` で
  完結 (Worker redeploy 不要)。ADR-0056 と完全に同じ規約。
- per-tool runtime toggle (`enabled=false`) / per-org visibility
  (`visibility='org'` + `org_id` filter) / canary (`version` filter) が
  全て row 操作で可能。
- `gen-tool-manifest.mjs` 廃止 → CI build 時間短縮 (~2s/actor)。
- 監査が `vertex_repo_commit` (ADR-0046 triple-witness) の schema 軸と
  一致 (`actor_did + nsid + schema_hash`)。
- ADR-0023 strict-match `lxm` claim は `lxm_scope` 列に明示保存
  (default = `nsid`)、将来 wildcard scope (`com.etzhayyim.apps.foo.*`) へ
  拡張する余地を残す。

## Negative / Trade-off

- MCP `tools/list` は cold cache 時に Kysely SELECT 1 RTT。
  Hyperdrive pool 圧迫を避けるため 60s cache + in-flight share。
- `mcpFacade` (codegen) と `mcpRegistry` (DB) の 2 経路が一時的に
  並存。完全廃止までは新規 actor は registry に寄せる (`etzhayyim deploy`
  が auto-inject)、既存 codegen actor は phase-2 で migration。
- Lexicon → DB の sync が `etzhayyim contract sync` (CI step) に依存。
  CI 不発時は DB 古いまま → `--strict --only-drift` を CI gate で実行。

## Migration

| Step | 内容 | 完了条件 | 状態 (2026-04-25) |
|---|---|---|---|
| 1 | `vertex_mcp_tool_def` migration apply (`apply-pending.sh`) | `pnpm db:drift` 0 件 | ✓ done |
| 2 | `sync-mcp-registry.py --apply` で全 lexicon を ingest | row count == lexicon count | ✓ done (1,738 rows / 178 actors) |
| 3 | host-sdk PR (mcp-registry-loader.ts + host-web-router.ts mcpRegistry path) merge | host-sdk tests green | ✓ done (21/21 vitest) |
| 4 | pilot 1 actor が `mcpRegistry` で deploy、`/mcp tools/list` が DB 由来になる | curl で nsid 列挙確認 | ✓ done (lawfirm.etzhayyim.com, 26 tools) |
| 5 | `etzhayyim deploy` で `APP_ACTOR_HANDLE` env auto-inject + loader fallback 追加 | actor 単位 explicit override 不要 | ✓ done (commit `448e6a6e685`) |
| **G4** | **MCP `tools/call` を `vertex_bpmn_lexicon_binding` 経由で bpmn-dispatcher にルート** | 1M actor scale で actor=data, compute=shared FaaS | **✓ done (commit `9acfffacb6b`, 33/33 vitest)** |
| 6 | CI gate: `sync-mcp-registry.py --strict --only-drift` を pre-merge check に追加 | drift 0 件 | pending (scheduled `trig_014EHSaLranGL4oqVjx8g3FW` 2026-05-09) |
| 7 | `gen-tool-manifest.mjs` を deprecated → 残 codegen actor が 0 になり次第削除 | 全 actor が registry に寄った時 | pending |

各 Step は独立 rollback 可能。Step 4 までは既存 codegen actor に影響しない。

## G4: BPMN dispatcher routing (2026-04-25)

### Context

ADR-2604261000 当初の想定は **N=200 actor** scale だった。1M+ actor 前提で
再評価すると、CF Worker 500/account 制限、K8s pod-per-actor の cost
($20M/月)、DO per-actor の long-tail cold latency 等の制約から、**actor =
Kotoba/Datomic row、compute = shared FaaS via Zeebe ServiceTask** が Shannon η
0.864 で頭一つ抜ける (G4 評価)。これは ADR-0056 BPMN-as-actor + ADR-2604250836
LangGraph as Zeebe ServiceTask と完全に同じ思想。

### Decision

MCP `tools/call` の dispatch logic を 2 段にする:

```
1. vertex_bpmn_lexicon_binding に row があるか? (60s cache)
   ├─ YES → POST dispatcher.etzhayyim.com/xrpc/{nsid} (Zeebe gRPC 経由 pyzeebe pool)
   │           ├─ 2xx/4xx → response 返却 (Zeebe `{ok, variables}` を flat unwrap)
   │           └─ 5xx/timeout/error → fall through ↓
   └─ NO → app.handleXRPC (in-isolate, 既存)
```

Implementation: `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/mcp-bpmn-router.ts`
+ `mcp-server.ts` `dispatchMcp` の `tools/call` case + `host-web-router.ts`
auto-wiring (mcpRegistry 有効時に bpmnRouter も有効、`mcpRegistry.bpmnRouting:
false` で opt-out)。

### Why fall-through on 5xx (not 4xx)

PDS の `pipethroughBpmnDispatcher` (`50-infra/cloudflare/workers/atproto/src/
dispatch.ts:466-484`) と同じ defense-in-depth 設計:
- **5xx / timeout / network error** = dispatcher / Zeebe / pyzeebe pool の
  infra 障害 → in-process handler に逃がして actor 全滅を回避
- **4xx** = application-level error (validation 失敗等) → client に verbatim
  surface

### Header forwarding

incoming MCP request の以下のみ dispatcher に forward (それ以外は drop):
- `authorization`
- `content-type`
- `x-etzhayyim-*`
- `atproto-*`

`cookie` / `host` / `user-agent` 等は drop して情報漏洩を防ぐ。
`DISPATCHER_INTERNAL_SECRET` env (or `SS_DISPATCHER_INTERNAL_SECRET` Secrets
Store binding) があれば `x-internal-trust` header に attach (ADR-2604231457
strict mode 準備)。

### Cache 戦略

- **route lookup cache**: per-NSID 60s, positive AND negative。"binding
  存在しない" も cache して in-process tool の call 毎に DB hit しない。
- **DB error**: 5s 短期 negative cache → recovering DB を block しない。
- **In-flight promise sharing**: 同じ NSID への concurrent lookup は 1 SELECT
  に集約 (cold cache の barrier storm 回避)。

### 新規 BPMN-routed tool 追加手順

```sql
-- ADR-0056 と完全同じ INSERT N rows 規約:
INSERT INTO vertex_bpmn_lexicon_binding
  (vertex_id, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at)
VALUES
  ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.bpmn.binding/{ns-action}-v1',
   '{nsid}', '{bpmn_process_id}', 1, 30000, 'active',
   to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'));
```

60s cache 期限切れで自動切替。Worker redeploy 不要。

### Out of scope

- Zeebe ServiceTask 内 LangGraph (ADR-2604250836 で別扱い)
- BPMN process 自体の作成 (ADR-0056 sync-bpmn-actors.py で別途管理)
- per-tool timeout の細分化 (現状は `result_timeout_ms` 単純使用)

## Pilot findings (2026-04-25, lawfirm.etzhayyim.com)

### F1. Default `actorDid` resolution mismatches sync-script keying

`mcpRegistry: {}` の default `actorDid` 解決順は (host-web-router.ts):

```
mcpRegistry.actorDid → APP_DID → PERFORMER_DID → did:web:{APP_NANOID}.etzhayyim.com
```

一方 `sync-mcp-registry.py` は NSID 4th segment (`com.etzhayyim.apps.{actorSlug}.*`)
から `did:web:{actorSlug}.etzhayyim.com` を生成する。lawfirm の場合:

| Source | Value |
|---|---|
| Default (APP_NANOID) | `did:web:lf1rm8k0.etzhayyim.com` |
| Sync script (NSID slug) | `did:web:lawfirm.etzhayyim.com` |

→ 不一致で 0 行。`mcpRegistry: { actorDid: "did:web:lawfirm.etzhayyim.com" }`
の明示が必要。

**Mitigation (本 ADR 範囲内で実装済)**:
- `mcp-registry-loader.ts` が 0 行時に `console.warn` を出して driver
  ヒントを残す。
- ADR ↑ `mcpRegistry: { actorDid }` を pilot 例として明示。

**Step 5 で恒久化予定**: `etzhayyim deploy` が `APP_ACTOR_HANDLE` env を inject
し、loader の default を `did:web:{APP_ACTOR_HANDLE}.etzhayyim.com` に切替。
APP_ACTOR_HANDLE は `kotodama.jsonld` の `profile.handle` か、なければ
component dir 名 (`etzhayyim-wasm-{slug}-*`) から派生。

### F2. `mcpFacade` と `mcpRegistry` 並存パターンが正解

OpenAPI 3.0 publishing は依然 `mcpFacade.routes` 経由 (codegen)。本 ADR
は OpenAPI registry 化を範囲外とするため、pilot actor は両方渡すのが
理に適う:

```ts
}, {
  mcpRegistry: { actorDid: "did:web:lawfirm.etzhayyim.com" },  // /mcp ← DB
  mcpFacade: { ...lawfirmManifest },                      // /.well-known/openapi.json ← codegen
});
```

`host-web-router.ts` は `mcpRegistry` が勝つ実装になっており、`/mcp` は
DB、OpenAPI は codegen で並走する。Step 7 で OpenAPI も DB-derived に
寄せる別 ADR を起案する。

### F3. 150 generated tool-manifest files were orphaned

`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/generated/tool-manifest/`
に codegen 済 152 ファイルがあったが、実際に import されていたのは
`lawfirm.ts` のみ (152 中 1)。残り 150 + `_types.ts` は dead source-tree。

Pilot 中に 150 を削除 (4.1 MB → 80 KB)。`lawfirm.ts` + `_types.ts` は
Step 7 で lawfirm の OpenAPI 移行と同時に削除する。

### F4. apply-pending.sh が必須経路

`pnpm db:migrate` (kysely migrator) は本 repo では fail する (ADR-2604241342
Failure A)。pilot では Failure A に追加で **compute pod panic** が発生
(actor 数 10K+ で hard limit を超過、CLAUDE.md 想定の 2.4K の 4 倍)。
apply-pending.sh 経由で 1 migration ずつ apply する経路は ADR-2604241342
の通り正解。

### F5. 1,738 連続 INSERT は cluster 再起動を誘発する

初版 `sync-mcp-registry.py` は per-row `psycopg2.connect()` を 1,738 回
開いた → barrier storm で cluster recovery 入り。修正: 単一接続 + 100-row
chunk 多値 INSERT (`apply_batch`)。Kotoba/Datomic の write pattern は
fewer-larger-batches を好む。

# Alternatives Considered

## A. ADR-0087 §D3 codegen のまま

- η ≈ 0.55。
- ADR-0056 BPMN-as-actor と規約が割れる。
- runtime per-tool enable/disable が redeploy を要求。

## B. Kysely registry (採用)

- η ≈ 0.88。
- Trade-off は MCP 層での Zod 静的型を失うこと (handler 層は無関係)。
- AJV を別途同梱して MCP 層 validation を復活させる選択肢は ADR-0005
  違反 (二重 validation)、`parseLexiconInput()` で十分。

## C. AJV + DB registry (hybrid)

- η ≈ 0.82 (B より低い)。
- AJV ~30 KB を host-sdk に追加。MCP 層 + handler 層で 2 重 validation。
- ADR-0005 違反、却下。

## D. PDS 集約 `com.etzhayyim.mcp.message` を per-actor scope 拡張

- ADR-0087 で既に却下済 (SPoF, ADR-0036 逆行)。本 ADR でも採用しない。

# References

- ADR-0087 — kotodama per-actor MCP tool facade (`90-docs/adr/0087-kotodama-mcp-tool-facade.md`)
- ADR-0056 — BPMN-as-actor (`90-docs/adr/0056-bpmn-as-actor.md`)
- ADR-0036 — Worker-direct Hyperdrive persistence
- ADR-0005 — Shannon redundancy prohibition
- ADR-0023 — Auth Shannon-optimal 4-layer (lxm strict match)
- migration `20260423050934_vertex_kind_mcp_capability.ts` — 既存 kind→MCP binding 前例
- migration `20260425100000_vertex_mcp_tool_def.ts` — 本 ADR の DDL
- `70-tools/scripts/contract/sync-mcp-registry.py` — sync pipeline
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/mcp-registry-loader.ts` — runtime loader
- MCP Streamable HTTP — https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
