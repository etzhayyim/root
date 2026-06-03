---
id: 260324-source-graph-hybrid-design
title: Source Graph — 3-Layer Hybrid Extraction (Shannon-Optimal)
status: active
doc_type: explanation
topic: source-graph-annotation
authoritative: true
last_verified: 2026-03-24
authoritative_for:
  - source-level annotation system
  - source graph extraction architecture
  - etzhayyim source-graph CLI
related:
  - 260319-magatama-wit-dodaf-nist-coverage
  - 260324-source-graph-hybrid-design
  - 260323-yoro-human-credit-economy-design
supersedes: []
superseded_by: []
---

# Source Graph — 3-Layer Hybrid Extraction

## Goal

Bazel が BUILD ファイルで宣言する dependency/visibility/rule を、ソースコードから自動抽出 + コメント差分宣言で実現し、既存の yata Cypher グラフに投影して violation を検出する。

## Scope

- 対象: 全 App (2,045+ Go, 25+ Rust, 30+ TS ソースファイル)
- CLI: `etzhayyim source-graph {scan,violations,cypher,dot}`
- scoring: `source_graph_score` (0-100)

## Decision: 3-Layer Hybrid (Approach E)

Shannon 情報理論に基づき、冗長度最小で情報量最大のアプローチを採用。

| Layer | Source | 抽出内容 | 冗長度 | 実装 |
|---|---|---|---|---|
| **L1: Metadata** | `magatama.jsonld` + `world.wit` (既存) | import/export, performerType, DID, collections, sensitivity | **0%** | `source_graph_meta.go` |
| **L2: AST** | `go/ast` (Go), regex (TS/Rust) | WRecord kinds, Cypher labels, Commands, Invoke calls, Serve | **0%** | `source_graph_ast.go` |
| **L3: `@etzhayyim:`** | コメント宣言 (差分のみ) | authority, contract, sensitivity, cross-app intent | **~15%** | `source_graph.go` |

### Approach 比較 (定量)

| # | Approach | 冗長度 | 自動率 | 保守 h/年 | Stale 率 |
|---|---|---|---|---|---|
| A | `@etzhayyim:` のみ | 100% | 0% | ~500h | ~35% |
| B | AST のみ | 0% | ~70% | ~0h | 0% |
| C | AST + `@etzhayyim:` | ~15% | ~85% | ~80h | ~9% |
| D | WIT + jsonld のみ | 0% | ~40% | ~0h | 0% |
| **E** | **D + B + `@etzhayyim:`** | **~8%** | **~85%** | **~40h** | **~4.5%** |

Approach E は A 比で冗長度 12.5x 改善、保守コスト 12.5x 改善。

## Layer 1: WIT + magatama.jsonld

既存 artifact からゼロコスト抽出。`sgParseJSONLD()` が `magatamaJSONLD` struct (deploy.go 既存) を再利用。`sgParseWIT()` が `witImportRe`/`witExportRe` (hooks.go 既存) を再利用。

抽出対象:
- `@id` → DID
- `performerType` → service/system/person/organization
- `triggers.wCommit.collections` → reactive input collections
- `interfaces.requires` → WIT dependency
- `world.wit` import/export/include → WIT interface graph

## Layer 2: AST Extraction

### Go (`go/ast`)

標準ライブラリ `go/ast` で完全な AST 解析。historical guest Go files も `parser.ParseFile` で parse 可能 (構文解析のみ、import 解決不要)。Parse 失敗時は regex fallback。TS native (default) は TS AST で解析。

| SDK Call | 抽出 | ノード属性 |
|---|---|---|
| `magatama.WRecord("kind", ...)` | Write target | `writes: ["kind"]` |
| `magatama.WRecordUpdate("kind", ...)` | Write target | `writes: ["kind"]` |
| `magatama.ATPost(did, ...)` | cross-actor call | `calls: ["did#ATPost"]` |
| `magatama.ATPostWithRecord(text, coll, rkey)` | Write target | `writes: ["coll"]` |
| `magatama.G("Label")` | Cypher read | `reads: ["cypher:Label"]` |
| `magatama.Invoke(did, method, ...)` | cross-actor call | `calls: ["did#method"]` |
| `app.Command("", "name", ...)` | Command registration | `commands: ["name"]` |
| `app.Query("", "name", ...)` | Query registration | `queries: ["name"]` |
| `magatama.HandleWCommit(handler)` | Event handler | `handlers: ["handler"]` |
| `app.Serve()` | App registration | `has_serve: true` |
| `magatama.DIDCreate(path, ...)` | DID creation | `dids: ["path"]` |
| `magatama.Follow(did)` | Follow target | `follows: ["did"]` |

Per-function breakdown: 各関数内の WRecord/G/Invoke を個別にトラッキングし、func-level ノードとして graph に投影。

### TypeScript (regex)

PDS `index.ts` 等の infra TS ファイルを対象。

| Pattern | 抽出 |
|---|---|
| `MATCH (...:Label)` | Cypher read labels (全 `(var:Label)` パターン) |
| `MERGE (...:Label)` | Cypher write labels |
| `case "MethodName":` | XRPC method handlers |
| `createRecord/mergeRecord("coll")` | Write collections |
| `export async function name()` | 関数定義 |

### Rust (regex)

WASM component `lib.rs` を対象。

| Pattern | 抽出 |
|---|---|
| `w_record("kind")` / `WRecord("kind")` | Write target |
| `G("Label")` / `.g("label")` | Cypher read |
| `app.command("", "name", ...)` | Command registration |
| `app.serve()` / `.serve()` | App registration |
| `WithCapabilityTags(vec!["tag".into()])` | Capability tags |
| `pub async fn name(...)` | 関数定義 |

## Layer 3: `@etzhayyim:` Annotation (差分宣言)

AST で抽出不可能な意図・契約・権限のみ手書き宣言。

### 構文

```
// @etzhayyim:<directive> <value>
```

Go / Rust / TS / WIT 共通。

### Directive 一覧

| Directive | Scope | 意味 | Cypher 投影 |
|---|---|---|---|
| `@etzhayyim:import <wit>` | file/func | WIT 依存宣言 | `(:Source)-[:IMPORTS]->(:WITInterface)` |
| `@etzhayyim:lexicon <nsid>` | file/func | AT Lexicon 対応 | `(:Source)-[:IMPLEMENTS]->(:Lexicon)` |
| `@etzhayyim:calls <did>#<method>` | func | cross-actor 呼出 | `(:Source)-[:INVOKES]->(:DID)` |
| `@etzhayyim:writes <collection>` | func | Write 先宣言 | `(:Source)-[:WRITES_TO]->(:Collection)` |
| `@etzhayyim:reads <collection>` | func | Read 先宣言 | `(:Source)-[:READS_FROM]->(:Collection)` |
| `@etzhayyim:authority <kind>/<id>` | file | 準拠 authority | `(:Source)-[:GOVERNED_BY]->(:Authority)` |
| `@etzhayyim:rule <rule-id>[,...]` | file/func | 適用ルール | `(:Source)-[:ENFORCES]->(:Rule)` |
| `@etzhayyim:sensitivity <level>` | file | データ分類 | property on `:Source` node |
| `@etzhayyim:owner <did>` | file | 責任 DID | `(:Source)-[:OWNED_BY]->(:DID)` |
| `@etzhayyim:contract <cat>/<id>` | file | 契約根拠 | `(:Source)-[:BOUND_BY]->(:Contract)` |
| `@etzhayyim:supersedes <path>` | file | 置換元 | `(:Source)-[:SUPERSEDES]->(:Source)` |
| `@etzhayyim:visibility <level>` | file/func | Access scope | property on `:Source` node |
| `@etzhayyim:ref <doc-path>` | file | 設計 doc 参照 | `(:Source)-[:REFERENCES]->(:Document)` |

### 使用例

```go
// @etzhayyim:authority sovereign/jpn, treaty/wto
// @etzhayyim:sensitivity confidential
// @etzhayyim:owner did:web:news.etzhayyim.com
// @etzhayyim:ref 90-docs/260324-news-wrpc-stream-reactive-design.md

func (app *App) handleArticle(commit wCommit) {
    // @etzhayyim:calls did:web:i18n.etzhayyim.com#translate
    magatama.ATPost(did, text, opts)
}
```

L2 AST が `ATPost` call を自動抽出。L3 `@etzhayyim:calls` は cross-app intent (「翻訳のために呼ぶ」) を宣言。`@etzhayyim:authority` / `@etzhayyim:sensitivity` は AST 不可分。

## Violation Detection

8 ルール:

| Rule | Severity | 検出 |
|---|---|---|
| `wit-import-drift` | warning | `@etzhayyim:import` 宣言が `world.wit` に存在しない |
| `sensitivity-escalation` | error | confidential/restricted source が public DID を呼出 |
| `authority-gap` | info | sovereign authority 宣言に treaty がない |
| `dead-supersedes` | warning | `@etzhayyim:supersedes` 先ファイルが存在しない |
| `shannon-redundancy` | warning | 同一 collection に複数 app が書込 |
| `rule-no-dual-write` | error | `@etzhayyim:rule no-dual-write` 宣言に writes 2+ |
| `dead-ref` | warning | `@etzhayyim:ref` 先ドキュメントが存在しない |
| `circular-dependency` | error | calls グラフに循環 |

## Score Model

```
source_graph_score =
    25% * auto_extract_rate      (L1+L2 automation: no manual work)
  + 25% * violation_free_rate    (nodes without violations / total)
  + 20% * annotation_coverage    (L3 annotated files / total files)
  + 15% * authority_coverage     (nodes with authority / total nodes)
  + 15% * reference_integrity    (valid refs / total refs)
```

## Cypher Graph Schema

```cypher
// Nodes
(:Source {path, kind, func_name, line, app_did, sensitivity, visibility})
(:WITInterface {fqn})
(:Lexicon {nsid})
(:Authority {kind, id})
(:Rule {id})
(:Contract {category, id})
(:Document {path})
(:DID {id})           // merges with existing :DID nodes
(:Collection {nsid})

// Edges
(:Source)-[:IMPORTS]->(:WITInterface)
(:Source)-[:IMPLEMENTS]->(:Lexicon)
(:Source)-[:INVOKES {method}]->(:DID)
(:Source)-[:WRITES_TO]->(:Collection)
(:Source)-[:READS_FROM]->(:Collection)
(:Source)-[:GOVERNED_BY]->(:Authority)
(:Source)-[:ENFORCES]->(:Rule)
(:Source)-[:BOUND_BY]->(:Contract)
(:Source)-[:SUPERSEDES]->(:Source)
(:Source)-[:REFERENCES]->(:Document)
(:Source)-[:OWNED_BY]->(:DID)
```

## CLI

```bash
etzhayyim source-graph scan          # 3-layer scan → JSON graph
etzhayyim source-graph violations    # violation detection + scoring
etzhayyim source-graph cypher        # Cypher MERGE statements for yata projection
etzhayyim source-graph dot           # Graphviz DOT output
```

## Implementation

| File | LOC | 責務 |
|---|---|---|
| `source_graph.go` | ~500 | Framework, L3 parser, merge, violations, scoring, CLI |
| `source_graph_ast.go` | ~380 | L2: `go/ast` + TS regex + Rust regex |
| `source_graph_meta.go` | ~200 | L1: WIT + magatama.jsonld (既存型再利用) |
| `source_graph_test.go` | ~300 | L3 tests (14 tests) |
| `source_graph_ast_test.go` | ~350 | L1+L2 tests (16 tests) |

30 tests, 0 external dependencies.
