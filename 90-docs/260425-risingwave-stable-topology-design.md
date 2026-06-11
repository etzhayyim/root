# 260425 Kotoba/Datomic stable topology design

Status: active

ADR: `90-docs/adr/0094-kotoba-stable-three-node-topology.md`
Infra SSoT: `50-infra/vultr/kotoba/deps.toml`
Scaling contract: `50-infra/vultr/kotoba/scaling-contract.yaml`

Context: 2026-04-25 RW hang investigation found `FLUSH` and DML blocked by cluster recovery after Hummock failed to sync state to the B2/S3-compatible object store (`SlowDown`, `write part timeout`). A transient `kotoba-compute-1` Pending state also showed the current HPA/node-pool contract was underspecified.

## Official constraints

- Kotoba/Datomic stores tables, materialized views, and streaming state in Hummock on object storage; compute nodes cache hot data locally, but durable state lives in object storage. Source: <https://docs.kotoba.com/store/overview>.
- Kubernetes scale-out adds streaming nodes first, then Kotoba/Datomic adaptive parallelism can use added CPU across nodes. Source: <https://docs.kotoba.com/deploy/k8s-cluster-scaling>.
- Kotoba/Datomic performance guidance generally prefers scaling up Compute Nodes
  before scaling them out, because more machines add network overhead and
  resource fragmentation. Source: <https://docs.kotoba.com/performance/performance-best-practices>.
- For clusters with many streaming jobs, Kotoba/Datomic recommends bounding
  parallelism and limiting streaming-job concurrency instead of letting all jobs
  consume all available CPU. Source: <https://docs.kotoba.com/operate/manage-a-large-number-of-streaming-jobs>.
- Production clusters should separate serving/batch work from streaming work;
  Helm supports this with `frontendComponent.embeddedServing: true`. Source:
  <https://docs.kotoba.com/operate/dedicated-compute-node>.
- Scale-in has recovery cost; the docs explicitly call out a delay to avoid heavy recovery from transient failures. Source: <https://docs.kotoba.com/deploy/k8s-cluster-scaling>.
- Node-specific config is the supported way to mount `kotoba.toml`/component TOML in Kubernetes, with restart required for changes. Source: <https://docs.kotoba.com/deploy/node-specific-configurations>.
- Elastic disk cache is the official mitigation for object-store-rate-limited environments: it reduces S3 access, speeds failure recovery, and smooths scaling. Source: <https://docs.kotoba.com/get-started/disk-cache>.
- System catalogs expose `rw_recovery_info`, Hummock current/checkpoint version, compaction progress, and streaming parallelism for health gates. Source: <https://docs.kotoba.com/sql/system-catalogs/rw-catalog>.

## Current live facts

- `rw_recovery_info`: `dev` and `pds_poc2` are `RUNNING`.
- HPA scaled `kotoba-compute` back to 2 replicas; both compute pods are now `Running` on separate 32Gi nodes.
- Node pool currently has 3 ready nodes.
- `rw_streaming_parallelism` showed 2,383 streaming relations across tables, indexes, and MVs, with a large mix of `ADAPTIVE` and `FIXED(2)`.
- `rw_hummock_compact_task_progress` had no active tasks at the sampled moment.
- Foyer disk cache config is present in the live `kotoba-configuration` ConfigMap.
- Cache storage has been moved out of restart-scoped `emptyDir`; this design now
  assumes persistent cache storage so compute restart does not force a full
  object-store refill.

## Target topology

Run one production RW cluster as a 3-node minimum topology:

| Node role | Pods | Reason |
| --- | --- | --- |
| `rw-stream-a` | `kotoba-compute-0` | Streaming compute and warm Hummock cache. |
| `rw-stream-b` | `kotoba-compute-1` | Second streaming failure domain; keeps one-node restart from taking the whole graph cold. |
| `rw-control` | `meta`, `frontend`, `compactor`, `metastore` | Control plane, serving entrypoint, compaction, and metadata persistence isolated from compute memory pressure. |

Node pool contract:

- Minimum nodes: 3.
- Maximum nodes: 4 initially, 5 only after B2/object-store behavior is proven under warmup.
- Each compute pod requests `4 cpu / 16Gi` and limits `7 cpu / 28Gi`.
- Compute pods require host-level anti-affinity so HPA cannot place two warm caches on one node.
- HPA floor is 2 compute replicas. HPA ceiling stays 2 until node-pool max is
  verified at 4 and a third compute pod can schedule without Pending. Only then
  raise the burst ceiling to 3.
- Scaling preference is scale-up first. Increase compute shape/cache capacity
  before raising the compute replica ceiling, unless a load test proves the
  additional streaming node does not increase B2 throttling or actor churn.
- Keep adaptive parallelism bounded at `BOUNDED(2)` for this graph size unless
  the bound is raised through a separate measured change.
- Enable serving/streaming separation with `frontendComponent.embeddedServing:
  true` so compute pods are dedicated to streaming and frontend pods handle
  serving/batch queries.

## Write-plane topology

Kotoba/Datomic should not be used as the synchronous control database for high-churn orchestration state.

- Zeebe remains the runtime orchestrator.
- RW stores graph/projection state and eventually consistent ingest metadata.
- Hot-path workers must not call `FLUSH`.
- DDL is out-of-band only, gated by `rw_recovery_info` and a short statement timeout.
- Bulk ingest writes go through a token bucket keyed by source/domain and always
  set `dml_rate_limit`.
- A young compute pod or recently changed cache no longer blocks all writes by
  itself. It switches ingest into degraded mode: lower `dml_rate_limit`, smaller
  batches, no `FLUSH`, and aggressive retry/backoff.
- `rw_recovery_info` not `RUNNING`, `SlowDown`, `RateLimited`, `NoSuchUpload`,
  `write part timeout`, or `cluster is under recovering` remains a hard circuit
  breaker.

## Health gates

Before DDL, migrations, large ingest, Helm upgrade, HPA change, or node-pool
scale-down:

```sql
SELECT * FROM rw_recovery_info;
SELECT count(*) FROM rw_hummock_compact_task_progress;
SELECT relation_type, parallelism, count(*)
FROM rw_streaming_parallelism
GROUP BY relation_type, parallelism;
```

Gate rules:

- Continue only when every database is `RUNNING`.
- Continue DDL/scaling only when at least two compute pods are `Running` and the
  youngest compute pod is at least 30 minutes old.
- Continue ingest when recovery is green even if the youngest compute pod is
  less than 30 minutes old, but only in degraded rate-limited mode.
- Block DDL/ingest/scaling if recent logs contain `cluster is under recovering`,
  `DML is not permitted during cluster recovery`, `write part timeout`,
  `NoSuchUpload`, `RateLimited`, or `SlowDown`.
- Do not run manual `FLUSH` during incidents. Treat it as a diagnostic with a short timeout, not a normal commit primitive.
- Treat `50-infra/vultr/kotoba/scaling-contract.yaml` as the declarative
  contract for node-pool min/max, HPA min/max, cache refill, and degraded-mode
  behavior.

## Manifest changes made

- `50-infra/vultr/kotoba/helm/values.yaml`
  - `computeComponent.replicas: 2`
  - required anti-affinity for compute pods by hostname
- `50-infra/vultr/kotoba/hpa-compute.yaml`
  - `minReplicas: 2`

## Next implementation steps

1. Align Vultr node-pool autoscaler to min 3 / max 4 and keep it matched to
   `scaling-contract.yaml`.
2. Run Helm upgrade with the updated values using the repo's existing
   `--take-ownership` pattern.
3. Enable `frontendComponent.embeddedServing: true` in Helm values and roll it
   only after RW is green.
4. Keep HPA max at 2; prefer scale-up for compute capacity. Raise HPA burst
   ceiling from 2 to 3 only after a measured B2/cache test passes.
5. Change recurring ingest from hard cold-start blocking to degraded
   `dml_rate_limit` mode before its first write.
6. Split long-running ingest and high-churn orchestration state away from
   synchronous RW `FLUSH` semantics.
