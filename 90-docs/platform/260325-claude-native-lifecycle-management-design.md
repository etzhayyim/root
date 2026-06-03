---
id: 260325-claude-native-lifecycle-management
title: "Claude-Native Lifecycle Management — Delete Over Annotate"
status: active
doc_type: adr
topic: lifecycle-management
authoritative: true
last_verified: 2026-03-25
authoritative_for:
  - lifecycle management for code artifacts
  - deprecated/legacy/removed symbol handling
  - CLAUDE.md inventory elimination policy
  - symbol graph and structural validation
related:
  - docs-claude
supersedes:
  - CLAUDE.dead-services.md (flat list → structural enforcement)
superseded_by: []
---

# Claude-Native Lifecycle Management — Delete Over Annotate

## Goal

LLM (Claude) が stale な定義名・関数名・lexicon を参照するコードを生成することを構造的に防止する。annotation ではなく削除と構造検証で実現する。

## Decision

### P1. Delete Over Annotate

deprecated/removed な artifact は **コードから削除する**。git に履歴がある。

`@lifecycle:deprecated` marker を書くのは Shannon 違反: Claude の context window に「使うな」という token を載せることは entropy ≈ 0。Claude にとっての最適解は、存在しないものを見せないこと。

```
# Shannon 違反 (token 消費して「使うな」と伝える)
// @lifecycle:deprecated replaced_by=ComAtprotoRepoCreateRecord
type WprotoChannel struct { ... }

# Shannon 最適 (0 token。Claude は WprotoChannel を知らない)
(削除済み。git log -S WprotoChannel で参照可能)
```

`CLAUDE.dead-services.md` も同様。Claude が session 開始時に読む = 「使うな」リストを暗記させる = hallucination の seed。削除対象。

**禁止ルールのみ残す**: `CLAUDE.dead-services.md` のうち **禁止パターン** (magic values, 禁止 API) は行動ルールであり削除しない。artifact 一覧 (除去済みサービス・crate) は削除する。

### P2. Symbol Graph as Single Source of Truth

名前変更問題の根本: Claude はテキストを読む。テキストは stale になる。

AST/symbol graph を生成し、Claude が「今有効な名前」を構造的に取得する。

```bash
etzhayyim symbol-graph --format json
```

```json
{
  "wit": {
    "etzhayyim:yata/yata@1.0.0": {
      "functions": ["g", "g-exec"],
      "types": ["cypher-result", "query-error"]
    }
  },
  "xrpc": {
    "com.etzhayyim.yoro.feed.get-timeline": {
      "method": "GET",
      "handler": "50-infra/cloudflare/workers/atproto/src/pds-handlers-feed.ts:128"
    }
  },
  "go_exports": {
    "20-actors/magatama/magatama-guest-go": {
      "types": ["App", "HandleFunc", "ServeFunc"],
      "functions": ["NewApp", "Invoke", "Serve"]
    }
  }
}
```

symbol-graph に存在しない名前は使わない。情報の不在が制約になる。

### P3. Lexicon Registry = Valid Surface

WIT が Single Source。`etzhayyim lexicon-list` が今有効な NSID 全一覧を返す。手書き禁止。

```bash
etzhayyim lexicon-list --format json
```

deprecated な lexicon は WIT から削除 → `lexicon-list` に出ない → Claude は知らない → 使わない。

### P4. Lefthook Gate (Push-Time Structural Validation)

Claude が生成したコードに stale name が混入しても、push 前に catch。

```yaml
# lefthook.yml
pre-push:
  commands:
    symbol-validate:
      run: etzhayyim symbol-validate {push_files}
```

`etzhayyim symbol-validate` の処理:

1. 変更ファイルから import/参照シンボルを AST parse で抽出
2. symbol-graph の有効 exports と照合
3. 不一致 = error (削除済み/rename 済みシンボルへの参照)

```
$ etzhayyim symbol-validate main.go
ERROR: main.go:15 - WprotoChannel is not in symbol graph
  Suggestion: ComAtprotoRepoCreateRecord (50-infra/cloudflare/workers/atproto/src/...)
```

Claude への feedback loop: push reject → Claude がエラーを読む → 正しい名前に修正。annotation 不要、構造が制約する。

### P5. CLAUDE.md = Behavioral Rules Only (Zero Inventory)

CLAUDE.md には **判断基準** だけ書く。一覧は全て tool 出力に委譲。

```markdown
# BAD (status table = stale になる inventory)
| Component | Status | Details |
| CSR Container | [PRODUCTION] | ... |
| LSMGraph | [DEPRECATED] | replaced by Arrow |

# GOOD (tool へのポインタ)
## Component Status
Run: `etzhayyim symbol-graph --package yata`
```

CLAUDE.md に残すもの:
- 禁止ルール (「REST 新規追加禁止」「base64 禁止」)
- 設計判断 (「T1/T2/T3 の使い分け」)
- tool へのポインタ (「status は `etzhayyim symbol-graph` で確認」)

残さないもの:
- artifact 一覧 (symbol-graph が権威)
- status table (コード自体が権威)
- dead services list (削除済み = 存在しない)

## Architecture

```
     Claude context window
     ┌──────────────────────────┐
     │ CLAUDE.md (rules only)   │  最小 token
     │ + source code (Read)     │  必要分だけ
     └────────┬─────────────────┘
              │ need valid names?
              ▼
     etzhayyim symbol-graph (AST)      今の真実
     etzhayyim lexicon-list (WIT)      有効 API
              │
              │ generates code
              ▼
     lefthook pre-push             gate
     etzhayyim symbol-validate          stale 参照 reject
              │
              ▼
         git push OK
```

## Shannon Analysis

| 方式 | Token/session | Entropy | 問題 |
|---|---|---|---|
| 従来 (marker + dead-services + status table) | ~2000 | ≈ 0 (「使うな」情報) | stale、hallucination seed |
| 本設計 (削除 + tool 照会) | 0 常時 + 必要時 tool call | max (全て actionable) | tool 実装が必要 |

## `etzhayyim shannon` Integration

`symbol-graph` / `symbol-validate` / `lexicon-list` は独立コマンドではなく **`etzhayyim shannon` の新 check `stale_symbol_entropy`** として統合する。

既存 `etzhayyim shannon` (8 checks, weighted average):

| Check | Weight | 内容 |
|---|---|---|
| `claude_md_duplication` | 0.25 | CLAUDE.md 間のルール重複 |
| `code_clone_cross` | 0.15 | Cross-project code clone |
| `collection_write_fan` | 0.15 | 同一 collection への multi-app write |
| `wit_type_duplication` | 0.10 | WIT type 重複 |
| `config_redundancy` | 0.10 | wrangler.jsonc config 重複 |
| `dead_code_entropy` | 0.10 | 空関数/stub handler |
| `doc_code_drift` | 0.10 | evidence link staleness |
| `rust_duplication` | 0.05 | Rust function body hash 重複 |

**追加:**

| Check | Weight | 内容 |
|---|---|---|
| **`stale_symbol_entropy`** | **0.10** | WIT 不在 binding + 削除済みシンボル参照 + CLAUDE.md strikethrough |

`stale_symbol_entropy` 内部:
1. `00-contracts/wit/deps/` から有効 WIT interface/function を収集 (= lexicon-list)
2. `//go:wasmimport` directive と照合、不一致 = violation (= symbol-validate)
3. `code_quality.go` prohibited patterns をソース全体で grep
4. CLAUDE.md `~~strikethrough~~` を検出 (除去済み artifact の残存)

**Lefthook 連動:**
```yaml
symbol-validate:
  run: etzhayyim shannon scan --check stale_symbol_entropy --fail-on-violation
```

**実装先:** `70-tools/etzhayyim/shannon.go` に `shCheckStaleSymbolEntropy()` を追加。`source_graph_ast.go` の AST extraction を再利用。

## Migration Status

| Step | Status |
|---|---|
| `CLAUDE.dead-services.md` → 禁止パターンのみに縮小 | Done |
| CLAUDE.md status table 削除 (yata, root) | Done |
| CLAUDE.md strikethrough 削除 (7 files) | Done |
| dead code 削除 (WprotoChannel, rpc/remote-call) | Done |
| `lefthook.yml` に `symbol-validate` 追加 | Done |
| `etzhayyim shannon` に `stale_symbol_entropy` check 実装 | TODO |
