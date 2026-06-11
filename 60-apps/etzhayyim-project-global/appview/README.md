# etzhayyim-project-global App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `etzhayyim-performer-sys-etzhayyim-app-resources-py0fvqwk`
- `global-app-r4k7m2x9`

## 実装済み wasm components

- `global-ui-w5n8p3q6`（以前別々だった MCP / Resources App を 1 コンポーネントに統合）

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。
