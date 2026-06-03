# etzhayyim-project-tia App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `etzhayyim-performer-sys-etzhayyim-app-tia-seeker-r5k2m8a3`
- `tia-ports-graphql-6ffwdypt`
- `tia-systems-authenticator-nc8a92xo`
- `tia-systems-database-56lcmovj`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## Current Components

- `tia-mcp-component`
  - public MCP gateway (`/api/mcp`)
  - GraphQL + seeker dispatch
- `tia-seeker-component`
  - seeker orchestration MCP
  - targets/list + seek/run + observation/report

## MCP Endpoints (host-based)

- `https://tia.etzhayyim.com/api/mcp` (`tia-mcp-component`)
- `https://seeker.tia.etzhayyim.com/api/mcp` (`tia-seeker-component`)

詳細設計は `wasm/DESIGN.md` を参照。
