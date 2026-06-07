# YORO Actor Quality Process Mining - 2026-04-29

## Scope

Target process: `com.etzhayyim.apps.yoro.actorQualityEnrich`

Observed window: last 12 hours from `2026-04-29T07:11:38Z`.

The production runtime currently exposes only part of the process as event data. BPMN/OCEL activity tables exist, but actorQuality task-level events were not emitted during this rollout. The practical process mining view therefore joins:

- PDS XRPC tail events for workflow start acceptance
- `app.bsky.actor.profile` repo records for profile enrichment output
- `app.bsky.feed.post` repo records with `murakumo-quality-seed-*` rkeys for seed-post output
- AppView spot checks for public visibility

## Observed Process Model

1. `candidate.selected`
2. `xrpc.workflow.start.accepted`
3. `repo.profile.self.written`
4. `repo.seedPost.written`
5. `appview.profile.visible`

The intended BPMN model is still:

1. `yoro.actorQuality.inspect`
2. `yoro.actorQuality.enrichProfile`
3. `yoro.actorQuality.ensureSeedPost`

Task-level conformance cannot be measured yet because no actorQuality rows were present in `vertex_bpmn_activity_event`, `vertex_bpmn_instance`, `vertex_bpmn_signal_log`, or `vertex_ocel_event`.

## Runtime Metrics

- PDS accepted actorQuality XRPC events: `49`
- PDS outcomes: `ok=49`
- PDS window: `2026-04-29T05:07:47.852Z` to `2026-04-29T07:02:09.937Z`
- PDS wall time: min `232ms`, p50 `443ms`, p95 `19561ms`, max `19949ms`, avg `2496.8ms`
- Reconstructed artifact cases: `37`
- Reconstructed complete cases with profile and seed post: `37`

## Artifact Variants

| Source hint | Cases | Profile | Seed post | Window |
| --- | ---: | ---: | ---: | --- |
| controlled rollout batch 25 phase 2026-04-29 | 25 | 25 | 25 | 2026-04-29T07:01:44Z..2026-04-29T07:02:10Z |
| controlled rollout batch phase 2026-04-29 | 9 | 9 | 9 | 2026-04-29T07:00:25Z..2026-04-29T07:00:37Z |
| pilot actor quality dedicated appview fixed 2026-04-29 | 1 | 1 | 1 | 2026-04-29T06:56:59Z |
| pilot actor quality live backfill 2026-04-29 | 1 | 1 | 1 | 2026-04-29T06:35:09Z |
| manual SEO quality repair 2026-04-29 | 1 | 1 | 1 | 2026-04-29T05:23:16Z |

## Findings

- The current dedicated Zeebe worker path is functionally completing cases. The latest 25-case batch produced 25 profile records and 25 seed posts within roughly 26 seconds.
- The observed XRPC count is higher than reconstructed artifact cases because it includes dry runs, earlier failed/partial attempts, and workflow starts that did not necessarily produce a seed artifact in the sampled recent records.
- The process has a real observability gap: task-level BPMN/OCEL mining is not possible yet for actorQuality because activity events are absent.
- Previously observed bottlenecks are confirmed as process risks: generic all-task Zeebe activation caused backpressure, AppView selected stale profile records before the `rkey='self'` ordering fix, and deployment image drift can replace the dedicated quality worker.

## Next Control Point

Implemented next step: lightweight event emission was added to the pod worker path in `kotodama.primitives.yoro_social`, not to the Cloudflare Worker path.

Cloudflare Worker remains responsible for ingress/process-start visibility:

- PDS XRPC route accepts `com.etzhayyim.apps.yoro.actorQualityEnrich`
- PDS tail logs show request outcome and wall time

The pod worker is responsible for task-level process mining:

- `actorQuality.inspect.started/completed`
- `actorQuality.enrichProfile.started/completed`
- `actorQuality.ensureSeedPost.started/completed`
- common fields: `caseId`, `actorDid`, `instanceKey`, `taskType`, `sourceHint`, `dryRun`, `status`, `elapsedMs`, `errorCode`

Deployment status:

- image: `ghcr.io/etzhayyim/kotodama:yoro-actor-quality-process-mining-6209801e7cb5-20260429072810-amd64`
- Kubernetes deployment: `yoro-actors/yoro-actor-zeebe-worker`
- worker profile: `ZEEBE_WORKER_PROFILE=yoro_actor_quality`
- rollout: `1/1` ready

Smoke result:

- dry-run public XRPC returned `200`, `asyncStarted=true`, `instanceKey=6755399442751375`
- `vertex_bpmn_activity_event` received `yoro.actorQuality.inspect.started` and `yoro.actorQuality.inspect.completed`
- process mining script now reports `bpmn_activity > 0`

Use the mining script as the rollout gate. It now reports both artifact completion and task-level BPMN activity counts:

```bash
DATABASE_URL='REDACTED_USE_DATABASE_URL_ENV' \
  node 70-tools/scripts/yoro/actor-quality-process-mining.mjs --since-hours=12 --limit=500 --json
```

Recommended next rollout gate: run `--limit=100 --live --sleep-ms=750 --source-hint="controlled rollout batch 100 phase 2026-04-29"` and require:

- PDS `ok` rate remains 100%
- reconstructed complete cases increase by 100
- AppView spot checks show `description` and `postsCount >= 1`
- worker image remains `ghcr.io/etzhayyim/kotodama:yoro-actor-quality-dedicated-664fc09d87dd-20260429063130-amd64`

## Controlled Batch 100 Result

Executed with:

```bash
DATABASE_URL='REDACTED_USE_DATABASE_URL_ENV' \
  node 70-tools/scripts/yoro/actor-quality-backfill.mjs \
  --live \
  --limit=100 \
  --sleep-ms=750 \
  --source-hint='controlled rollout batch 100 process mining 2026-04-29'
```

Result:

- candidates after dedupe: `84`
- XRPC workflow starts: `84`
- failures: `0`
- seed posts written: `84`
- complete artifact cases for this source hint: `84`
- artifact window: `2026-04-29T07:54:05Z..2026-04-29T07:55:29Z`
- deployment image during run: `ghcr.io/etzhayyim/kotodama:yoro-actor-quality-process-mining-6209801e7cb5-20260429072810-amd64`

Task-level BPMN activity rows for this source hint:

| Activity | Started | Completed |
| --- | ---: | ---: |
| `yoro.actorQuality.inspect` | 168 | 168 |
| `yoro.actorQuality.enrichProfile` | 84 | 84 |
| `yoro.actorQuality.ensureSeedPost` | 84 | 84 |

Spot-checked public AppView profiles:

| Actor | HTTP | Description | Posts |
| --- | ---: | --- | ---: |
| `did:web:uqpel6i6.etzhayyim.com:geo:iata-airport:ICN` | 200 | yes | 1 |
| `did:web:uqpel6i6.etzhayyim.com:geo:icao-airport:KJFK` | 200 | yes | 1 |
| `did:web:uqpel6i6.etzhayyim.com:geo:iso3166-1:cr` | 200 | yes | 1 |
| `did:web:uqpel6i6.etzhayyim.com:geo:iso3166-1:dk` | 200 | yes | 1 |
| `did:web:uqpel6i6.etzhayyim.com:geo:unlocode:EG` | 200 | yes | 1 |

Follow-up finding: `inspect` is observed twice per case while `enrichProfile` and `ensureSeedPost` are once per case. Treat this as the next BPMN optimization target before increasing concurrency.
