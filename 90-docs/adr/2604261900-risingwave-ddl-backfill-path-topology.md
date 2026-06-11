---
id: adr-2604261900-kotoba-ddl-backfill-path-topology
title: Kotoba/Datomic DDL Backfill and Hot Path Topology
status: active
doc_type: adr
topic: infrastructure
authoritative: true
last_verified: 2026-04-26
authoritative_for:
  - kotoba-write-path-topology
  - kotoba-ddl-queue-topology
  - kotoba-backfill-path-topology
  - kotoba-flush-policy
related:
  - adr-0094-kotoba-stable-three-node-topology
  - adr-2604241342-kotoba-out-of-band-migration-pattern
supersedes: []
superseded_by: []
---

# Context

The production Kotoba/Datomic cluster runs on Vultr VKE with Hummock state on
Backblaze B2. The 2026-04-25 incidents showed that treating application ingest,
DDL, backfill, migration, FLUSH, and scaling as one operational path creates a
single failure surface:

- hot-path workers issued schema/flush work while the cluster was recovering;
- DDL/backfill created streaming jobs during object-store pressure;
- compute restart or scale events cold-started cache refill against B2;
- write callers saw `DML is not permitted during cluster recovery`.

Kotoba/Datomic supports background DDL, `WAIT`, `CANCEL JOBS`, runtime parameters,
and catalog-based progress monitoring. Those controls only help if every writer
uses a stable topology with explicit path ownership.

The 2026-04-26 barrier incident confirmed that the boundary must also cover
Cloudflare Workers and foreground MV backfills. A foreground
`CREATE MATERIALIZED VIEW mv_gov_record_dedup` job (`9163`) scanned
`vertex_repo_record` with a 15,993,583-row snapshot while hot-path `FLUSH`
sessions were active. An unrelated lightweight `CREATE TABLE` probe (`9175`)
stayed at 0% until both jobs were canceled.

# Decision

Use five separate VKE/K8s paths. The hot path never owns DDL, backfill, or
FLUSH. The ops paths are serialized and gated.

| Path | K8s home | Allowed work | Forbidden work | Gate |
|---|---|---|---|---|
| Hot write path | app namespaces such as `mitama-udf`, `blockchain`, and social/fund workers | bounded `INSERT`/`UPDATE`/`DELETE`, cursor writes, small metadata updates | `CREATE TABLE`, `CREATE MATERIALIZED VIEW`, `CREATE INDEX`, source/sink creation, destructive `ALTER`/`DROP`, `FLUSH`, initial backfill | `RW_DDL_GUARD=1`, `RW_ALLOW_HEAVY_DDL=0`, `RW_ALLOW_FLUSH=0`, `rw-health-gate.sh` |
| DDL queue path | `kotoba` namespace, future `rw-ddl-queue-runner` Job/Deployment | one heavy DDL at a time with background DDL and bounded parallelism | bulk data ingest, application-serving writes | `rw_recovery_info` running, no object-store errors, no pending compute, `rw_ddl_progress` owner check |
| Migration runner path | graph-schema or migration namespace, isolated Job | submit migration statements to the DDL queue, record audit output | direct psql DDL from app images, concurrent runners | queue lock plus dry-run before apply |
| Backfill path | dedicated `*-backfill-worker` Jobs or Zeebe workers | rate-limited historical ingest and MV/source backfills | hot cursor writes without throttle, schema creation outside queue | `dml_rate_limit`, `source_rate_limit` where applicable, small batches, circuit breaker |
| Operator diagnostics path | short-lived operator Job/shell | `SHOW JOBS`, catalog reads, bounded diagnostic `FLUSH` only when explicitly required | commit primitive, cron-based flush, app-callable flush | manual reason, timeout, clean recovery/object-store gate |

## VKE and Helm Topology

- `kotoba` namespace owns Kotoba/Datomic Helm resources, `rw-meta-backup`, and
  the future `rw-ddl-queue-runner`.
- Application namespaces own hot-path workers only. Their pod env must default
  to `RW_DDL_GUARD=1`, `RW_ALLOW_HEAVY_DDL=0`, `RW_ALLOW_FLUSH=0`, and
  `RW_SYNC_POOL=0`.
- Cloudflare Workers using Kotoba/Datomic through Hyperdrive are also hot-path
  writers. Their `wrangler.jsonc` vars must default to `RW_ALLOW_FLUSH=0`.
  A Worker may issue `FLUSH` only when explicitly redeployed or configured for
  a bounded diagnostic run with `RW_ALLOW_FLUSH=1`.
- Dedicated backfill workers use separate manifests, smaller resource requests,
  explicit rate limits, and resumable cursors. They do not share the same
  deployment as live hot-path consumers.
- Migration jobs do not connect to Kotoba/Datomic as free-form psql clients. They
  submit to the DDL queue, which is the only writer allowed to run heavy DDL.
- Helm/HPA/node-pool changes use `scaling-contract.yaml` before apply. Compute
  scale-up is preferred before scale-out; scale-out remains bounded by the node
  floor and cache/object-store gates in ADR-0094.

## DDL Queue Algorithm

1. Run `70-tools/scripts/ingest/rw-health-gate.sh`.
2. Acquire a single queue lock, preferably a Kubernetes `Lease` in namespace
   `kotoba`. A DB lock table is acceptable only if it is already available.
3. Confirm `rw_catalog.rw_recovery_info` is running for every database.
4. Confirm recent Kotoba/Datomic logs contain no `SlowDown`, `RateLimited`,
   `NoSuchUpload`, `write part timeout`, recovery block, or pending compute.
5. Confirm `rw_catalog.rw_ddl_progress` is empty or the active job is owned by
   the same queue worker.
6. Set the session preamble:
   - `SET BACKGROUND_DDL = true`
   - `SET streaming_parallelism_strategy_for_table = 'BOUNDED(1)'`
   - `SET streaming_parallelism_strategy_for_materialized_view = 'BOUNDED(1)'`
   - `SET streaming_parallelism_strategy_for_index = 'BOUNDED(1)'`
7. Submit exactly one heavy DDL statement.
8. Poll `rw_ddl_progress` and `SHOW JOBS`.
9. Use `WAIT` for the created table, materialized view, index, source, or sink
   before the next heavy DDL is released.
10. Record SQL hash, owner, start/end time, Kotoba/Datomic job id, and gate status.

Materialized views over existing data are always heavy DDL, even when the SQL
looks narrow. They must not be submitted as foreground work from an ad-hoc psql
session. Use `BACKGROUND_DDL`, bounded parallelism, and statement-level
`source_rate_limit` where Kotoba/Datomic supports it.

## Backfill and Flush Policy

Backfill is data movement, not schema management. Backfill workers must be
resumable, throttled, and circuit-broken on recovery or object-store errors.
Large historical loads use a separate path even when the target table already
exists.

Bulk ingest follows the same separation. It must not run during RW cold-start
or object-store recovery windows unless the job has an explicit low
`dml_rate_limit`, bounded batch size, and an operator has accepted degraded
mode. On 2026-04-26, `maps-bulk-ingest` sent giant `INSERT INTO vertex_spatial`
batches during the 58Gi node migration cold-start window and triggered
`DML is not permitted during cluster recovery`; the remediation was to scale
the bulk-ingest deployments to zero until `rw-health-gate.sh` returned healthy
or degraded-write only.

`FLUSH` is diagnostic-only in this topology. It is never a commit primitive and
must not be embedded in application code, Zeebe handlers, cron jobs, or migration
scripts. Operator FLUSH requires a short timeout and a recorded reason.
Read-after-write callers should tolerate checkpoint lag or use a separate
application-level state path; they must not force a checkpoint from the hot path.

Operational support jobs also stay out of the hot path:

- `rw-meta-backup` is allowed to run hourly, but snapshot count must be pruned
  before it reaches Kotoba/Datomic's 100-snapshot manifest limit. A successful
  verification backup is required before deleting failed backup Jobs from an
  incident window.
- `data-collection` state uses `collector-state-pvc`; on Vultr this PVC must be
  at least `40Gi`, because smaller requests are rejected by the block-storage
  API.

## Recovery Policy

If a DDL job is stuck but recovery is running and object-store logs are clean,
the queue may issue `CANCEL JOBS <job_id>` and requeue after gates pass. The
queue must not run automatic `RECOVER`; recovery remains an explicit operator
action.

If `SHOW JOBS` shows an unowned foreground MV backfill, cancel it before
submitting or retrying unrelated schema work. The job can be requeued as a
heavy DDL after gates pass.

# Consequences

- Application writes remain available during compute cold start when recovery is
  running and object-store logs are clean; they degrade through lower
  `dml_rate_limit` and smaller batches.
- Schema evolution becomes slower but deterministic: one heavy DDL at a time.
- Backfills cannot accidentally share the live cursor deployment.
- Future Helm or VKE scaling changes have a single contract that covers write
  path behavior, not only pod counts.

# Alternatives Considered

- Allow app workers to create missing tables lazily. Rejected because it couples
  the hot path to streaming-job creation and backfill.
- Use FLUSH as a write barrier. Rejected because FLUSH blocks during recovery and
  amplified the production incident.
- Pause all ingest whenever compute is young. Rejected because cold-start alone
  is not a correctness failure; recovery and object-store pressure are the true
  hard stops.

# References

- Kotoba/Datomic background DDL: https://docs.kotoba.com/sql/commands/sql-set-background-ddl
- Kotoba/Datomic `WAIT`: https://docs.kotoba.com/sql/commands/sql-wait
- Kotoba/Datomic `CANCEL JOBS`: https://docs.kotoba.com/sql/commands/sql-cancel-jobs
- Kotoba/Datomic runtime parameters: https://docs.kotoba.com/operate/view-configure-runtime-parameters
- Kotoba/Datomic system catalogs: https://docs.kotoba.com/sql/system-catalogs/rw-catalog
- Kotoba/Datomic serverless backfill: https://docs.kotoba.com/processing/serverless-backfill
- Kotoba/Datomic Kubernetes scaling: https://docs.kotoba.com/deploy/k8s-cluster-scaling
- Kotoba/Datomic disk cache: https://docs.kotoba.com/get-started/disk-cache
