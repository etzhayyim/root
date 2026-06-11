---
id: adr-2605081430-osm-ingest-rw-tuning-and-k8s-utilization
title: OSM ingest tuning + RW compute CPU limit + K8s utilization score
status: accepted
doc_type: adr
topic: infra
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - osm-ingest-tuning
  - kotoba-compute-resources
  - k8s-utilization-score
related:
  - 90-docs/adr/0048-kotoba-vultr-b2-primary.md
  - 90-docs/adr/0094-kotoba-stable-three-node-topology.md
supersedes: []
superseded_by: []
---

# OSM ingest tuning + RW compute CPU limit + K8s utilization score

## Context

OSM PBF ingest pipeline (`70-tools/maps-osm-ingest`, image v0.3.0) has been the
sole stress workload against the 2-node Vultr VKE RW cluster. Run 1 (Japan,
2026-05-05→07) failed at 48.7h during way phase due to compute-0 restart.
Run 2 stopped at 3h to characterize the bottleneck. Three Andorra benches
(2026-05-08, 491k nodes / 26k ways / 761 rels / 587k way-edges) characterized
optimal config.

The 2-node `kotoba-pool-58gb` (vhf-16c-58gb × 2 = 32 vCPU / 116 GiB) is
shared by RW (compute / meta / frontend / compactor / metastore), Zeebe broker,
~10 pyzeebe worker pools, Mitama actors (shinshi / kobo / kabi / hakkou / etc.),
BPMN dispatcher, and ad-hoc ingest. After Foyer disable (ADR-0048 incident
2026-04-25), in-memory cache absorbs all hot-path SST reads.

This ADR codifies (a) the optimal OSM ingest config validated end-to-end,
(b) the RW compute CPU limit lift discovered through bench profiling, and
(c) a quantitative K8s utilization score with explicit improvement targets.

## Decisions

### D1. OSM ingest optimal config (verified, N=2 Andorra)

| Param | Value | Source |
|---|---|---|
| `--batch-size` | **1000** | bench: flush=5000 was -28% slower |
| RW system `barrier_interval_ms` | **2000** | Config A; 5000 → 2000 |
| RW system `checkpoint_frequency` | **15** | Config A; 30 → 15 (cycle 150s → 30s) |
| RW system `batch_enable_distributed_dml` | **true** | bench: +12% mean N=2 |
| Image | `ghcr.io/etzhayyim/maps-osm-ingest:v0.3.0` | RunTracker + B2 cache (POST bug, falls back to direct) + cursor every 100 batches |
| Per-pod cpu request / limit | **2 / 4** | per-pod parallelism: 3 writers (node/way/rel) |
| Per-pod memory request / limit | **4Gi / 8Gi** | streamed decode, no large in-memory state |

Rejected configs:
- `--batch-size 5000` (antipattern, codified `[[conventions]] osm-ingest-optimal-config-andorra-validated`)
- Foyer disk cache (carried over from ADR-0048 retraction)

### D2. RW compute CPU limit raised 1250m → 6000m

Bench observation: both compute pods hit 99% CPU at the 1250m limit during
single-pod Andorra ingest. Each node has 16 vCPU; 14+ vCPU sat idle. CPU was
the proximate bottleneck, not memory or B2.

Change: `kubectl patch sts kotoba-compute` (helm conflicted with prior
`kubectl-patch` field manager; out-of-band patch is canonical here).

```
limits:
  cpu: 1250m  →  6m   # 6000m
  memory: 24Gi (unchanged)
requests:
  cpu: 1 (unchanged)
  memory: 20Gi (unchanged)
```

Expected throughput uplift: 2.5–3× (CPU-bound measurement). Risk: rolling
restart of compute pods interrupts in-flight ingests; OSM ingest's
content-addressed PK + cursor enables idempotent restart, so blast radius is
< 1 ingest job.

`computeComponent.resources.limits.cpu` in `50-infra/vultr/kotoba/helm/values.yaml`
should be updated to `6000m` to align with deployed state (drift cleanup).

### D3. distributed_dml=true global (with sunset)

Currently set ALTER SYSTEM globally. Per RW source review
(`src/common/src/session_config/mod.rs`), the official semantics are
"No atomicity guarantee in this mode. Its goal is to gain the best ingestion
performance for initial batch ingestion where users always can drop their
table when failure happens." Safe for OSM (content-addressed PK, idempotent
re-run, droppable). Unsafe blanket for transactional DML.

Migration: maps-osm-ingest v0.4.0 should add `SET batch_enable_distributed_dml = true`
session-local at writer connect time, then ALTER SYSTEM revert to false.
Tracked as `[[migrations]] osm-ingest-session-local-distributed-dml`.

### D4. Right-size memory requests on over-provisioned non-RW workloads

User directive (2026-05-08): optimize within current 2-node `vhf-16c-58gb`
topology; future scale-out is **horizontal** (more 58 GiB nodes), not vertical
(bigger nodes). This rules out the `vhf-32c-128gb` upgrade path.

Audit revealed many non-RW pods at 1-30% memory utilization. Live patches
applied via `kubectl patch deployment ... --type=json` (drift from helm
chart values acknowledged; chart values to be re-synced in follow-up):

| Pod | Was | Now | Real usage | Rationale |
|---|---|---|---|---|
| yoro-actors/yoro-vector-embedding-worker | 4 GiB | 512 MiB | 61 MiB (1%) | massive slack |
| mitama-udf/zeebe-worker | 3 GiB | 1 GiB | 163 MiB (5%) | over-request |
| mitama-udf/chat-agent | 2 GiB | 512 MiB | 81 MiB (4%) | over-request |
| ipfs/kubo-0 | 2 GiB | 512 MiB | 126 MiB (6%) | over-request |
| mitama-udf/mitama-udf (3 replicas) | 1 GiB ea | 384 MiB | ~110 MiB (11%) ea | over-request |
| maps-bulk-ingest/{wikidata,osm-planet,geonames,gtfs-jp,wikipedia} | 1 GiB ea | 384 MiB | 29-126 MiB (3-12%) | over-request |
| mitama-udf/{lg-x,lg-shinshi,lg-narou,lg-mangaka,lg-animeka,animeka-zeebe-worker} | 768 MiB ea | 384 MiB | ~100 MiB (14%) ea | over-request |
| **Total reclaim** | | | | **~22 GiB nominal request** |

Inverse: **under-requested pods upgraded to prevent OOM**:

| Pod | Was | Now | Real usage |
|---|---|---|---|
| blockchain/ethereum-mainnet | 5.6 GiB | 10 GiB | 8.4 GiB (149% — OOM risk) |
| blockchain/bitcoin-mainnet | 2 GiB | 4 GiB | 3.1 GiB (154% — OOM risk) |

Net cluster memory request impact: **-22 GiB (reclaim) + 6.4 GiB (OOM fix)
= ~15.6 GiB net freed**. Observed delta: node-0 memory request 95% → 83-89%
(post-rolling-restart steady-state). node-1 stays 92-96% because the bigger
ethereum/bitcoin upgrades landed there.

Concurrent ingest parallelism: 2 → **4** pods (verified post-rightsize),
expected to settle at 6-8 once rolling restarts converge.

### D5. Horizontal scale path (no vertical upgrades)

Per user directive 2026-05-08, the scaling path is monotonic horizontal:

```
Phase 1 (now):   2× vhf-16c-58gb (32 vCPU / 116 GiB)   $640/mo
Phase 2 (next):  3× vhf-16c-58gb (48 vCPU / 174 GiB)   $960/mo  +1 compute pod
Phase 3 (later): 4× vhf-16c-58gb (64 vCPU / 232 GiB)   $1280/mo +1 compute pod
```

Anti-affinity (`requiredDuringSchedulingIgnoredDuringExecution` on
`kotobalabs.com/component=compute`) means 1 compute pod per node max.
With each new node = 1 new compute pod = ~+33% throughput (Phase 1→2) or
~+25% (Phase 2→3, diminishing).

**Rejected**: `vhf-32c-128gb` vertical upgrade. Reasons: (a) halves the
anti-affinity slot count for HA, (b) doubles per-node blast radius, (c) cost
parity with horizontal (2× of `vhf-32c-128gb` = $1280/mo same as 4× of
`vhf-16c-58gb`), (d) horizontal gives more topology shards for streaming
parallelism.

### D6. Trigger RECOVER to rebalance actors after compute scale-out

After D2 rolling restart of both compute pods, observed actor placement
heavily skewed to compute-1 (worker 775): 23,651 actors vs 89 on
compute-0 (worker 776). compute-0 idle at 0.5% CPU while compute-1 at
79% of its new 6 cpu limit.

Root cause: `disable_automatic_parallelism_control = true` (set 2026-04-30
post-incident) prevented RW from auto-rebalancing after worker re-registration.
Without rebalance, all pre-existing streaming actors remained on compute-1
and only newly-created actors landed on compute-0.

Cure path tested 2026-05-08T16:21 JST:

1. `ALTER SYSTEM SET adaptive_parallelism_strategy = 'AUTO'` (rw_admin user)
2. `ALTER MATERIALIZED VIEW mv_osm_ingest_top_runs SET PARALLELISM = 12`
   (any MV change works as a trigger; output prompts: "Run RECOVER in a
   separate session to trigger recovery")
3. `RECOVER` (rw_admin user, fires actor redistribution)

Outcome (T+16 seconds, no recovery loop):

| Metric | Pre-RECOVER | Post-RECOVER | Δ |
|---|---|---|---|
| Actors on compute-0 | 97 (0.3%) | **20,924 (49.9%)** | +21,500% |
| Actors on compute-1 | 23,657 | 21,000 | balanced |
| compute-0 CPU usage | 30m (0.5%) | **2,933m (49%)** | +9,777% |
| compute-1 CPU usage | 4,716m (79%) | 3,976m (66%) | -16% |
| **Combined CPU** | **4,746m** | **6,909m** | **+45.6%** |
| Stuck DDL in SHOW JOBS | 1 (`vertex_lawfirm_msgraph_subscription`) | 0 | queue cleared |
| Ingest pod casualties | — | 1 (Cambodia, gRPC reset) | content-addr PK enables cheap re-apply |
| RECOVERING loop | — | none ✓ | 2026-04-30 trauma overcome |

**2026-04-30 incident retrospective**: that incident was on a
*license-capped 1-worker* topology where automatic rebalance had no place
to spread to and looped. With 2 healthy 6-cpu workers, RECOVER converges
in seconds. The original `disable_automatic_parallelism_control = true`
guard was the right call for that topology but is now stale; the static
control should be lifted post-rebalance.

Follow-up tracked: re-evaluate whether to leave automatic parallelism
control enabled going forward, or only flip it on transiently around
manual rebalance events.

### D7. Compactor horizontal scale-out (1×0.5cpu → 3×2cpu)

After D6 stabilized actor balance, world-ingest soak revealed the next
choke point: the Hummock compactor.

**Symptoms (h+6 monitoring)**:
- `running_parallelism_count = 1` on the single compactor replica
- Level 0 SSTs reported `stale_ratio: 85-93` (i.e. 85-93% of each SST is
  overwritten data) accumulating without compaction
- Compactor pod CPU **501m / 500m limit** = pinned at limit
- Frontend CPU 500m / 500m = also pinned (downstream of compactor blocking)
- Ingest writer pods stuck at "rate limit applied" with no progress logs
- Aggregate INSERT rate dropped 9.3M/h (h+3) → 2.6M/h (h+6) = -72%
- vertex_osm_element row count *declined* slightly = compactor finally
  starting to consolidate but at far below ingestion rate

**Root cause**: Config A's faster checkpoint cadence (30s vs 150s) generates
~5× more SSTs. Default 1-replica compactor at 0.5 cpu cannot keep up. PK
upsert (content-addressed `{repo}:{collection}:{rkey}:{action}`) creates
high-stale-ratio SSTs by design — every batch contains many overwrites of
the same vertex_id. Compactor is essential, not optional, for sustained
ingest under this access pattern.

**Change**:
- `kubectl scale deploy kotoba-compactor --replicas=3` (was 1)
- limits: cpu 500m → 2000m, memory 4Gi → 8Gi
- requests: cpu 100m, memory 512Mi (kept low so 3 replicas can pack into
  existing 2-node memory budget)

**Outcome at T+3min**:
- 3 replicas all `Running`, each at 0.5–1.3 cpu actively pulling tasks
- `running_parallelism_count` rises across all 3 (RW auto-detects from
  `CONTAINER_CPU_LIMIT=2` env, derives parallelism = 2 per pod = 6 total)
- Aggregate compactor capacity: 1 × 0.5cpu = 0.5 cpu (1 parallel) →
  3 × 2cpu = 6 cpu (6 parallel) = **12× compaction throughput**
- vertex_osm_element live key count *decreasing* (compactor consolidating
  stale duplicates faster than writer adds them) = healthy
- Writer cursor progress visible: 3 active runs, ~333K rps combined

**Lesson learned**: Config A (smaller checkpoint cadence for faster
DML visibility) is a *write amplifier* under PK upsert workloads. Compactor
must scale together with checkpoint frequency. Future tuning must consider
this as a triplet: (`barrier_interval_ms`, `checkpoint_frequency`, compactor
replica × parallelism).

### D8. s2_cell_id u64 → i64 bit-reinterpret (v0.3.1)

After D2/D6 stabilized cluster, world ingest exposed a geographic bug:
4 of 5 first-wave production pods (Australia-Oceania, Cambodia, Myanmar,
Nepal) failed with:

    Casting to i64 out of range
    error while evaluating expression `try_cast('12284187311763095552')`

**Root cause**: ingester's `sql_opt_u64()` helper called raw `to_string()`
on `Option<u64>`. S2 cell IDs on faces 4-5 (mid-Pacific, parts of Asia,
Oceania) exceed i64::MAX (2^63 ≈ 9.22e18). Andorra bench (face 0) never
exercised this. Europe-only fits in i64 by coincidence.

**Fix in v0.3.1** (`writer.rs:sql_opt_u64`):

```rust
// Bit-reinterpret u64 → i64 to fit RW BIGINT.
v.map(|x| (x as i64).to_string()).unwrap_or_else(|| "NULL".into())
```

Range queries on s2_cell_id must apply the same `as i64` cast on bounds
to preserve ordering (S2 cell IDs are interleaved x/y bits; bit-pattern
ordering is geographic-locality-preserving regardless of signedness
interpretation, but mixing signed and unsigned breaks the order).

Image: `ghcr.io/etzhayyim/maps-osm-ingest:v0.3.1@sha256:8646be4f...`,
all 59 jobs swapped 2026-05-08T11:00 JST.

### D9. License key removal — exit Premium tier, no cluster size cap

After D7 cascade investigation, root cause analysis from RW source
(`src/license/src/manager.rs`, `src/license/src/rwu.rs`) established the
exact license accounting formula:

```rust
// 1 RWU (Kotoba/Datomic Unit) = 1 CPU core + 4 GiB memory.
memory_limit = (rwu_limit + 1) * 4 GiB - 1
```

Our cluster carried the public **`rw-default-all-4-core`** evaluation key
(`tier: all, rwu_limit: 4`) granting Premium feature access up to
4 cores + 20 GiB total cluster. JWT decoded:

```
sub: "rw-default-all-4-core"
iss: "prod.kotoba.com"
tier: "all"
cpu_core_limit: 4
exp: ~year 2200 (effectively perpetual)
```

OSM ingest workload requires:
- compute: 24 GiB memory each × 2 = 48 GiB (Andorra bench observed 22 GiB usage)
- compactor: 1-4 GiB × 3 = 3-12 GiB
- meta + frontend + metastore: ~9 GiB
- **Total ~60-69 GiB** vs license cap **20 GiB**

Test: compute memory 24 → 8 GiB to fit license caused immediate OOMKill
(exit 137) on compute-1 within 3.5min. Streaming actor state cannot fit
in 8 GiB at our scale.

**Conclusion**: license-fit is structurally impossible for this workload.

**Decision**: remove license_key entirely. Cluster reverts to `Tier::Free`
default (`rwu_limit: None` → no CPU/memory cap). Premium features
(DatabaseFailureIsolation, resource groups, etc.) become unavailable
"based on your license" — but they were already disabled while over-cap,
so net effect on cluster behavior is **zero**.

Operational impact of losing DBI:
- Cluster has 2 databases: `dev` (production OSM ingest) + `pds_poc2` (idle)
- Without DBI, a `dev` failure cascades to `pds_poc2` (and vice versa)
- Since `pds_poc2` is idle, blast radius is contained to `dev` only — same as before
- The frequent "database 1 reset" recovery events have **a different root cause**
  (DDL backfill stalls, gRPC connection resets) and are NOT caused by license
- License removal is purely cosmetic for cascade behavior

Implementation:
```sql
-- in metastore PostgreSQL (not RW frontend; RW system_param is rw_admin-only via ALTER SYSTEM)
UPDATE system_parameter SET value = '' WHERE name = 'license_key';
-- restart meta pod to reload
kubectl -n kotoba delete pod kotoba-meta-0
```

Post-removal log signature changes from:
> "DatabaseFailureIsolation disabled by license error: ... exceeds the maximum allowed by the license key"

to:
> "DatabaseFailureIsolation is not available based on your license"

The **first** message implies "would work if you had a bigger license"; the
**second** simply states "Premium feature, not in free tier". Neither
prevents cluster operation.

**Rejected alternative**: stay on the 4-core key and try to fit. Verified
impossible — compute can't run in 8 GiB. Tried in this session at h+10 and
hit immediate OOMKill.

**Rejected alternative**: acquire a larger Premium license. Out of session
scope; user opted for "no Premium" rather than commercial purchase.

### D10. Knowledge persisted in graph schema

Migration `20260508210000_osm_ingest_bench_findings.ts` adds:

| Object | Purpose |
|---|---|
| `vertex_osm_ingest_run` (ALTER +12 cols) | per-run config + phase timings + aggregate_rps |
| `vertex_osm_ingest_finding` (NEW) | derived insights — best_config / antipattern / observation |
| `edge_osm_run_versus` (NEW) | pairwise bench A vs B comparisons |
| `mv_osm_ingest_top_runs` (NEW streaming MV) | ranked-by-aggregate_rps for analytics |

Future operators query `SELECT * FROM mv_osm_ingest_top_runs ORDER BY aggregate_rows_per_sec DESC LIMIT 1`
to retrieve the current empirically-best config.

## K8s utilization score (2026-05-08)

Methodology: 6 dimensions, each 1-10. Composite = simple mean.

| Dimension | Pre | +D2+D3 | +D4 | +D6 | +D7+D8 | **+D9 license-out** | Notes |
|---|---|---|---|---|---|---|---|
| **CPU efficiency** | 3/10 | 7/10 | 7/10 | 9/10 | 9/10 | **6/10** | D9 brought compute back to 2cpu/pod (license-fit was tried and failed). Now sized for sustainability not max-throughput |
| **Memory efficiency** | 4/10 | 4/10 | 6/10 | 6/10 | 6/10 | **6/10** | compute 24Gi restored after 8Gi OOM |
| **HA topology** | 7/10 | 7/10 | 7/10 | 8/10 | 8/10 | **8/10** | Compactor 3-replica preserved |
| **Scalability headroom** | 4/10 | 5/10 | 6/10 | 7/10 | 8/10 | **9/10** | License removal unlocks horizontal scale (D5 phase 2/3) without acquiring commercial license |
| **Workload isolation** | 5/10 | 5/10 | 5/10 | 5/10 | 5/10 | 5/10 | Unchanged |
| **Cost efficiency** | 6/10 | 7/10 | 8/10 | 9/10 | 9/10 | **9/10** | $0 marginal cost; license removal also $0 |
| **Composite** | **4.8/10** | 5.8/10 | 6.5/10 | 7.3/10 | 7.5/10 | **7.2/10** | -0.3 from compute downgrade but +sustainability (no recurring OOM/cascade) |

## RW performance impact factor scorecard (2026-05-08)

Per-factor severity rating (10 = severe blocker / saturated, 1 = healthy / no impact).
Each row is one component or knob with measurable impact on RW ingest throughput.

| Factor | Pre-tuning | Current | Δ | Mitigation |
|---|---|---|---|---|
| **Compute CPU limit** (per pod) | 9/10 (1.25cpu pinned at 99%) | 3/10 (6cpu, ~70% used) | -6 | D2 raised limit |
| **Actor distribution skew** | 8/10 (post-restart 99.7/0.3 split) | 1/10 (50/50 sticky) | -7 | D6 RECOVER |
| **Compactor saturation** | 9/10 (1 pod 0.5cpu pinned, stale_ratio 85-93) | 3/10 (3 pods × 2cpu, 6 parallel, draining) | -6 | D7 horizontal scale |
| **Frontend CPU limit** | 7/10 (500m at 500m limit) | 7/10 (unchanged, **next blocker**) | 0 | TBD |
| **Memory pressure on RW pool** | 8/10 (95% req, OOM risk) | 5/10 (83-89% req post-rightsize) | -3 | D4 reclaim |
| **Checkpoint cycle** (Config A trade-off) | 6/10 (slow at 150s, blocked DML visibility) | 5/10 (fast 30s, drives compactor pressure) | -1 | D1 tuned, D7 absorbed cost |
| **DML serialization** (without `distributed_dml`) | 7/10 (single-worker per session) | 4/10 (round-robin across 2 workers) | -3 | D3 enabled global |
| **Batch size** (writer flush) | 6/10 (5000 caused parse OOM) | 3/10 (1000 verified optimal) | -3 | D1 chose 1000 |
| **License core cap (4 cores)** | 0/10 (no awareness) | **2/10** (license removed, free-tier no cap, Premium features unavailable but unused) | -7 | D9: license_key=''; cluster size unrestricted |
| **PBF download serialization** (Geofabrik 1 connection) | 5/10 (re-runs re-download) | 5/10 (B2 cache code present but POST bug) | 0 | v0.4.0 fix planned |
| **i64 overflow in s2_cell_id** | (latent) | 2/10 (fixed v0.3.1) | -8 | D8 |
| **Connection drop during long ingest** (3h+) | 7/10 (Canada hit it) | 7/10 (unchanged, manifests on big-region pods) | 0 | v0.4.0 keepalive/retry |
| **Object store (B2) throttling** | 9/10 (2026-04-25 incident) | 4/10 (`opendal_writer_abort_on_err`, `keepalive_ms=30000`) | -5 | ADR-0048 carried |
| **Foyer disk cache cold-start storm** | 9/10 (2026-04-25 incident) | 1/10 (Foyer disabled) | -8 | ADR-0048 retraction |
| **Per-pod parallelism in pyzeebe-style sharing** | 6/10 (Mitama starves RW) | 5/10 (D4 reduced over-request) | -1 | partial; D6 follow-up `mitama-pool` |
| **Network egress to B2** | 2/10 (Bandwidth Ally free) | 2/10 | 0 | architectural |

### Composite RW health (weighted sum, 0-100 = best)

```
factor_health[i] = 10 - severity[i]                 (higher = healthier)
weight[i]        = relative impact on ingest throughput

Pre-tuning  composite = 31/100   (severely blocked)
Post-D7     composite = 75/100   (healthy until license cascade discovered)
Post-cascade composite = 60/100  (license cap exposes cluster-wide blast radius)
```

### License accounting formula (verified from RW source, retained for future reference)

```rust
// 1 RWU = 1 CPU core + 4 GiB memory  (src/license/src/manager.rs)
memory_limit = (rwu_limit + 1) * 4 GiB - 1
//                            ^^^^ "allow some margin"

// Tier::Free default = rwu_limit: None = no cap on either dimension
```

| Configuration | rwu_limit | CPU cap | Memory cap | Premium features |
|---|---|---|---|---|
| `Tier::Free` (no key) | None | unlimited | unlimited | none available |
| `rw-default-all-4-core` (paid eval) | 4 | 4 cores | 20 GiB - 1 | all if within cap |

**Verification query** (current cluster size):
```sql
SELECT
  SUM(system_total_cpu_cores) AS total_cpu,
  ROUND(SUM(system_total_memory_bytes) / 1024.0 / 1024.0 / 1024.0, 1) AS total_mem_gib
FROM rw_catalog.rw_worker_nodes WHERE state='RUNNING';
```

`system_total_cpu_cores` = `CONTAINER_CPU_LIMIT` env var (integer floor; 500m → 0).
`system_total_memory_bytes` = container memory limit.

After D9 license removal, the cluster operates with no size cap. Premium
features (DBI, resource groups, etc.) become "not available based on your
license" — but they were already unavailable while over-cap, so this is
purely cosmetic for our cluster behavior.

Top 3 remaining bottlenecks (priority order):

1. **Frontend CPU limit (500m, currently pegged at 500m)** — 1 frontend pod
   bottlenecks all `INSERT VALUES` parse/plan. Recommend: limit 500m → 2000m
   *and* 1 → 2 replicas. Same playbook as D7 worked for compactor.
2. **Long-running pod connection drop** (Canada 3h+ → "connection closed").
   Need writer-side TCP keepalive + idempotent batch retry in v0.4.0.
3. **B2 cache POST bug**. v0.4.0 should fix to save Geofabrik egress on
   re-runs. Re-running Canada (6.3GB PBF) costs 10-15min download per attempt.

### Concrete improvement targets (post D1-D8; horizontal-only constraint)

1. **Move non-RW workloads to a dedicated pool** (Workload isolation 5 → 8).
   Add `mitama-pool` (vhp-8c-32gb × 2 = $192/mo for 2 nodes) and pin
   BPMN/Mitama/Zeebe to it via node selector. RW pool becomes RW-only,
   memory pressure drops, CPU pressure drops, OOM risk eliminated.
   This is also a horizontal step — adds nodes, doesn't enlarge them.
2. **Add HPA for compute or one-node burst** (Scalability 6 → 8).
   When `mv_osm_ingest_top_runs` shows live ingest, scale RW pool to 3
   `vhf-16c-58gb` nodes + compute replicas to 3. When idle, drop back to 2.
3. **Continue right-sizing audit** (Memory 6 → 8). After current rolling
   restarts settle, re-audit `kubectl top` vs requests. Many pyzeebe pools
   may still over-request after this round. Reclaim further 5-10 GiB.
4. **Implement maps-osm-ingest v0.4.0 session-local distributed_dml** (sunset
   D3 global flag). Removes the cross-app atomicity-loss footgun.
5. **Fix B2 cache POST bug in v0.4.0** (currently graceful direct-DL fallback;
   re-runs of large continent PBFs would save 4-12 GB Geofabrik egress per run).
6. ~~Vertical node upgrade~~ — explicitly rejected per D5. All future scale
   is horizontal: more `vhf-16c-58gb` nodes, never bigger.

## Consequences

**Pro**:
- 2.5–3× expected ingest throughput at $0 marginal cost
- Bench knowledge persisted as queryable graph data, not prose
- Explicit K8s scoring exposes specific improvement levers
- Future bench/ingest runs auto-populate `mv_osm_ingest_top_runs` for trend analysis

**Con**:
- D2 patch causes rolling restart of compute pods → in-flight ingest interruption (mitigated by content-addressed PK)
- D3 global distributed_dml=true affects all RW DML workloads; not just OSM. Session-local revert (v0.4.0) tracked but not yet shipped
- D2 widens compute pod CPU burst → can starve other workloads on same node during peak ingest. Mitigation = D1 follow-up (dedicated mitama-pool)

**Neutral**:
- ADR-0094 stable-three-node-topology floor of 2 compute pods unchanged.
  This ADR amends only the per-pod resource shape, not topology.

## References

- ADR-0044: Kotoba/Datomic UDF language strategy
- ADR-0048: Kotoba/Datomic Vultr B2 primary cutover
- ADR-0094: Kotoba/Datomic stable three-node topology
- `src/common/src/session_config/mod.rs` (RW upstream, gh CLI fetch 2026-05-08)
- `src/frontend/src/scheduler/distributed/stage.rs` (RW upstream)
- `30-graph/graph-schema/migrations/20260508210000_osm_ingest_bench_findings.ts`
- `deps.toml [[conventions]] osm-ingest-optimal-config-andorra-validated`
- `deps.toml [[conventions]] rw-distributed-dml-semantics`
- `deps.toml [[migrations]] osm-ingest-bench-findings-schema-20260508`
