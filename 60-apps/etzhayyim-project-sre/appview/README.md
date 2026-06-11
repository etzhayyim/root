# etzhayyim-project-sre App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `etzhayyim-performer-org-etzhayyim-sys-toolbar-7w8z9k2l`
- `etzhayyim-performer-sys-activity--monitor`
- `etzhayyim-performer-sys-sre-patrol-ol-agent`
- `sre-5q1z8oag`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## `sre-mcp-component` Matrix app user

- `sre-mcp-component` は `@sre:etzhayyim.com` を既定の Matrix app user として扱う。
- 実 user ID は homeserver 上では `@sre:matrix.etzhayyim.com` を使う。
- issue 投稿は `CreateIssue` method から `m.room.message` を Matrix room へ送る。
- 必須 env:
  - `MATRIX_BASE_URL`
  - `SRE_MATRIX_ISSUE_ROOM_ID`
  - `SRE_MATRIX_PASSWORD`
- 任意 env:
  - `SRE_MATRIX_USER_ID` (default: `@sre:matrix.etzhayyim.com`)
  - `SRE_MATRIX_LOGIN_USER` (default: `sre`)
  - `SRE_MATRIX_DISPLAY_NAME` (default: `sre.etzhayyim.com`)
  - `SRE_MATRIX_ACCESS_TOKEN` or `MATRIX_ACCESS_TOKEN` if token pinning is preferred
