# sys-briefing-mcp-component

`etzhayyim-performer-sys-etzhayyim-app-briefing-bis87j5v` の App 版コンポーネントです。

## Endpoints

- `GET /health`, `GET /healthz`, `GET /readyz`
- `GET /status/jobs`
- `POST /jobs/briefing-run`
- `POST /events/briefing.requested`
- `POST /api/mcp`, `POST /{nanoid}/api/mcp`

## MCP tools

- `sysbriefing.list_jobs`
- `sysbriefing.enqueue_job`
- `sysbriefing.run_job`

## Persistence

- `kotodama WIT` の `briefing_jobs` Arrow table に永続化
