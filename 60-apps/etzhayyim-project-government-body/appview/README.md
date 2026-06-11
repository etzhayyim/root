# etzhayyim-project-government-body App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `gov-67d08614`
- `gov-ui-84008ada`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## 実装済みコンポーネント

- `gov-mcp-component` (`gov-67d08614` 対応)
  - `GET /api/v1/cofog`, `/api/v1/citizens`, `/api/v1/services`, `/api/v1/treasury`
  - `POST /xrpc`, `POST /{nanoid}/xrpc`
  - `wasi:keyvalue/store` で gov 状態を永続化
- `gov-ui-mcp-component` (`gov-ui-84008ada` 対応)
  - `GET|PUT /api/v1/ui/config`, `GET /api/v1/ui/navigation`
  - `POST /xrpc`, `POST /{nanoid}/xrpc`
  - `GET /...` で静的フロント (`svelte/build`) を配信
  - `wasi:keyvalue/store` で UI 状態を永続化

- `gov-planning-mcp-component` (resource planning / scheduling / gitstate)
  - `GET /api/v1/planning/resource`, `/api/v1/planning/schedule`, `/api/v1/planning/gitstate`
  - `POST /api/v1/planning/publish`, `POST /xrpc`
  - `wasi:keyvalue/store` で planning state を永続化
