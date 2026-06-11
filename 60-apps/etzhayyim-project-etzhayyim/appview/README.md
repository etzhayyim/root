# etzhayyim-project-etzhayyim App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `news-scheduler-go`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## 実装済みコンポーネント

- `news-scheduler-mcp-component` (`news-scheduler-go` 対応)
  - `POST /api/mcp`, `POST /{route-id}/api/mcp`
  - 既存互換 REST: `/jobs/news-*`
