# AGENTS (60-apps/etzhayyim-project-business-manager)

- `business-manager` component の変更は `70-tools/performer` ベースで実装する。
- API は `wasi:http/incoming-handler` + `performer.Adapter` のみに限定し、
  フロントエンド固定 API を追加しない。
- 不要な設定/未使用フィールド（dead code）を増やさない。
- `default` namespace へ作成しない。
- ステートは performer の KV スコープ（`ScopeOrg`）で管理し、
  新規実装は `main.go` に閉じて保守する。
