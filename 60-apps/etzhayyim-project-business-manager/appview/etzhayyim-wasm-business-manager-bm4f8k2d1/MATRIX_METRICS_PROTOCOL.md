# BM Metrics Matrix Protocol

## Goal

`bm.etzhayyim.com` の app metrics 評価結果を Matrix room に報告し、確認、承認、異常時エスカレーションを Matrix protocol 上で完結させる。

## Transport

- homeserver: `https://matrix.etzhayyim.com`
- client: `70-tools/performer.NewMatrixClientFromEnv()`
- delivery: Matrix room event
- correlation: `request_event_id`, `run_id`, `domain`, `captured_at`

## Rooms

- control room:
  `!bm-metrics-control:matrix.etzhayyim.com`
  BM の定期報告、障害、再実行要求
- app rooms:
  - `!bm-shinshi:matrix.etzhayyim.com`
  - `!bm-news:matrix.etzhayyim.com`
  - `!bm-games:matrix.etzhayyim.com`
  - `!bm-gamers:matrix.etzhayyim.com`
  - `!bm-pachinko:matrix.etzhayyim.com`
- escalation room:
  `!bm-metrics-escalation:matrix.etzhayyim.com`

## Event Types

- report:
  `org.etzhayyim.metrics.report`
- alert:
  `org.etzhayyim.metrics.alert`
- ack:
  `org.etzhayyim.metrics.ack`
- verify request:
  `org.etzhayyim.metrics.verify`
- verify result:
  `org.etzhayyim.metrics.verify.result`
- rollout gate:
  `org.etzhayyim.metrics.gate`

## Report Event

```json
{
  "app": "bm",
  "domain": "news",
  "run_id": "bm-1773288424192244002",
  "source": "https://bm.etzhayyim.com",
  "report_type": "scheduled",
  "score": 81.4,
  "risk_level": "medium",
  "metrics_url": "https://news.etzhayyim.com/metrics",
  "health_url": "https://news.etzhayyim.com/health",
  "captured_at": "2026-03-12T04:07:04Z",
  "otel_metrics": {
    "request_count": 1244,
    "error_count": 2,
    "active_requests": 0,
    "avg_duration_seconds": 0.041,
    "uptime_seconds": 6432
  },
  "content_stats": {
    "metrics": [
      {"key":"articles","value":421},
      {"key":"active_feeds","value":6},
      {"key":"editor_tracks","value":3}
    ]
  },
  "kpis": [
    {"name":"traffic_health","status":"healthy","score":88},
    {"name":"content_coverage","status":"warning","score":66}
  ],
  "diagnostics": {},
  "requires_ack": true
}
```

## Verify Flow

1. BM posts `org.etzhayyim.metrics.report`
2. reviewer bot or operator posts `org.etzhayyim.metrics.verify`
3. verifier fetches `health` and `metrics`
4. verifier posts `org.etzhayyim.metrics.verify.result`
5. operator posts `org.etzhayyim.metrics.ack`

## Ack Event

```json
{
  "app": "bm",
  "domain": "news",
  "run_id": "bm-1773288424192244002",
  "request_event_id": "$metrics-report",
  "ack_status": "accepted",
  "confirmed_by": "@ops:matrix.etzhayyim.com",
  "confirmed_at": "2026-03-12T04:09:10Z",
  "note": "public metrics and health verified"
}
```

## Alert Rules

- `health != 200`
- `/metrics` fetch failed
- `error_count > 0`
- `score < 65`
- `risk_level == high`
- `diagnostics` not empty

On alert, BM posts `org.etzhayyim.metrics.alert` to control room and app room.
If unresolved after SLA, mirror to escalation room.

## Implementation Notes

- BM should post Matrix events after each `Evaluate`.
- Use one room per app so history stays app-scoped.
- Use the control room for cross-app summaries and daily digest.
- Do not proxy metrics through `performer-framework`; fetch from the public app route or direct service route.
- If BM runtime outbound remains unstable, emit reports from a lightweight verifier job instead of BM itself.
