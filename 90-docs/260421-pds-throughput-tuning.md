---
id: 260421-pds-throughput-tuning
title: PDS throughput tuning — Hyperdrive / RW frontend / Worker binding
status: active
doc_type: reference
topic: pds-infrastructure
authoritative: false
last_verified: 2026-04-21
related:
  - 260420-pds-commit-seq-race-analysis.md
---

# PDS throughput tuning — optimal settings audit (2026-04-21)

Follow-up to `260420-pds-commit-seq-race-analysis.md` residual issue (b): `sdk.pds.createRecord` 60% failure rate under 10-parallel burst, with animeka `writeDomain` catch-all swallowing `work-xxx` fallback rkeys.

## Layers inspected

1. **Cloudflare Hyperdrive** — CF edge pool → RW origin
2. **RisingWave frontend** — pg wire handler (parse/plan/route)
3. **RisingWave compute** — streaming MV execution
4. **PDS Worker (`etzhayyim-pds-2603241700`)** — XRPC → Kysely → Hyperdrive
5. **app Worker → PDS Worker binding** — CF service binding, same zone

## Current config (2026-04-21)

### Hyperdrive (`kagami-risingwave`, id `e84c0a2babe44fc7b74818e394b4b896`)

| Param | Value | Notes |
|---|---|---|
| `origin_connection_limit` | **60** | Shared across ALL Workers platform-wide |
| `host` / `port` | 172.236.132.11:4566 | Linode LKE frontend service |
| `caching` | disabled | Write path; caching disabled is correct |
| `mtls` | sslmode=require | TLS mandatory |

### RW frontend (`helm/values.yaml` `frontendComponent`)

| Param | Value | Notes |
|---|---|---|
| replicas | **1** | No HA, single pg wire termination |
| cpu limit | **500m** (0.5 CPU) | Very low — parses + plans + routes every query |
| memory limit | 2 GiB | Fine |

### RW compute

| Param | Value | Notes |
|---|---|---|
| replicas | 1 | GPU node constraint |
| cpu limit | 14 | Fine (16 vCPU node, 1 reserved) |
| memory limit | 48 GiB | Generous |
| `RW_PARALLELISM` | 14 (auto) | Streaming ops per MV |
| `streaming_parallelism` (session default) | 2 | **Low** — new MV DDL creates 2-way parallel MVs |

### RW cluster params

| Param | Value | Notes |
|---|---|---|
| `barrier_interval_ms` | 5000 | Checkpoint every 5s |
| `checkpoint_frequency` | 30 | S3 write every 150s |
| `force_two_phase_agg` | true | Cluster-wide agg distribution — good |
| `in_flight_barrier_nums` | 64 | Fine |
| `statement_timeout` | 120000 ms | Session; fine for writes |
| `idle_in_transaction_session_timeout` | 60000 ms | Session; fine |
| `implicit_flush` | false | Async writes — don't change (would add 5s/INSERT) |

### PDS Worker (`core.ts`)

| Param | Value | Notes |
|---|---|---|
| pg client | `HyperdriveDialect` (single `pg.Client`) | ADR-0007; **correct** — no pg.Pool |
| per-isolate seq mutex | ✅ added 2026-04-20 | `nextRepoCommitSeq` |
| retry attempts | 12 | Up from 4 |
| retry jitter | `+random(1..24)` | Skip contended slots |
| non-conflict error logs | ✅ added 2026-04-20 | `[repo-commit]` |

### app Worker → PDS binding

| Param | Value | Notes |
|---|---|---|
| transport | `BindingTransport` via `env.PDS_SERVICE` | CF service binding |
| timeout | none explicit | Inherits CF 25s hard timeout |
| signing | `signAtprotoJwt` per request | CPU cost per createRecord |

## Bottleneck diagnosis

Under 10 parallel `createWork`:

| Stage | Capacity | Saturation? |
|---|---|---|
| app Worker XRPC handler | CF isolates ×N | Low |
| app Worker → PDS binding | `env.PDS_SERVICE` RPC | **Limited by PDS Worker CPU** |
| PDS Worker handler | CF 30s CPU, ~100ms MST + sign + insert | **Serialized bottleneck** |
| PDS → Hyperdrive | 60 origin connections | **Platform-wide shared** |
| Hyperdrive → RW frontend | depends on frontend CPU | **0.5 CPU frontend — the lowest cap** |
| RW frontend → compute | 14 parallelism | Fine |
| RW INSERT commit | 5s barrier | Async (not per-request blocking) |

**Primary bottleneck: RW frontend 0.5 CPU.** Single pg wire handler at 500m CPU cannot parse/plan 10 concurrent INSERTs in a burst — requests queue at the pg protocol layer, Hyperdrive connections idle waiting, and when queue depth exceeds reasonable latency, the Worker binding times out / returns errors.

**Secondary bottleneck: Hyperdrive `origin_connection_limit=60` shared across platform.** If multiple apps (animeka + mangaka + yoro + ...) are all writing concurrently, 60 connections platform-wide saturates quickly.

## Recommended changes (ordered by ROI)

### Tier 1 — immediate, zero-risk additive (do first)

**(1) Bump Hyperdrive `origin_connection_limit`: 60 → 150**

```bash
npx wrangler hyperdrive update e84c0a2babe44fc7b74818e394b4b896 \
  --origin-connection-limit=150
```

- Gives CF edge more headroom before queueing
- RW frontend accepts up to ~100-200 connections at default libpq
- Cost: 0 — CF quota is free
- Risk: frontend CPU may spike if connections simultaneously send queries; mitigated by Tier 2
- Verification: ~3 min (RW takes ≥150s to settle)

### Tier 2 — helm upgrade (moderate impact, requires cluster access)

**(2) Bump frontend CPU: 500m → 2000m (2 CPU)**

`50-infra/linode/risingwave-iceberg/helm/values.yaml`:

```diff
 frontendComponent:
   replicas: 1
   resources:
     requests: { cpu: "100m", memory: 512Mi }
-    limits:   { cpu: "500m", memory: 2Gi }
+    limits:   { cpu: "2000m", memory: 2Gi }
```

- 4× parse/plan throughput
- GPU node has 14 available CPU, 6+ unused → room for this bump
- Risk: if node pressure changes, 2 CPU limit may not always be available; request stays 100m
- Verification: `helm upgrade` + ≥3 min + re-run 10-parallel test

**(3) Add frontend replicas: 1 → 2**

```diff
-  replicas: 1
+  replicas: 2
```

- Horizontal scale for burst absorption
- Hyperdrive round-robins across frontend endpoints (via K8s service)
- Risk: session state handled at frontend; 2 replicas means round-robin between them. `_repoCommitSeq` in app code doesn't care (each INSERT is independent), but if any app relies on session-pinned behavior (LISTEN/NOTIFY, cursors), review first
- Verification: `helm upgrade` + smoke test all apps' health

### Tier 3 — fundamental fix (large scope, future phase)

**(4) Switch `vertex_id` from `{repo}:seq:{seq}` to `{repo}:{collection}:{rkey}`**

Eliminates seq-based PK collisions entirely. `seq` becomes a strictly ordering column (with BIGINT DEFAULT nextval/SEQUENCE or similar), not PK. Migration + app code adjustments.

**(5) Use RW SEQUENCE (if available) or `INSERT ... SELECT COALESCE(MAX(seq),0)+1` atomic pattern**

Removes client-side seq allocation race entirely.

## Changes NOT recommended

| Change | Why not |
|---|---|
| Enable `implicit_flush` | Adds 5s latency per INSERT; write-heavy apps become unusable |
| Drop `barrier_interval_ms` to 1000 | Increases S3 Hummock write rate 5× → may retrigger the 2026-04-16 SlowDown storm |
| Bump `streaming_parallelism` session default | Affects new MV DDL; existing MVs retain their parallelism. Low ROI vs frontend CPU fix |
| `pg.Pool` in PDS Worker | ADR-0007 explicitly forbids — leaks 'error' events past fetch scope → CF 1101 |

## Verification protocol

RW takes ≥150s (barrier × checkpoint_frequency) for INSERTs to be visible in some read paths, and ~3 min for helm upgrade pod rollover. Always:

1. Apply change
2. Wait **≥5 min** (2× max propagation)
3. Run the 10-parallel `createWork` test (see `260420-pds-commit-seq-race-analysis.md` §Post-fix benchmarks)
4. `SELECT COUNT(*) FROM vertex_repo_commit WHERE rkey IN (...10 rkeys...)` — target 8-10/10 persistence
5. `kubectl top pod -n risingwave` — confirm frontend CPU headroom remains

## Rollback

- Hyperdrive: `npx wrangler hyperdrive update ... --origin-connection-limit=60`
- Frontend CPU: `helm upgrade` with old values → old values.yaml or `helm rollback`
- Replicas: `helm upgrade` replicas=1 → K8s scales down (unused replica removed)

Each change is independently revertible within ~2 min.

## Applied changes (2026-04-21)

### Tier 1 — NOT applied

Hyperdrive hard cap: `Invalid connection limit specified: (150). Please indicate a limit in the valid range (5-60). [code: 2021]`. **CF Hyperdrive `origin_connection_limit` maxes at 60** per config. Already at ceiling; no headroom available through Hyperdrive itself.

### Tier 2 — partially applied

1. ✅ **Frontend CPU 500m → 2000m** applied. Helm upgrade succeeded.
2. ❌ **Frontend replicas 1 → 2** reverted. Attempting 2 replicas evicted `compute-0` to Pending state (node memory pressure). Reverted to 1 replica.
3. ✅ **Compute memory limit 48Gi → 16Gi, request 40Gi → 14Gi** (unplanned but necessary). Previous values.yaml had compute request=40Gi / limit=48Gi, but node allocatable is only 32Gi (physical 64Gi minus k8s + GPU runtime reservations). RW_TOTAL_MEMORY_BYTES auto-binds to container limit and assert-panics when limit > node memory available. Reducing to 14/16 matches actual capacity. This was a **latent bug exposed by helm upgrade** — any future compute restart would have hit the same crash.

### Benchmark (post-fix, 2026-04-21 10:38 JST)

- Solo sequential writes: **2/2 persisted** (100%, no regression)
- 10-parallel `createWork` burst: **1/10 persisted** (10%, unchanged from pre-Tier-2)

### Conclusion

**Frontend CPU was NOT the bottleneck.** `kubectl top` showed pre-upgrade frontend running at 9m / 500m (1.8% utilization) during idle, and the helm upgrade did not improve the parallel-burst persistence rate. The residual 90% drop must be elsewhere:

- **Hyperdrive `origin_connection_limit=60`** — already at CF cap; shared platform-wide. Under 10-parallel burst from animeka + any concurrent mangaka/yoro/etc., edge pool can saturate.
- **PDS Worker CPU** — each createRecord does JWT signing + MST commit + multiple inserts + subscribeRepos dispatch + derive rules. CF Worker has 30s CPU wall-clock, not per-request budget; 10 concurrent requests may hit the isolate's CPU quota.
- **HyperdriveDialect single client** — 1 pg.Client per isolate. Serialized through single TCP. If 10 requests queue behind each other on the single client, later ones time out at 25s CF Worker hard timeout.

**Unblock strategies not yet tried**:

1. **Split PDS write path per-isolate**: have `writeRecord` use `getRepoDb()` with different clients keyed by collection hash, giving 4-8 concurrent pg clients per isolate. Risk: CF pg.Pool leak (ADR-0007), but manual round-robin through N `pg.Client` instances may avoid that trap.
2. **Hyperdrive with `@cloudflare/hyperdrive-compat` or direct pg pool** — bypass HyperdriveDialect and use pg.Pool with explicit error handler. High risk without regression testing.
3. **Queue writes via Durable Object single-writer** — serializing concurrency at the app layer. Strong consistency at the cost of throughput.
4. **Replace `${repo}:seq:${seq}` PK with content-based `${repo}:${collection}:${rkey}`** — eliminates PK collision as root cause (seq race becomes visible ordering issue, not collision). Migration + handler rewrite.

**Recommendation for next phase**: trace individual failed writes. Add a per-request `traceId` that flows animeka Worker → PDS Worker → Hyperdrive → RW, logged at each hop. Run the 10-parallel burst; grep CF Worker logs for the 9 failing traceIds to see which hop drops them. This reveals whether drop is at CF Worker CPU, Hyperdrive, pg.Client, or RW.

### Stability side-effect

The compute memory fix (40Gi→14Gi) removed a **latent crash** that would have triggered on the next unplanned compute pod restart. Previous values.yaml was a lying configuration; the actual running pod had the older correct config from prior deploys. Any helm upgrade or pod eviction would have applied the bad values.yaml and crashed compute. So this intervention was a net stability win even though it didn't solve the parallel-burst issue.

## Phase 3 — ROOT CAUSE + FIX (2026-04-21)

Used `wrangler tail` on the PDS Worker to capture `[repo-commit]` logs during a live 10-parallel burst. Smoking gun:

```
[repo-commit] seq=22118 repo=... rkey=3mjxvgfuaal2i ...
[repo-commit] seq=22118 repo=... rkey=3mjxvgfwlgs2i ...   ← same seq, different rkey
[repo-commit] seq=24857 repo=... rkey=3mjxvgfv5k22o ...
[repo-commit] seq=24857 repo=... rkey=3mjxvgfwsbk2w ...   ← same seq, 5 different rkeys
[repo-commit] seq=24857 repo=... rkey=3mjxvgfwv7c2w ...
[repo-commit] seq=24857 repo=... rkey=3mjxvgfsvbk2w ...
[repo-commit] seq=24857 repo=... rkey=3mjxvgg5bck2n ...
```

Different CF isolates read **different `MAX(seq)`** values (22117 and 24856 — gap of 2739 = other apps' commits in between) and independently computed clashing seqs. The mutex fixed intra-isolate, but inter-isolate collisions remained. `vertex_id = ${repo}:seq:${seq}` PK collided → 1 write succeeds, others throw PK conflict → retries exhaust → drop.

### Fix applied (PDS version `e1cc159a-df0b-4c7f-9c49-192bb3cdede6`, animeka `9084e584-7a0a-46c9-8e0a-db4f2f504998`)

1. **Content-addressed vertex_id** (core.ts):
   ```diff
   - vertex_id: `${repo}:seq:${seq}`,
   + vertex_id: `${repo}:${collection}:${rkey}:${action}`,
   ```
   Each `(repo, collection, rkey, action)` tuple has exactly one vertex_id. `seq` stays monotonic within isolate; seq duplicates across isolates have **zero impact** (consumer reads `ORDER BY seq ASC` which tolerates duplicates + gaps).

2. **Conflict = idempotent duplicate**: PK conflict now means same record already written → log `[repo-commit] duplicate record skipped` and return success. Retry loop replaced with single-shot + warn.

3. **App-side retry in animeka `writeDomain`**: 4 attempts × 250/500/1000ms exponential backoff around `sdk.pds.createRecord`. Since the PDS PK is content-addressed, retrying with the same rkey is idempotent.

### Final benchmark (2026-04-21)

| Metric | Pre-fix | Post mutex+jitter | Post content-PK | Post retry 3× (80/160ms) | **Post retry 4× (250/500/1000ms)** |
|---|---|---|---|---|---|
| Solo sequential | 100% | 100% | 100% | 100% | **100%** |
| 10-parallel (TID responses) | 10/10 | 10/10 | 5/10 | 8/10 | **10/10** |
| 10-parallel (persisted) | 1/10 (10%) | 2/10 (20%) | 5/5 | 8/8 | **10/10 (100%)** |

**Final: 10-parallel bursts now persist 100% end-to-end.** PDS version `e1cc159a-df0b-4c7f-9c49-192bb3cdede6` (content-PK) + animeka version `e98fce28-edf1-4019-99ca-4217576508b8` (4× retry).

### Vertex scope of fix

Surveyed other `vertex_repo_*` tables for the same seq-based PK anti-pattern:

- `vertex_repo_commit` — **was** affected, fixed (content-PK `${repo}:${collection}:${rkey}:${action}`)
- `vertex_repo_record` — OK, uses `uri` (already content-addressed via at-uri)
- `vertex_repo_block` — OK, uses CID (content-addressed by MST design)
- `vertex_repo_root` — removed 2026-04-14 (derived from commit log)

Only 1 table affected. Fix is complete for the PK collision class.

### Lesson

The PDS commit race isn't about `seq` contention — it's about **PK collision**. As long as the PK encodes seq, any clash in seq-computation causes data loss. Content-based PK removes the entire class of failure. The mutex/jitter fixes from 2026-04-20 were treating symptoms, not the root. Next time: start with `wrangler tail` + `grep "seq="` to see if seqs are colliding before inferring complex retry logic.

### Remaining work (minor)

- Per-request traceId for deeper observability across CF Worker hops (not blocking)
- Monitor mangaka & other apps for any residual commit-level issues — all should automatically benefit from the PDS content-PK fix
- Consider adopting content-addressed PK pattern for other `vertex_repo_*` tables
