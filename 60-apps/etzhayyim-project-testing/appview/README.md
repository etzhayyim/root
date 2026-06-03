# etzhayyim-project-testing App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `etzhayyim-performer-svc-fixture-manager-t7b6v8m1`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## 実装済みコンポーネント

- `fixture-manager-mcp-component` (`etzhayyim-performer-svc-fixture-manager-t7b6v8m1` 対応)
  - `dashboard/list/get/create` 機能を HTTP + MCP で提供
  - `POST /api/mcp`, `POST /{nanoid}/api/mcp`
  - データは `wasi:keyvalue/store` へ永続化
