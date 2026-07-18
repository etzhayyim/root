> **DEPRECATED**: Actor implementation is owned by
> `orgs/etzhayyim/com-etzhayyim-business-manager` with EDN canonical metadata.
> This project wasm/*/src/app.ts is retained as T3 fallback only.

# CLAUDE.md (60-apps/etzhayyim-project-business-manager)

このプロジェクトの `business-manager` コンポーネントは `70-tools/performer` を前提にした API-only App 実装。

## 参照する上位ルール
- `60-apps/CLAUDE.md` の方針（namespace / App / MCP / Connect）

- `40-engine/kotoba/crates/kotoba-kotodama/CLAUDE.md` の runtime 運用

## business-manager 固有メモ
- 実行中ランタイム: `businessManagerRuntime` + `businessManagerAdapter`
- 外部公開: `wasi:http/incoming-handler` 経由 + `/api/mcp`（または `/health`）
- 主要メソッド:
  - `evaluate`
  - `run_now`
  - `get_status`
  - `health`
- ステートキー: `business-manager-state`（`ScopeOrg`）
- 運用方針: 不要なスタブ/デッドコードは残さず、機能をメソッドに寄せる

## 開発メモ
- `RuntimeConfig` の設定は既定値のみ利用し、未使用設定の放置を避ける。
- `default` namespace は使用しない。
- コンポーネントの namespace は `kotodama-runtime` 固定。
