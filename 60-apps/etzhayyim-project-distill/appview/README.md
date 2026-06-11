# etzhayyim-project-distill App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `distill-9xgoe7e6`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## 実装済みコンポーネント

- `distill-mcp-component` (`distill-9xgoe7e6` 対応)
  - `POST /api/mcp`, `POST /{nanoid}/api/mcp`
  - 既存互換 REST: `/training/*`, `/dataset/*`, `/models*`
