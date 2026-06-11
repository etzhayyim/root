# etzhayyim-project-hrse App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `hrse-components-ijwzfzfn`
- `hrse-cz9yy991`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## 現在の実装

- `hrse-components-app-component`: `hrse-components-ijwzfzfn` 向け UI components metadata companion (`/api/mcp`, `/{nanoid}/api/mcp`, `/healthz`)
- `hrse-mcp-component`: App 単体で動作する MCP facade (`/api/mcp`, `/{nanoid}/api/mcp`, `/health`)
- `hrse-ui-w7h3x9nq`: `hrse.etzhayyim.com` 向け static site component (`70-tools/etzhayyim-static-site` + embedded `static/`)

## 移行ステータス

- `hrse-components-ijwzfzfn`: implemented (`hrse-components-app-component`)
- `hrse-cz9yy991`: implemented (`hrse-mcp-component`)
- `hrse.etzhayyim.com` frontend: implemented (`hrse-ui-w7h3x9nq`)
