---
id: f-plan-lexicon-as-contract
title: "F-Plan — Lexicon-as-Contract: Host Capability SSoT 統合 (WIT 廃止)"
status: active
doc_type: explanation
topic: lexicon-as-contract
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - magatama-host-sdk host capability surface の Single Source of Truth
  - host capability の codegen pipeline (lex-cli analog)
  - WIT vs Lexicon JSON contract 戦略
  - in-process host capability dispatch (BindingTransport pattern)
  - Lexicon から MCP / gRPC / XRPC / BPMN へ投影する際の Shannon loss 方針
  - Lexicon を semantic contract layer として扱う transport projection 原則
  - F-Plan migration phases (1 → 2 → 3 → 3b)
  - Shannon η 計算 (host capability surface)
related:
  - w-protocol-at-superset-architecture
  - did-path-lexicon-correspondence
  - wit-lexicon-typed-alignment
  - adr-0087-magatama-mcp-tool-facade
  - adr-2604261000-mcp-registry-via-kysely-schema
supersedes:
  - wit-lexicon-typed-alignment
superseded_by: []
---

# F-Plan — Lexicon-as-Contract: Host Capability SSoT 統合

## Goal

magatama-host-sdk の host capability surface (app に提供される ~100 個の host 関数) を **Lexicon JSON のみ** から派生する状態にする。WIT を contract layer から外し、混乱の源を消す。Shannon η = 1.0 (host capability の単一 SSoT)。

## Scope

**対象**: TS Native (DEFAULT, T3) 経路。`src/app.ts` + `@etzhayyim/magatama-host-sdk` + esbuild → CF Worker。

**対象外**: T3 Container (wasmtime, ~2 components) 経路。Rust contract-jco generator (1 component)。これらは WIT を継続使用。

## Executive Summary

| 局面 | F1 host | F2 app | F3 wire | F4 identity | F5 gov | S̄ | Shannon η |
|---|---|---|---|---|---|---|---|
| Phase 0 (初期) | 3 (WIT + TS + host-imports) | 3 | 2 | 1 | 1 | 2.0 | **0.70** |
| Phase 2 後 | **1 (Lexicon)** | 3 | 2 | 1 | 1 | 1.6 | 0.78 |
| Phase 3b 後 (WIT archive) | **1** | 3 | 2 | 1 | 1 | 1.6 | **0.85** (実効: WIT noise 除去) |
| **F2 complete (current, 2026-04-13)** | **1** | **1** | **1** | **1** | **1** | **1.0** | **1.00** |

F-Plan は Phase 1〜3b で **F1 (host capability surface)** を Lexicon SSoT に統合し、続く F2 ステップ群 (codemod sweep、runtime validator、schema inference、legacy assert archive) で **F2 app command surface** と **F3 wire format** も Lexicon SSoT に完全統合した。全 5 contract facts が単一 SSoT + 派生物構造で η = 1.0 を達成。

## Decision

**Lexicon JSON が host capability surface の唯一の SSoT。** WIT は archive、TS interface は派生物 (codegen 出力)。

これは **atproto SDK の `lex gen-api` pattern と完全一致** する。`bluesky-social/atproto/packages/api/package.json` に:

```json
"scripts": {
  "codegen": "lex gen-api --yes ./src/client ../../lexicons/com/atproto/*/* ../../lexicons/app/bsky/*/* ..."
}
```

W Protocol は AT Protocol の superset を宣言している以上、contract layer でも superset 関係を保つのが自然。

### 2026-04-25 amendment: Lexicon is the semantic contract, transports are projections

Lexicon は **transport protocol そのものではなく、semantic contract layer** として扱う。
MCP / gRPC / XRPC / BPMN は Lexicon から派生する projection であり、SSoT ではない。

Shannon 的には、`Lexicon → MCP tool schema` / `Lexicon → gRPC proto` /
`Lexicon → XRPC handler` / `Lexicon → BPMN binding` が **可逆**であれば情報欠損は無い。
欠損が起きるのは bit 列の問題ではなく、次の semantic / operational metadata を
projection 側に写さない時である:

- `description`, examples, human/agent-facing tool text
- NSID namespace, actor DID / owner DID, repo / app boundary
- `procedure` / `query` / `record` の種別
- `x-etzhayyim-*` 拡張 (`capabilityTags`, `sensitivity`, `auth`, `sideEffects`,
  `idempotency`, `timeoutMs`, `resultSemantics`, `bpmnProcessId`)
- JSON Schema の nullable / union / additionalProperties / format / encoding
- governance / consent / audit / Service Auth `lxm` の scope 情報

したがって、MCP / gRPC を使う場合も、設計規則は:

```
Lexicon = canonical semantic contract / namespace / schema / docs / auth hints
MCP     = agent-facing projection of Lexicon procedures
gRPC    = internal high-performance projection where needed
XRPC    = web/federated/public procedure surface
BPMN    = long-running orchestration binding
```

MCP を主 SSoT にしない。MCP は tool discovery と LLM/agent runtime 接続には強いが、
DID ownership、federation、durable record graph、BPMN binding、governance metadata を
標準では保持しない。gRPC も主 SSoT にしない。gRPC は server-to-server の型安全・streaming・
codegen に強いが、human/agent 向け説明や federation metadata は標準 field ではない。

projection が不可逆になる field は必ず Lexicon 側に `x-etzhayyim-*` として残す。
推奨 extension:

| Field | Meaning |
|---|---|
| `x-etzhayyim-transport.mcp.toolName` | MCP tool 名。省略時は NSID をそのまま使う |
| `x-etzhayyim-transport.grpc.service` | gRPC service / method への projection hint |
| `x-etzhayyim-bpmn.processId` | BPMN process id / Zeebe task binding |
| `x-etzhayyim-auth` | Service Auth / permission-set / `lxm` scope |
| `x-etzhayyim-capabilityTags` | MCP discovery / ActorCapability graph tags |
| `x-etzhayyim-sensitivity` | data classification / federation gate |
| `x-etzhayyim-idempotency` | retry / dedupe contract |
| `x-etzhayyim-sideEffects` | write / dispatch / external call semantics |
| `x-etzhayyim-timeoutMs` | BPMN / MCP / worker timeout budget |
| `x-etzhayyim-ownerDid` | actor / app ownership boundary |
| `x-etzhayyim-resultSemantics` | result shape beyond bare JSON Schema |

外部 ecosystem の都合で MCP tool name や gRPC method name が NSID から変形される場合も、
mapping は Lexicon extension か generated registry (`vertex_mcp_tool_def`) に置き、
handler / proto / MCP manifest 側に手書き再定義しない。これにより semantic decision の
source count は 1 のまま保たれ、Shannon η=1.0 を維持できる。

## Architecture

```
00-contracts/lexicons/com/etzhayyim/host/                   ← SSoT (37 lexicons across 21 capability groups)
├── core/configGet.json,        logAppend.json
├── authn/verifyToken.json
├── authz/enforce.json
├── ipfs/publish.json
├── storage/putObject.json,     getObject.json
├── cdn/upload.json,            publicUrl.json
├── telemetry/emitMetric.json,  log.json
├── accessLog/record.json
├── ocel/emitEvent.json
├── pubsub/publish.json,        pull.json
├── secrets/get.json,           set.json,    delete.json
├── lock/tryLock.json,          unlock.json
├── virtualActor/invoke.json
├── llm/converse.json,          chat.json,   route.json,   react.json
├── activity/spawnParallel.json, awaitAll.json
├── identity/resolve.json,      listActors.json
├── capability/listOwn.json,    discover.json
├── conversation/createSession.json, sendMessage.json
├── governance/registerManifest.json, checkPolicy.json
├── invoke/call.json
└── cypher/query.json           (compat shim — prefer createKyselyDb)

  ↓ codegen (lex-cli analog)

70-tools/scripts/contract/gen-host-client-from-lexicon.mjs

  ↓ 派生

20-actors/magatama/sdk/magatama-host-sdk/src/generated/host-client.ts
   │  - 37 typed capability functions
   │  - HOST_NSID frozen constants
   │  - HostDispatcher interface
   │  - setHostDispatcher() registration
   │
   └── 各 lexicon の x-hostImportsMethod 拡張 → dispatcher routing key

  ↓ runtime dispatch

20-actors/magatama/sdk/magatama-host-sdk/src/host-dispatcher.ts
   │  switch (nsid) {
   │    case HOST_NSID.secretsGet: ...   // → hostImports.secretsGet(input.key)
   │    case HOST_NSID.cypherQuery: ...  // → hostImports.graphExec(...)
   │    ...
   │  }

  ↓ in-process (BindingTransport pattern)

20-actors/magatama/sdk/magatama-host-sdk/src/host-imports.ts
   - existing 1287-line implementation, untouched
```

### Lexicon schema convention

各 host lexicon は標準 AT Protocol Lexicon schema + `x-hostImportsMethod` 拡張を持つ:

```json
{
  "lexicon": 1,
  "id": "com.etzhayyim.host.secrets.get",
  "defs": {
    "main": {
      "type": "query",
      "description": "Retrieve a secret value by key from the host secret store.",
      "x-hostImportsMethod": "secretsGet",
      "parameters": {
        "type": "params",
        "properties": { "key": { "type": "string" } },
        "required": ["key"]
      },
      "output": {
        "encoding": "application/json",
        "schema": {
          "type": "object",
          "properties": {
            "value": { "type": "string" },
            "found": { "type": "boolean" }
          },
          "required": ["found"]
        }
      }
    }
  }
}
```

`x-hostImportsMethod` が host-imports.ts のメソッド名を指す → host-dispatcher.ts の switch case が機械的に対応する。

## Migration Phases

### Phase 1: Scaffold (POC)

- 3 capability lexicons (secrets.get, cypher.query, llm.converse)
- `gen-host-client-from-lexicon.mjs` 実装
- `host-dispatcher.ts` (1 case のみ)
- 4 vitest tests proving end-to-end path
- **既存 code への変更ゼロ** (新規ファイルのみ)

### Phase 2: Full host surface

- 21 capability groups × 1〜4 flagship methods = **37 lexicons**
- bootstrap script (`bootstrap-host-lexicons.mjs`) で一括生成
- host-dispatcher.ts に 37 case 実装 (b64/bigint/json adapter 含む)
- vitest 拡張: 全 NSID coverage guard (新 NSID 追加時の dispatcher 漏れを compile-time-like に検出)
- **141/141 host-sdk tests pass**, リグレッションなし
- **既存 host-imports.ts への変更ゼロ**

### Phase 3: Rules / docs

- `CLAUDE.md` (root) の `LLM Coding Guardrails` から `wit/world.wit` 必須要件を削除
- `CLAUDE.md` の `Key Conventions` "TS Native + WIT Contract" → "TS Native + Lexicon Contract"
- `deps.toml` の `[[conventions]]` / `[directory_index.*]` / `[app_layer.*]` を更新
- `20-actors/magatama/CLAUDE.md` に新セクション `## Host Capability Contract (Lexicon SSoT, F-Plan 2026-04-13)` 追加

### Phase 3b: WIT archive

- 503 per-component `wit/world.wit` + 435 project-level `package.wit` + transitive deps = **3007 .wit files** archived to `_archive/wit-2026-04-13/`
- 936 component dirs cleaned of inert WIT scaffolding
- **2 components retained in-tree** (legacy compat):
  - `60-apps/etzhayyim-project-cad/appview/etzhayyim-wasm-cad-cd4dview/wit/` (T3 Container, runtimeType: container)
  - `60-apps/etzhayyim-project-hoge/appview/etzhayyim-wasm-hoge-h0g3t3st/contract-jco/wit/` (Rust contract-jco generator)
- `etzhayyim build` の `validateMagatamaGovernanceImport` は missing wit/ を silent skip (build.go:558-560)
- **141/141 host-sdk tests pass**

### F2: App command contract (2026-04-13)

F1 (host capability) 統合に続き、F2 (app command surface) も Lexicon SSoT に統合:

- **NSID type guards 強化**: `AssertCommandNSID` / `AssertQueryNSID` (loose) を archive、`StrictCommandNSID` / `StrictQueryNSID` (compile-time unknown-NSID error) を `sdk.app.command` / `sdk.app.query` のデフォルトに昇格
- **`nsid()` tagged helper**: `LEXICON_NSID` frozen record から NSID を compile-time 検証付きで参照
- **`LexiconInput<N>` / `LexiconOutput<N>`**: per-NSID I/O 型マップ (2243 エントリ) から lexicon schema → TS 型を自動派生
- **Runtime validator** (`parseLexiconInput()` / `LexiconValidationError`): lexicon `LEXICON_INPUT_SCHEMA` registry を runtime 参照し、必須プロパティ・型不一致を throw で検出

#### Codemod sweep (195 apps)

| Script | 役割 | 結果 |
|---|---|---|
| `bootstrap-app-lexicons.mjs` | app.ts から不明 NSID を抽出 → stub lexicon 自動生成 | **1765 stubs created** |
| `f2-codemod.mjs` | `.command("ai...", ...)` → `.lexiconCommand(nsid("ai..."), ...)` | **192 files migrated** |
| `infer-lexicon-schemas.mjs` | Handler body 解析 → stub lexicon に input/output/required を書き戻し | **1171 lexicons enriched** |
| `parseLexiconInput-codemod.mjs` | `decodeJson(body, {})` → `parseLexiconInput("nsid", body)` (inline + single-use named fn) | **495 rewrites across 36 apps** |

**Inference patterns** (`infer-lexicon-schemas.mjs`):

- Destructured args: `const { name, age } = decodeJson(body, {})`
- Typed generic: `decodeJson<{foo: string; bar: number}>(body, ...)`
- Fallback literal: `decodeJson(body, { foo: "", count: 0 })`
- Property access: `str(args.X)` / `num(args.Y)` / `Boolean(args.Z)` / `Array.isArray(args.W)`
- Output: `return { ok: true, id: foo, error?: ... }` → output.schema
- Required: `if (!args.X || !args.Y)` + local var tracking (`const foo = str(args.foo); if (!foo) ...`)

#### Holdout apps (manually migrated 2026-04-13)

- **shinshi**: `"shinshi.createDID"` → `com.etzhayyim.apps.shinshi.createDid` (short-form → fully-qualified AT Protocol NSID)
- **i18n**: ``${CMD_SERVICE}.RegisterProject`` × 12 → `com.etzhayyim.apps.i18n.registerProject` × 12 (template literal → static literal)
- **outlook-mcp-component**: ``${SERVICE_NS}.GetOAuthConfig`` × 10 → `com.etzhayyim.apps.outlook.getOauthConfig` × 10
- **media-gamers**: 5 underscore-name NSIDs migrated via re-run of codemod after stub bootstrap

#### Legacy archive

- `AssertCommandNSID` / `AssertQueryNSID` loose types → `_archive/20-actors/magatama/sdk/magatama-host-sdk-legacy-nsid-assert-260413/`
- `@etzhayyim/magatama-host-contract` 12-line stub package → inlined into `magatama-host-sdk/src/types.ts`, archived to `_archive/00-contracts/magatama-host-contract-260413/`
- `build.go` dead `validateWITVersion` path → softened to optional (only runs when `--wit-dir` / `MAGATAMA_WIT_DIR` is set)

#### Final state

- **198 / 198 apps** on strict-typed command/query
- **2346 lexicons** (2243 XRPC + 82 record + 21 permission-set)
- **165 / 165 host-sdk tests** passing (152 + 13 validator tests)
- **Shannon η = 1.0** across F1 (host) / F2 (app command) / F3 (wire) / F4 (identity) / F5 (governance)

## Codegen Pipeline (lex-cli analog)

| Layer | Path |
|---|---|
| Lexicon SSoT | `00-contracts/lexicons/com/etzhayyim/host/**/*.json` |
| Codegen tool | `70-tools/scripts/contract/gen-host-client-from-lexicon.mjs` (444 lines, lex-cli analog) |
| Bootstrap | `70-tools/scripts/contract/bootstrap-host-lexicons.mjs` (one-shot, idempotent) |
| Generated typed client | `20-actors/magatama/sdk/magatama-host-sdk/src/generated/host-client.ts` |
| In-process dispatcher | `20-actors/magatama/sdk/magatama-host-sdk/src/host-dispatcher.ts` |
| Host implementation (legacy, unchanged) | `20-actors/magatama/sdk/magatama-host-sdk/src/host-imports.ts` |

### Adding a new host capability

1. `00-contracts/lexicons/com/etzhayyim/host/{group}/{action}.json` を作成 (`x-hostImportsMethod` 必須)
2. `node 70-tools/scripts/contract/gen-host-client-from-lexicon.mjs` で typed client 再生成
3. `host-dispatcher.ts` の switch に case を追加
4. 必要なら `host-imports.ts` に実装を追加
5. `pnpm exec vitest run` で 141+ tests 合格を確認 (coverage guard が新 NSID dispatch 漏れを検出)

**禁止**: TS interface を先に書いて lexicon を後追いで作ること (Shannon η が下がる)。Lexicon が SSoT で TS は派生物。

## Comparison: WIT vs Lexicon (F1 host capability surface)

| 軸 | WIT (旧) | Lexicon (新) |
|---|---|---|
| TypeScript 型安全性 | ◎ (jco-generated bindings) | ◎ (codegen) |
| 多言語 SDK 同形性 | × (各言語別 codegen 必要) | **◎** (atproto と同じ pattern、Go/Rust/Python codegen 流用可能) |
| AT Protocol federable | × | **◎** (W Protocol superset として一貫) |
| validator 生成 | × (手書き) | **◎** (lex-cli が生成) |
| Wire format と host interface の名前空間統一 | × (別系統) | **◎** (`com.etzhayyim.host.*` / `com.etzhayyim.apps.*` 同じ NSID space) |
| Description / doc string ホバー | △ (WIT comment) | **◎** (Lexicon `description` field) |
| Build 依存 | jco / canonical-abi / wasm-tools | **なし** (esbuild + node script) |
| Build time | 数秒 (jco) | **<1s** (純粋 TS) |

WIT の唯一の優位性は wasm component model の wire format ですが、T3 TS Native では wasm 境界自体がないため無意味。

## Exceptions (T3 Container / Rust)

T3 Container (wasmtime runtime) と Rust contract-jco generator は WIT を継続使用:

- `60-apps/etzhayyim-project-cad/appview/etzhayyim-wasm-cad-cd4dview/`
  - 理由: 128MB Worker memory 制約超過のため Container mode、jco bridge 必須
- `60-apps/etzhayyim-project-hoge/appview/etzhayyim-wasm-hoge-h0g3t3st/contract-jco/`
  - 理由: contract-jco generator は WIT を入力として WASM component を出力する Rust ツール

これらは WIT を入力に持つ legitimate use case であり、Lexicon に置き換える必要がない。

## Shannon Analysis

### F1 (host capability surface)

- 旧: WIT world.wit + TS host-imports.ts + magatama-host-sdk types = 3 sources
- 新: Lexicon JSON のみ (TS は派生) = 1 source
- 効率: η_F1 = 1/3 → **1.0**

### 全体 (5 facts)

```
η = log2(N) / mean(log2(N · S_i))
  = 1 / (1 + log2(S̄) / log2(N))
```

- N = 5, S̄ = 1.6 (Phase 3b 後)
- η = 1 / (1 + log2(1.6)/log2(5)) = 1 / (1 + 0.678/2.322) ≈ **0.78** (理論値)

ただし WIT noise の物理的除去 (3007 files archive) で **dead source** が消えたため、実効的な mental model 上の S̄ は 1.4 まで下がり、効率は **0.85** に相当。

η = 1.0 にするには Phase 4 (app 側 migration) と D (F2/F3 codegen 統合) を完了する必要がある。

## Counter Arguments

### 「WIT は wasm component model の標準」

- 標準であるのは wire format としてのみ。T3 TS Native は wasm 境界がないので適用不能。
- T3 Container には残置済み。

### 「Lexicon は AT Protocol の wire 用で host interface 用ではない」

- 形式上は wire 用。しかし `BindingTransport` (CF Worker service binding RPC) という in-process transport が既に存在し、Lexicon を transport-agnostic な contract として使える。
- atproto 自身も `@atproto/lexicon` package を server-side validator に使っている前例あり。

### 「F2 / F3 が未統合なので η < 1.0、価値が薄い」

- F1 だけでも 3007 ファイルの dead noise が消え、新規 app の認知負荷が大きく下がる。
- Phase 4 と D は別 PR で段階的に実施可能、F1 を先に統合する判断は非可逆ではない。

## References

- 旧設計 (superseded): `90-docs/atproto/260324-wit-lexicon-typed-alignment-design.md`
- 権威 reference: `20-actors/magatama/CLAUDE.md` §Host Capability Contract (Lexicon SSoT, F-Plan 2026-04-13)
- atproto codegen pattern: `bluesky-social/atproto/packages/api/package.json` `"codegen": "lex gen-api ..."`
- Migration tracking: `deps.toml [[migrations]] §wit-contract-layer-removal`
- Archive location: `_archive/wit-2026-04-13/` (3007 files)
- Test coverage: `20-actors/magatama/sdk/magatama-host-sdk/test/host-dispatcher.test.ts` (10 tests, 141/141 全体合格)
