# WIT Low Backlog Decision (Issue #761)

Generated: 2026-02-24
Scope: `etzhayyim-project-kami`

## Decision

- Project: `etzhayyim-project-kami`
- Component: `wasm/kami-actor-naming-component`
- Decision: `definition cleanup (spec-only)`
- Reason:
  - `wit/world.wit` に export 定義は存在したが、実装コード (`main.go`, `go.mod`) が存在しない。
  - 現状は README ベースの設計段階であり、実運用対象ではない。

## Applied Changes

1. `wit/world.wit`
- `export naming;` を削除
- spec-only である旨のコメントを追加

2. `README.md`
- ステータスを `Spec-only` と明示
- export 再有効化の条件（実装追加、KV 連携、`go test` 成功）を追記

## Final Status

- Low 判定理由は「設計のみで実装未着手」で説明可能
- 実運用対象外として world 定義を整理済み
- 実装対象化する場合の復帰条件を文書化済み
