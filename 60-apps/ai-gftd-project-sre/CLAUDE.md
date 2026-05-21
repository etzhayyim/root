# ai-gftd-project-sre — Project Runbook

## Overview

`sre.gftd.ai` — SRE monitoring App。全 App を定期評価し、問題を各 App の Matrix AS issue room に起票する。

## Architecture

```
Performer Reminder (5 min)
  └─ health_check_all → HTTP GET /health per registered App
       └─ fail → sre_issues upsert + POST !sre-issues-{nanoid}:matrix.gftd.ai

Playwright Runner CronJob (30 min)  [Native Go Docker]
  └─ list_apps → run generic smoke tests per App
       └─ report_playwright_result → sre_issues + Matrix post

Daily Evolution (JST 02:00)
  └─ 5-agent team review: BM/PO/MK/ENG/QA in !sre-team-srej0b1x:matrix.gftd.ai
```

## Components

| Component | Path | Role |
|---|---|---|
| SRE App | `wasm/ai-gftd-wasm-sre-job-srej0b1x/` | TS Native — health checks, issue management, Matrix posting |
| Playwright Runner | `runner/` | Native Go Docker — generic Playwright smoke tests |

## SRE App (nanoid: `srej0b1x`)

**Hostname**: `sre.gftd.ai`
**Methods**:

| Method | Trigger | Description |
|---|---|---|
| `register_app` | external POST | App を監視対象に登録、Matrix issue room を作成 |
| `list_apps` | Playwright runner | 登録済み App 一覧 |
| `trigger_health_check` | manual | 指定 App の即時ヘルスチェック |
| `health_check_all` | reminder 5min | 全 App ヘルスチェック (自己スケジュール) |
| `report_playwright_result` | runner | Playwright 結果受け取り + issue 起票 |
| `list_issues` | dashboard/query | 問題一覧 |
| `ack_issue` | operator | 問題 acknowledge |
| `resolve_issue` | operator | 問題解決マーク |
| `handle_daily_evolution` | reminder daily | MANDATORY 5-agent daily review |

## Matrix Issue Room Convention

App 登録時に以下の room を作成する:
- Room alias: `!sre-issues-{app_nanoid}:matrix.gftd.ai`
- Members: `@sre:matrix.gftd.ai`, `@eng-{app_nanoid}:matrix.gftd.ai`, `@qa-{app_nanoid}:matrix.gftd.ai`
- SRE bot が `m.room.message` で issue event を投稿する

## Arrow Tables

| Table | Purpose |
|---|---|
| `sre_apps` | 監視対象 App レジストリ |
| `sre_issues` | 検出された問題 (health/playwright/seo) |
| `sre_playwright_results` | Playwright run ログ |

## Playwright Runner

- **Image**: `ghcr.io/gftdcojp/sre-playwright-runner:TAG`
- **CronJob**: `infra/k8s/sre-cronjobs.yaml` — every 30 min
- Generic smoke checks: page load, h1 visible, health endpoint 200, meta description present

## Build & Deploy

```bash
# App
cd 60-apps/ai-gftd-project-sre/wasm/ai-gftd-wasm-sre-job-srej0b1x
gftd build
gftd deploy --smoke-url https://srej0b1x.gftd.ai/health

# Playwright Runner
cd 60-apps/ai-gftd-project-sre/runner
docker build -t ghcr.io/gftdcojp/sre-playwright-runner:<tag> .
docker push ghcr.io/gftdcojp/sre-playwright-runner:<tag>
kubectl apply -f ../../infra/k8s/sre-cronjobs.yaml
```

## Registering a App for Monitoring

```bash
curl -X POST https://sre.gftd.ai/xrpc/gftd.sre.v1.SREService/register_app \
  -H "Content-Type: application/json" \
  -d '{"id":"7m8oocsn","name":"GFTD Gamers","hostname":"gamers.gftd.ai","playwright_enabled":true}'
```
