# Houbun Ingest: BPMN + Zeebe + Python Worker Design

**Status**: proposed implementation design — 2026-04-25
**Scope**: `houbun.etzhayyim.com` / `contracts.etzhayyim.com` law, ordinance, constitution, treaty ingest.

## Goal

Turn the current operator-driven law ingest into a durable Zeebe workflow.

Current state:

- `70-tools/scripts/houbun_live_ingest.py` can write directly to Kotoba/Datomic.
- Kotoba/Datomic has partial `houbun` data: JP statutes/articles, UN treaty metadata,
  and constitution/social-contract metadata.
- `hanrei` cron currently creates collection jobs, but it does not own the
  authoritative `vertex_houbun_*` write path.

Target state:

- Cron starts BPMN instances only.
- Zeebe owns retry, backoff, partitioning, pause/resume, and incidents.
- Python workers own source fetching, normalization, deterministic writes, and
  visibility verification.
- `vertex_houbun_*` remains the canonical law graph; generic ingest tables only
  track runs/cursors/artifacts.

## Runtime Topology

```text
K8s CronJob / MCP ingest.start / dispatcher XRPC
        |
        v
Zeebe process: houbun_source_delta or houbun_world_backfill
        |
        v
Python Deployment: houbun-ingest-worker
        |
        +-- laws.e-gov.go.jp API v2
        +-- Constitute Project
        +-- Wikidata SPARQL / UNTC
        +-- GovInfo CFR bulk XML
        +-- EUR-Lex/CELLAR
        +-- future municipal ordinance sources
        |
        v
Kotoba/Datomic:
  vertex_houbun_statute
  vertex_houbun_article
  edge_houbun_statute_article
  vertex_houbun_treaty
  vertex_contracts_social_contract
  vertex_ingest_run / cursor / artifact
```

## Process Families

| Process ID | Purpose | Schedule |
|---|---|---|
| `houbun_egov_jpn_delta` | JP e-Gov law list + law body delta | daily or weekly |
| `houbun_constitution_delta` | Constitute Project active constitution metadata | weekly |
| `houbun_treaty_untc_delta` | Wikidata P9966 / UNTC treaty metadata | weekly |
| `houbun_cfr_delta` | US CFR title package ingest | monthly |
| `houbun_eurlex_seed` | explicit CELEX seed/backfill | manual/batch |
| `houbun_world_backfill` | controlled multi-source backfill by jurisdiction/source | manual |
| `houbun_municipal_jpn_backfill` | Japanese ordinances by municipality | later, manual first |

Do not combine all sources into one giant process. Each source has different
rate limits, cursor semantics, and parser failure modes.

## BPMN Shape

All source processes use the same control skeleton:

```text
start
  -> create_run
  -> health_gate
  -> plan_shards
  -> multi-instance shard subprocess
       -> acquire_cursor
       -> fetch_source
       -> persist_raw_artifact
       -> normalize
       -> write_graph
       -> verify_visibility
       -> advance_cursor
  -> refresh_coverage
  -> complete_run
end
```

Failure policy:

- `health_gate`: retry 3x, then fail process before any cursor is locked.
- `fetch_source`: retry with source-specific backoff; mark source `degraded`
  after bounded retries.
- `normalize`: fail fast to incident; parser drift must be visible.
- `write_graph`: retry only after a new health gate passes.
- `verify_visibility`: retry with delay; do not advance cursor on failed verify.
- `advance_cursor`: idempotent update keyed by `(family, source_id, shard_key)`.

## Zeebe Task Types

Use source-neutral task types for orchestration and source-specific handlers
inside Python. The worker dispatches by `source_id`.

| Zeebe task type | Input | Output | Notes |
|---|---|---|---|
| `houbun.createRun` | `run_id, source_id, mode, input_json` | `run_vertex_id` | Inserts `vertex_ingest_run`. |
| `houbun.healthGate` | `rw_url, source_id` | `rw_ok` | Blocks bulk writes if Kotoba/Datomic is unhealthy. |
| `houbun.planShards` | `source_id, mode, range, limit` | `shards[]` | Creates deterministic shard list. |
| `houbun.acquireCursor` | `source_id, shard_key, run_id` | `cursor_value` | Lock with TTL. |
| `houbun.fetchSource` | `source_id, shard_key, cursor_value` | `artifact_uri, source_count` | Raw payload goes to B2 or local artifact row. |
| `houbun.normalize` | `source_id, artifact_uri` | `normalized_uri, row_counts` | Parser output is typed rows. |
| `houbun.writeGraph` | `source_id, normalized_uri` | `records_written` | Deterministic upsert/insert-ignore. |
| `houbun.verifyVisibility` | `source_id, expected_counts` | `verified_counts` | Read-after-write checks. |
| `houbun.advanceCursor` | `source_id, shard_key, new_cursor` | `cursor_updated` | Runs only after verify. |
| `houbun.refreshCoverage` | `run_id, source_id` | `coverage_json` | Updates/requests coverage projections. |
| `houbun.completeRun` | `run_id, status, output_json` | `ok` | Final audit row update. |

## Source Config

Source behavior is data-driven:

```yaml
sources:
  egov-jpn:
    jurisdiction: jpn
    language: ja
    license: CC-BY-4.0
    planner: egov_law_list
    fetcher: egov_law_body
    normalizer: egov_v2_json
    writeTargets:
      - vertex_houbun_statute
      - vertex_houbun_article
      - edge_houbun_statute_article
    defaultLimit: 100
    maxArticlesPerLaw: 500
    rateLimit:
      sleepSeconds: 0.15

  constitute-active:
    jurisdiction: global
    language: en
    planner: constitute_list
    fetcher: constitute_metadata
    normalizer: social_contract_constitution
    writeTargets:
      - vertex_contracts_social_contract

  wikidata-untc:
    jurisdiction: international
    language: en
    planner: sparql_offset
    fetcher: wikidata_sparql
    normalizer: untc_treaty
    writeTargets:
      - vertex_houbun_treaty
      - vertex_contracts_social_contract
```

## BPMN XML Skeleton

Keep the real BPMN under a domain folder, for example:

`etzhayyim-root/60-apps/etzhayyim-project-houbun/bpmn/houbun-source-delta.bpmn`

The source-neutral skeleton should look like:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  id="defs_houbun_source_delta"
  targetNamespace="https://etzhayyim.com/bpmn/houbun">

  <bpmn:process id="houbun_source_delta" name="Houbun Source Delta" isExecutable="true">
    <bpmn:startEvent id="start" name="Start">
      <bpmn:outgoing>flow_create_run</bpmn:outgoing>
    </bpmn:startEvent>

    <bpmn:serviceTask id="create_run" name="Create run">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="houbun.createRun" retries="3" />
      </bpmn:extensionElements>
      <bpmn:incoming>flow_create_run</bpmn:incoming>
      <bpmn:outgoing>flow_health_gate</bpmn:outgoing>
    </bpmn:serviceTask>

    <bpmn:serviceTask id="health_gate" name="Kotoba/Datomic health gate">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="houbun.healthGate" retries="3" />
      </bpmn:extensionElements>
      <bpmn:incoming>flow_health_gate</bpmn:incoming>
      <bpmn:outgoing>flow_plan_shards</bpmn:outgoing>
    </bpmn:serviceTask>

    <bpmn:serviceTask id="plan_shards" name="Plan shards">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="houbun.planShards" retries="3" />
      </bpmn:extensionElements>
      <bpmn:incoming>flow_plan_shards</bpmn:incoming>
      <bpmn:outgoing>flow_shard_loop</bpmn:outgoing>
    </bpmn:serviceTask>

    <bpmn:subProcess id="shard_loop" name="Shard loop">
      <bpmn:extensionElements>
        <zeebe:loopCharacteristics inputCollection="=shards" inputElement="shard" />
      </bpmn:extensionElements>
      <bpmn:incoming>flow_shard_loop</bpmn:incoming>
      <bpmn:outgoing>flow_refresh_coverage</bpmn:outgoing>

      <bpmn:startEvent id="shard_start">
        <bpmn:outgoing>flow_acquire_cursor</bpmn:outgoing>
      </bpmn:startEvent>
      <bpmn:serviceTask id="acquire_cursor" name="Acquire cursor">
        <bpmn:extensionElements><zeebe:taskDefinition type="houbun.acquireCursor" retries="5" /></bpmn:extensionElements>
        <bpmn:incoming>flow_acquire_cursor</bpmn:incoming><bpmn:outgoing>flow_fetch</bpmn:outgoing>
      </bpmn:serviceTask>
      <bpmn:serviceTask id="fetch_source" name="Fetch source">
        <bpmn:extensionElements><zeebe:taskDefinition type="houbun.fetchSource" retries="5" /></bpmn:extensionElements>
        <bpmn:incoming>flow_fetch</bpmn:incoming><bpmn:outgoing>flow_normalize</bpmn:outgoing>
      </bpmn:serviceTask>
      <bpmn:serviceTask id="normalize" name="Normalize">
        <bpmn:extensionElements><zeebe:taskDefinition type="houbun.normalize" retries="1" /></bpmn:extensionElements>
        <bpmn:incoming>flow_normalize</bpmn:incoming><bpmn:outgoing>flow_write</bpmn:outgoing>
      </bpmn:serviceTask>
      <bpmn:serviceTask id="write_graph" name="Write graph">
        <bpmn:extensionElements><zeebe:taskDefinition type="houbun.writeGraph" retries="3" /></bpmn:extensionElements>
        <bpmn:incoming>flow_write</bpmn:incoming><bpmn:outgoing>flow_verify</bpmn:outgoing>
      </bpmn:serviceTask>
      <bpmn:serviceTask id="verify_visibility" name="Verify visibility">
        <bpmn:extensionElements><zeebe:taskDefinition type="houbun.verifyVisibility" retries="5" /></bpmn:extensionElements>
        <bpmn:incoming>flow_verify</bpmn:incoming><bpmn:outgoing>flow_advance</bpmn:outgoing>
      </bpmn:serviceTask>
      <bpmn:serviceTask id="advance_cursor" name="Advance cursor">
        <bpmn:extensionElements><zeebe:taskDefinition type="houbun.advanceCursor" retries="3" /></bpmn:extensionElements>
        <bpmn:incoming>flow_advance</bpmn:incoming><bpmn:outgoing>flow_shard_end</bpmn:outgoing>
      </bpmn:serviceTask>
      <bpmn:endEvent id="shard_end"><bpmn:incoming>flow_shard_end</bpmn:incoming></bpmn:endEvent>
    </bpmn:subProcess>

    <bpmn:serviceTask id="refresh_coverage" name="Refresh coverage">
      <bpmn:extensionElements><zeebe:taskDefinition type="houbun.refreshCoverage" retries="3" /></bpmn:extensionElements>
      <bpmn:incoming>flow_refresh_coverage</bpmn:incoming><bpmn:outgoing>flow_complete</bpmn:outgoing>
    </bpmn:serviceTask>

    <bpmn:serviceTask id="complete_run" name="Complete run">
      <bpmn:extensionElements><zeebe:taskDefinition type="houbun.completeRun" retries="3" /></bpmn:extensionElements>
      <bpmn:incoming>flow_complete</bpmn:incoming><bpmn:outgoing>flow_end</bpmn:outgoing>
    </bpmn:serviceTask>

    <bpmn:endEvent id="end" name="End"><bpmn:incoming>flow_end</bpmn:incoming></bpmn:endEvent>

    <bpmn:sequenceFlow id="flow_create_run" sourceRef="start" targetRef="create_run" />
    <bpmn:sequenceFlow id="flow_health_gate" sourceRef="create_run" targetRef="health_gate" />
    <bpmn:sequenceFlow id="flow_plan_shards" sourceRef="health_gate" targetRef="plan_shards" />
    <bpmn:sequenceFlow id="flow_shard_loop" sourceRef="plan_shards" targetRef="shard_loop" />
    <bpmn:sequenceFlow id="flow_refresh_coverage" sourceRef="shard_loop" targetRef="refresh_coverage" />
    <bpmn:sequenceFlow id="flow_complete" sourceRef="refresh_coverage" targetRef="complete_run" />
    <bpmn:sequenceFlow id="flow_end" sourceRef="complete_run" targetRef="end" />
  </bpmn:process>
</bpmn:definitions>
```

## Python Package Layout

Production code should be importable, not only executable as an operator script.

```text
40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ingest/
  core.py
  houbun/
    __init__.py
    config.py
    egov.py
    constitute.py
    untc.py
    cfr.py
    eurlex.py
    normalize.py
    write.py
    verify.py
  houbun_worker_main.py
  houbun_start.py
```

`70-tools/scripts/houbun_live_ingest.py` should be refactored by moving reusable
functions into `kotodama.ingest.houbun.*`; the script can remain as a thin
CLI wrapper for emergency/manual backfills.

## Worker Handler Skeleton

```python
from pyzeebe import ZeebeWorker, create_insecure_channel

from kotodama.ingest.houbun.config import load_source_config
from kotodama.ingest.houbun.egov import plan_egov, fetch_egov
from kotodama.ingest.houbun.normalize import normalize_artifact
from kotodama.ingest.houbun.write import write_graph
from kotodama.ingest.houbun.verify import verify_visibility
from kotodama.ingest.core import (
    create_run,
    health_gate,
    acquire_cursor,
    advance_cursor,
    refresh_coverage,
    complete_run,
)


channel = create_insecure_channel(os.environ["ZEEBE_GATEWAY"])
worker = ZeebeWorker(channel)


@worker.task(task_type="houbun.createRun", timeout_ms=30_000)
async def task_create_run(run_id: str, source_id: str, mode: str, input_json: str = "{}"):
    return await create_run("houbun", run_id, source_id, mode, input_json)


@worker.task(task_type="houbun.planShards", timeout_ms=120_000)
async def task_plan_shards(source_id: str, mode: str = "delta", limit: int = 100, offset: int = 0):
    cfg = load_source_config(source_id)
    if cfg.planner == "egov_law_list":
        return {"shards": await plan_egov(limit=limit, offset=offset, include_constitution=True)}
    raise ValueError(f"unsupported planner: {cfg.planner}")


@worker.task(task_type="houbun.fetchSource", timeout_ms=300_000)
async def task_fetch_source(source_id: str, shard: dict, cursor_value: str | None = None):
    cfg = load_source_config(source_id)
    if cfg.fetcher == "egov_law_body":
        return await fetch_egov(shard["law_id"])
    raise ValueError(f"unsupported fetcher: {cfg.fetcher}")


@worker.task(task_type="houbun.normalize", timeout_ms=300_000)
async def task_normalize(source_id: str, artifact_uri: str):
    return await normalize_artifact(source_id, artifact_uri)


@worker.task(task_type="houbun.writeGraph", timeout_ms=300_000)
async def task_write_graph(source_id: str, normalized_uri: str):
    return await write_graph(source_id, normalized_uri)


@worker.task(task_type="houbun.verifyVisibility", timeout_ms=120_000)
async def task_verify_visibility(source_id: str, expected_counts: dict):
    return await verify_visibility(source_id, expected_counts)


asyncio.run(worker.work())
```

The real implementation should reuse the liveness mtime pattern already used by
`kotodama.zeebe_worker_main`, because a closed gRPC channel can silently park
tokens.

## Kubernetes Deployment

Use a separate worker Deployment from the generic `zeebe-worker` so parser/API
resource spikes do not starve shinka/devstral tasks.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: houbun-ingest-worker
  namespace: mitama-udf
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: houbun-ingest-worker
  template:
    metadata:
      labels:
        app.kubernetes.io/name: houbun-ingest-worker
    spec:
      containers:
        - name: worker
          image: ghcr.io/etzhayyim/kotodama:<tag>
          command: ["python", "-m", "kotodama.ingest.houbun_worker_main"]
          env:
            - name: ZEEBE_GATEWAY
              value: zeebe-gateway.mitama-udf.svc:26500
            - name: KOTOBA_URL
              valueFrom:
                secretKeyRef:
                  name: mitama-udf-pool-rw
                  key: KOTOBA_URL
            - name: HOUBUN_ARTIFACT_BUCKET
              value: etzhayyim-nats
            - name: HOUBUN_ARTIFACT_PREFIX
              value: houbun/ingest
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "750m"
              memory: "1Gi"
```

Cron starter:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: houbun-egov-jpn-delta
  namespace: mitama-udf
spec:
  schedule: "0 18 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: start
              image: ghcr.io/etzhayyim/kotodama:<tag>
              command:
                - python
                - -m
                - kotodama.ingest.houbun_start
                - --process-id
                - houbun_source_delta
                - --source-id
                - egov-jpn
                - --mode
                - delta
```

## Variables

Minimum process instance variables:

```json
{
  "run_id": "houbun-egov-jpn-20260425T180000Z",
  "source_id": "egov-jpn",
  "mode": "delta",
  "limit": 100,
  "offset": 0,
  "requested_by": "cron:houbun-egov-jpn-delta",
  "max_articles_per_law": 500
}
```

For backfill:

```json
{
  "run_id": "houbun-world-backfill-001",
  "source_id": "egov-jpn",
  "mode": "backfill",
  "range": {"offset": 0, "limit": 1000},
  "requested_by": "mcp:com.etzhayyim.apps.ingest.backfill"
}
```

## Cursor Strategy

JP e-Gov:

- shard key: `law_id`
- cursor: last verified `revision_info.updated_at` or source content hash
- destination id: `at://did:web:houbun.etzhayyim.com:jpn:e-gov/com.etzhayyim.houbun.statute/{law_id}`

Constitute:

- shard key: `constitution_id`
- cursor: metadata hash
- destination id: `at://did:web:contracts.etzhayyim.com/com.etzhayyim.apps.contracts.socialContract/{source_rkey}`

UNTC/Wikidata:

- shard key: SPARQL offset page or `objid`
- cursor: max offset verified
- destination ids: `vertex_houbun_treaty` and `vertex_contracts_social_contract`

CFR/EUR-Lex:

- shard key: title/package or CELEX id
- cursor: package date/version
- artifact required before normalization because source XML may change.

## Observability

Each task logs one compact JSON line:

```json
{
  "run_id": "...",
  "source_id": "egov-jpn",
  "task": "houbun.writeGraph",
  "shard_key": "321CONSTITUTION",
  "records_written": 104,
  "duration_ms": 832
}
```

Minimum metrics:

- Zeebe activated/completed/failed job counts by `task_type`.
- `vertex_ingest_run.status` counts.
- records read/written/skipped by source.
- verify lag: `write_finished_at -> verify_finished_at`.
- cursor age by source.

## Rollout

1. Add importable `kotodama.ingest.houbun` modules by moving code from
   `houbun_live_ingest.py`.
2. Add the BPMN file and deploy with `zbctl deploy`.
3. Start one manual instance for `egov-jpn` with `limit=5`.
4. Verify `vertex_houbun_statute`, `vertex_houbun_article`, and cursor rows.
5. Enable one daily CronJob with `limit=100`.
6. Add Constitute and UNTC weekly processes.
7. Only after the above is stable, add CFR/EUR-Lex and municipal ordinance
   backfills.

## Hard Boundary

`hanrei` remains case-law/judicial intelligence. It may request houbun ingest or
search houbun facts, but the authoritative law/constitution/treaty write path
is `houbun` BPMN + Python worker.
