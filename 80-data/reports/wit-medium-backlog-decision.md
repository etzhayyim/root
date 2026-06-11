# WIT Medium Backlog Decision (Issue #760)

Generated: 2026-02-24
Scope: `apqc / communities / fleamarket / news / resources`

## Decision Summary

| Project | Decision | Rationale | This turn |
|---|---|---|---|
| etzhayyim-project-apqc | 保留 (段階実装) | `world.wit` 対象が非常に多く、テンプレート重複/派生が混在。先にカタログ正規化が必要。 | 方針確定 |
| etzhayyim-project-communities | 保留 (段階実装) | 多数の community 派生コンポーネントで同種 WIT 定義が反復。先に定義統合方針が必要。 | 方針確定 |
| etzhayyim-project-fleamarket | 実装 | MCP tool 実行経路を export 実体として明示化可能。 | `main.go` をハンドラマップ化 |
| etzhayyim-project-news | 実装 | 主要 tool を export 実体として明示化可能。 | `main.go` をハンドラマップ化 |
| etzhayyim-project-resources | 定義整理 | `resources-jsonld` に未実装 export が存在。実体に合わせて world 定義を整理。 | `world.wit` から未実装 export を除去 |

## Applied Changes

### fleamarket
- File: `60-apps/etzhayyim-project-fleamarket/wasm/fleamarket-mcp-component/main.go`
- Change:
  - `fleamarketExportHandlers` を追加
  - `callTool(...)` を `handler map` 経由に変更
- Test:
  - `cd .../fleamarket-mcp-component && go test ./...` pass

### news
- File: `60-apps/etzhayyim-project-news/wasm/news-mcp-component/main.go`
- Change:
  - `newsExportHandlers` を追加
  - `callTool(...)` の主要分岐 (`list_articles/get_article/scheduler_status/ingest_article/trigger_collection`) を `handler map` 経由へ整理
- Test:
  - `cd .../news-mcp-component && go test .` pass
  - `go test ./...` は既存生成コードの重複(`gen/wasi/*` の再定義)で失敗

### resources
- File: `60-apps/etzhayyim-project-resources/wasm/components/resources-jsonld-n2p4h9xk/wit/world.wit`
- Change:
  - 未実装だった以下 export を削除
    - `crawler-crawl-job`
    - `crawler-crawl-page`
    - `crawler-website-summary`
    - `quickwit-entity-index`
  - `etzhayyim:platform/etzhayyim-mcp` include のみ維持
- Test:
  - `cd .../resources-jsonld-n2p4h9xk && go test ./...` pass

## Next Slice (apqc / communities)

1. `world.wit` を重複クラスタ単位で整理（代表1件 + 派生N件）
2. `main.go` を持つコンポーネントから優先して `import/export` 実装有無を判定
3. `未実装 import` は
   - 実装予定あり: runtime 呼び出し追加
   - 実装予定なし: world から除去（もしくは deprecated 明示）
