# bpmn-engine-host

ADR 2605081200 — SpiffWorkflow BPMN engine host for the Zeebe replacement
PoC (Phase 1). Cluster-internal HTTP control surface. Persistent state
lives in Kotoba/Datomic (`vertex_spiff_*` tables, migration
`r_20260509110000_vertex_spiff_runtime`).

Replaces: Camunda 8 / Zeebe broker pod (license-encumbered).

## Scope (this slice)

- BPMN XML load from `vertex_bpmn_process_def` + parser cache
- `BpmnWorkflow` create + serialize → `vertex_spiff_instance`
- `do_engine_steps()` advance → re-serialize, append `vertex_spiff_history`
- Detect READY service-task tokens → enqueue `vertex_spiff_job`
- Worker callback `POST /v1/job/{id}/complete` → set task data, run task,
  advance, persist; idempotent on already-completed jobs
- Worker hard-fail `POST /v1/job/{id}/fail` (retryable by default)
- Per-instance `RLock` to serialize concurrent advance/complete (PoC
  single-replica; sharded path replaces with RW advisory lock)
- FastAPI on Granian, `/healthz` + `/readyz` + control endpoints

## Out of scope (Phase 2)

- Signal / message correlation routing (`POST /v1/instance/{id}/signal`)
- Signal / message correlation routing
- Hot-reload spec cache on RW change-data subscribe (currently explicit
  `POST /v1/process/{id}/reload`)
- Multi-shard topology + standby leader election
- Edge XRPC binding (`com.etzhayyim.apps.bpmn.startInstance` etc. → this host)

## Deploy

```bash
# Build (BuildKit remote, root CLAUDE.md "buildkit-k8s-remote-build")
70-tools/scripts/buildkit/remote-build.sh \
  -d 50-infra/k8s/bpmn-engine-host \
  -t ghcr.io/etzhayyim/bpmn-engine-host:$(date +%Y%m%d-%H%M%S)

# Apply
kubectl apply -f 50-infra/k8s/bpmn-engine-host/deployment.yaml
# Provision KOTOBA_URL from macOS Keychain (root CLAUDE.md, "Local Secret Storage")
security find-generic-password -s "etzhayyim.kotoba" -a "KOTOBA_URL" -w \
  | kubectl create secret generic bpmn-engine-host-secrets \
      -n mitama-udf --from-file=KOTOBA_URL=/dev/stdin
```

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/healthz` | — | `{status:"ok"}` |
| GET | `/readyz` | — | `{status:"ready"}` (503 if RW unreachable) |
| POST | `/v1/instance` | `{processId, variables?, correlationKey?, orgId?, userId?, actorId?}` | `{instanceId}` |
| POST | `/v1/instance/{id}/advance` | — | `{instanceId, completed, readyJobs[]}` |
| POST | `/v1/job/{id}/complete` | `{result?, workerId?}` | `{jobStatus, instanceId, completed, readyJobs[]}` |
| POST | `/v1/job/{id}/fail` | `{errorMsg, workerId?, retryable?}` | `{jobStatus, retryable, instanceId}` |
| POST | `/v1/job/{id}/throwBpmnError` | `{errorCode, message?, variables?, workerId?}` | `{jobStatus, errorCode, caught, instanceId, completed, readyJobs[]}` |
| POST | `/v1/instance/{id}/tick` | — | `{instanceId, completed, readyJobs[], persisted}` |
| POST | `/v1/timer/tick` | `?max_instances=N` | `{scanned, ticked, completed, errors}` |
| POST | `/v1/process/{id}/reload` | — | `{processId, version, xmlByteSize, loadedAt}` |

## Smoke

```bash
kubectl -n mitama-udf port-forward svc/bpmn-engine-host 8080:80 &
# Pre-req: at least one row in vertex_bpmn_process_def with bpmn_process_id
# (e.g. lawfirm_intake_funnel from migration 20260509080000)
curl -sX POST http://localhost:8080/v1/instance \
  -H 'content-type: application/json' \
  -d '{"processId":"lawfirm_intake_funnel","variables":{"intake_id":"smoke-1"}}'
```

## Risks / known issues

- **`do_engine_steps()` GIL**: Single Python process, single thread for
  engine steps. `BPMN_ENGINE_POOL_MAX=8` controls only the psycopg pool,
  not engine concurrency. Phase 3 introduces hash-sharded multi-pod for
  parallelism.
- **RW DDL contention**: This service does no DDL; only INSERT/DELETE.
  Heavy DDL must still go through the queue
  (`50-infra/CLAUDE.md` "Kotoba/Datomic Smooth Scaling Gate").
- **Spec cache invalidation**: Redeploying a BPMN does not auto-evict
  this pod's cache. Call `/v1/process/{id}/reload` after a
  `vertex_bpmn_process_def` insert until the firehose subscription is
  wired up.
- **Liveness vs asyncio**: `/healthz` is a trivial sync handler; this is
  intentional per root CLAUDE.md "pyzeebe asyncio loop starvation".
