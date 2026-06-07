# etzhayyim-project-briefing App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `etzhayyim-performer-sys-etzhayyim-app-briefing-bis87j5v`
- `briefing-2aqx6noz`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## 実装済みコンポーネント

- `briefing-ui-thcks5wz` に `briefing-mcp-component` を内包 (`briefing-2aqx6noz` 対応)
  - `GET/POST /api/v1/briefings`, `GET /api/v1/briefings/{id}`
  - `POST /api/mcp`, `POST /{nanoid}/api/mcp`
  - `kotodama WIT` の Arrow table へ briefing データ永続化
- `sys-briefing-mcp-component` (`etzhayyim-performer-sys-etzhayyim-app-briefing-bis87j5v` 対応)
  - `GET /status/jobs`, `POST /jobs/briefing-run`, `POST /events/briefing.requested`
  - `POST /api/mcp`, `POST /{nanoid}/api/mcp`
  - `kotodama WIT` の Arrow table へ job データ永続化
