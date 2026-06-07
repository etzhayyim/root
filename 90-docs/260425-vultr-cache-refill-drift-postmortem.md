# 260425 — Vultr Kotoba/Datomic cache_refill drift postmortem

Severity: **P1** (data-plane read outage, ~20 min)
Incident window: 2026-04-25 **11:05 → 11:30 JST** (compute-0 OOM → manual workload halt → self-recovery)
Primary author: Claude / ops follow-up pending.
Status: **root cause fixed in values.yaml + docs; helm rollout still required to materialize.**
References:
- `50-infra/vultr/kotoba/deps.toml [kotoba_vultr.incident_2026_04_25]`
- `deps.toml [[migrations]] rw-foyer-insert-rate-limit-port-to-vultr-2026-04-25`
- `90-docs/adr/2604251024-patent-bulk-ingest-and-blob-cid.md §Ingest Safety`
- `deps.toml [[conventions]] rw-bulk-insert-throttle` / `rw-health-gate-before-ingest`

## 1 — Summary

During smoke-test bulk ingest (patent metadata from Wikidata SPARQL),
`kotoba-compute-0` was OOMKilled at 11:05 JST. The restart triggered
a cold-Foyer refill that issued unbounded parallel SST reads to Backblaze
B2. B2 returned HTTP 503 `SlowDown` at approximately **12 events/sec**
(1,791 events in 120 s window), after which Hummock reads failed with
`ObjectStore RateLimited`, and every read-side query across the cluster
began timing out. Writes were manually halted at 11:13; full recovery
observed at ~11:32. No data was lost; no row was corrupted.

## 2 — Timeline (JST)

| Time | Event |
|---|---|
| ~10:00 | Background — `kotoba-meta-0` pod had restarted 61 min earlier (unrelated). |
| 10:47 | ADR 2604251024 patent-bulk-ingest PR work begins; smoke-test downloads 1 USPTO PDF; CIDs computed locally. |
| 10:55 | `CREATE TABLE vertex_patent_blob` issued against RW — times out after 30 s NOTICE "high barrier latency". Canceled 2x in succession (ddl_id 8773, 8774 both canceled). |
| 10:58 | First Wikidata SPARQL batch (986 `vertex_patent` rows) INSERTed via `psql -f`. |
| 11:05 | **`kotoba-compute-0` OOMKilled** (exit 137). Pod restarts with empty Foyer disk cache. |
| 11:05+ | Foyer `recover_mode = Quiet` preserved the on-disk cache slots, but in-flight queries had already triggered `cache_refill` to repopulate hot LSM levels from B2. Unbounded parallel reads begin. |
| ~11:06 | Backblaze B2 begins returning `<Code>SlowDown</Code>` nginx 503 responses: observed rate ~12 events/sec in `kotoba-compute-0` log. |
| 11:08 | `ingest.py` (loop-3 fire) starts second-generation INSERT batch into `vertex_work` / `edge_patent_cites` / `edge_owned_by`. `works.sql` `psql -f` hangs on `SELECT` fanout needed by streaming MV recompute. |
| 11:11 | Another operator issues a concurrent `CREATE TABLE vertex_open_defence_event` which also queues at 0% behind the stuck backfill. |
| 11:13 | ops kills `ingest.py` (PID 87762) and the stuck `psql` (PID 87869). No more writes from this workstation. |
| 11:18 | `kubectl logs --since=60s \| grep -c SlowDown` = 127 — storm still active. |
| 11:25 | `SlowDown` rate drops to <10/60s. |
| 11:32 | Foyer warm (~27 min since OOM); `SELECT 1` returns in 0 s; health gate reports healthy. |

## 3 — Root cause

**Config drift between ADR-0048 Vultr cutover (2026-04-22) and the Linode
configuration it was meant to replicate.**

Linode `50-infra/linode/kotoba-iceberg/helm/values-dedicated-32.yaml`
had three defense-in-depth blocks under the compute `configuration:` key:

```toml
[storage.data_file_cache]
… insert_rate_limit_mb = 450

[storage.meta_file_cache]
… insert_rate_limit_mb = 50

[storage.cache_refill]
data_refill_levels = [0, 1, 2, 3, 4, 5, 6]
concurrency = 10
unit = 64
threshold = 0.5

[server]
statement_timeout_secs = 120
```

These three blocks were **not present** in
`50-infra/vultr/kotoba/helm/values.yaml` when the Vultr cluster was
stood up on 2026-04-22. Without them:

- `cache_refill` uses the compiled-in default (unbounded parallelism,
  all LSM levels, no threshold) → a cold Foyer can issue dozens of
  concurrent range reads.
- `insert_rate_limit_mb` has no effective cap → Foyer writes compete
  with application reads for the same B2 bucket quota.
- `statement_timeout_secs` unset → a single stuck read can hold the
  query queue indefinitely, amplifying the storm.

Compounding the drift, **root `CLAUDE.md`** documented the Linode
numbers as if they were current Vultr production: "Foyer disk cache 32
GiB data + 4 GiB meta + `insert_rate_limit_mb=450/50` + `[storage.cache_refill]`
refill level 0-6". Actual Vultr values were 16 GiB data + 4 GiB meta
with **neither** the rate-limit nor the refill section present. Any
engineer (including the LLM) reading CLAUDE.md would believe the
mitigations were live when they were not.

## 4 — Trigger

The OOMKill itself was triggered by an uncapped bulk `INSERT` stream:
the smoke-test `ingest.py` opened a single `psycopg2` session and
streamed ~4,000 INSERTs across 3 tables plus `FLUSH;` between batches,
with `dml_rate_limit = -1` (unlimited). On a cluster with 772 tables /
172 MVs, each INSERT cascades into streaming-MV state updates; aggregate
memtable pressure pushed `compute-0` past its 30 GiB limit.

The drift (§3) is the latent cause. The uncapped workload (§4) is the
proximate trigger. Either alone would likely have been survivable.

## 5 — Fix applied in this commit

| Layer | Fix |
|---|---|
| `50-infra/vultr/kotoba/helm/values.yaml` | Ported the three missing blocks from Linode `values-dedicated-32.yaml` verbatim (comments preserved). Needs `helm upgrade --take-ownership` + rolling restart to take effect. |
| `50-infra/vultr/kotoba/deps.toml` | New `[kotoba_vultr.incident_2026_04_25]` section records timeline, drift, fix, and guardrails. |
| Root `deps.toml` | New `[[migrations]] rw-foyer-insert-rate-limit-port-to-vultr-2026-04-25` (status=in-progress until helm rollout lands). Two new `[[conventions]]`: `rw-bulk-insert-throttle` (mandatory `SET dml_rate_limit` for bulk ingest) and `rw-health-gate-before-ingest` (3-point probe before fire). |
| Root `CLAUDE.md` | Retracted the stale Linode-numbers claim inline; linked to the new incident section for authoritative current state. |
| `90-docs/adr/2604251024-patent-bulk-ingest-and-blob-cid.md` | New "Ingest Safety" section with Invariant A (`SET dml_rate_limit`) + Invariant B (3-point health gate) made mandatory for all patent/trademark/copyright BPMN processes. |
| `50-infra/vultr/patent-blob-converter/converter.py` | pyzeebe worker now issues `SET dml_rate_limit = 500` + `SET statement_timeout = '120s'` on every psql connection (autocommit). |
| `70-tools/scripts/ingest/rw-health-gate.sh` | Canonical implementation of the 3-point probe (exit 0/1/2). Verified against the live Vultr cluster post-recovery. |

## 5b — Follow-on findings (2026-04-25 afternoon, fires 5–7)

After the config fix + `helm upgrade` + rolling restart (revision 13,
11:36 JST), three further observations changed the understanding:

1. **The new config blocks background refill and Foyer writes, but do
   not throttle demand-side reads.** `[storage.cache_refill]` gates
   RW's *proactive* cache population and `insert_rate_limit_mb` gates
   *writes into Foyer*. Neither affects what happens when an active
   query touches a block that is not yet in Foyer — that goes straight
   to B2. With 772 tables on a 16 GiB Foyer (Vultr is half the Linode
   capacity), a single `CREATE TABLE` + one 5,000-row `INSERT` at the
   5-minute mark after restart produced **54 SlowDown/sec** (worse
   than the 12/sec peak of the original incident). Post-workload the
   cluster cascaded into the `cluster is under recovering` meta state
   and cancelled the in-flight DDL (ddl_id 8786).
2. **Even read-only pre-filter queries are unsafe during warmup.**
   At the 16-minute mark (barely past the 15-min threshold the gate
   had used), a `SELECT wikidata_qid FROM vertex_legal_entity` issued
   by the ingest script as a pre-filter **triggered SlowDown 702/60s
   (~11.7/sec)** and bubbled up as `Foyer error: RateLimited`. There
   is no way to make the pre-filter cheaper — that table is the thing
   we were dedup-ing against.
3. **The 15-min Foyer-warm threshold is too optimistic for Vultr.**
   On Linode (40 GiB Foyer, ADR-0019 topology) 15 minutes was enough;
   on Vultr (16 GiB Foyer + half the node memory) the working set does
   not fit in cache and the warm-up is effectively bounded by the
   cold-read storm. Observed behaviour: at 16-min pod age SlowDown was
   still 11/sec; at 30-min pod age it's expected to converge (this
   needs to be re-measured once a quiescent warmup completes).
   **Threshold raised 900s → 1800s** in `70-tools/scripts/ingest/rw-health-gate.sh`
   default.

Implications for the gate:

- `MIN_COMPUTE_AGE_SEC=1800` is now the default. Callers that know
  the cluster state (e.g. manually-paused ingest after a ~30-min
  idle) may override lower, but the default must reflect the worst
  case.
- The SlowDown probe (`probe 3/3`, `SLOWDOWN_MAX=10` per 60s) remains
  the right stop-signal. In practice it was more reliable than the
  time-based probe — fire 6 had age=600s (degraded) but SlowDown=0,
  fire 7 had age=885s (near threshold) but SlowDown also 0, fire 5
  had age<900s and triggered the new storm. The two probes together
  keep the gate conservative on both axes.
- Adding a 4th probe — a scoped `SELECT vertex_id FROM vertex_patent
  WHERE ... LIMIT 1 FETCH FIRST ... ` with a 5-second timeout — would
  directly measure demand-side read cost, but that probe itself
  contributes to B2 load during warm-up (the classic observer
  problem). Not added.
- Raising Vultr Foyer capacity (16 → 32 GiB data + 8 GiB meta) so the
  hot set actually fits is the durable fix; the gate is the
  availability band-aid until that happens. Tracked in follow-up
  issue `rw-vultr-foyer-capacity-expand-2026-04-25`.

## 6 — Prevention (beyond the fix)

1. **CI guard**: add a lint that fails CI if `50-infra/vultr/kotoba/helm/values.yaml`
   is missing any of `[storage.cache_refill]`, `insert_rate_limit_mb`,
   or `statement_timeout_secs`. Script template: `70-tools/scripts/ci/check-rw-values-tuning.sh`.
2. **Source-of-truth discipline**: when `CLAUDE.md` documents infra
   config values (cache sizes, rate limits, memory limits), it MUST
   cite the live file path that contains them (`50-infra/*/helm/*.yaml`)
   — never paraphrase. Paraphrase rots silently across cutovers.
3. **Runbook**: future cluster cutovers (Linode→Vultr, future moves) get
   a "tuning-block diff" checklist item — diff the outgoing values.yaml
   tuning block against the incoming one, and require sign-off on any
   deletion.
4. **Observability**: add a Prometheus alert on
   `rate(opendal_s3_http_status_total{status="503"}[1m]) > 0.5` — this
   would have paged at 11:06, 7 minutes before the operator noticed.
5. **Cohort workload guard**: no single psycopg2 session should emit
   more than ~500 INSERTs without an explicit `SET dml_rate_limit`. The
   `rw-bulk-insert-throttle` convention makes this explicit; the
   converter pod already applies it. Bulk-ingest scripts not yet
   migrated to this pattern are listed in the "remaining work" issue.
6. **Distinct bulk-ingest bucket on B2?** — Defer until we can measure
   whether dedicating a second B2 bucket + scoped application key for
   ingest-driven SST writes actually isolates the quota. B2 rps quotas
   are documented as per-account, not per-bucket, so this may be a
   no-op; leaving as an open question.

## 7 — Remaining work (tracked)

- Run `helm upgrade --take-ownership -f 50-infra/vultr/kotoba/helm/values.yaml`
  against the Vultr cluster (ops approval required — causes rolling
  restart of `kotoba-compute-0`, ~30 s unavailability on the
  read-plane).
- Re-apply `30-graph/graph-schema/migrations/20260425102400_vertex_patent_blob.ts`
  once compute-0 is stable and health gate returns 0.
- INSERT the staged pat5 (961 rows) + doi (5,000 rows) Wikidata batches
  that were deferred during the incident.
- Register BPMN dispatcher primitives for the new task types
  (`patent.usptoPatentsview.ingestPatent`, `patent.epoOps.fillCitations`,
  `patent.blob.convert`, `rw.health.probe`).
- Add the CI guard described in §6.1.

## 8 — No data loss, no customer impact

The incident affected the Kotoba/Datomic read plane only. Writes that had
already committed (986 `vertex_patent` rows from the first ingest batch,
2,940 `vertex_trademark` rows) were durable. No AT Protocol PDS /
federation traffic was affected (PDS talks to RW via Hyperdrive and
retries on `Scheduler error`). No user-facing app returned a 5xx to an
external caller during the window (all activity was internal ops).
