# etzhayyim-project-news App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `etzhayyim-news-r5wvpkot`
- `news-mcp-gy9z0qb7`
- `news-ui-f8n3k2q1`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。
- `news-mcp-component` は `news-ui-hytt1wm3` 内 `components/news-mcp-component` に統合済み。
