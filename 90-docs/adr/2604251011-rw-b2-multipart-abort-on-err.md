---
id: adr-2604251011-rw-b2-multipart-abort-on-err
title: "ADR: RW Hummock on B2 — opendal_writer_abort_on_err + s3.keepalive_ms tuning"
status: accepted
doc_type: adr
topic: rw-hummock-b2-multipart-reliability
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - rw-object-store-multipart-abort-policy
  - rw-s3-keepalive-for-b2
related:
  - adr-0048-risingwave-vultr-b2-primary
  - adr-0049-shared-udf-pool
  - adr-2604231349-timestamp-numbering-policy
supersedes: []
superseded_by: []
amends:
  - adr-0048-risingwave-vultr-b2-primary
---

# ADR: RW Hummock on B2 — opendal_writer_abort_on_err + s3.keepalive_ms tuning

## Context

ADR-0048 cut RisingWave's primary state store over to Backblaze B2
(`b2://etzhayyim-nats/linode/etzhayyim-iceberg/risingwave/state/`,
us-west-004) on Vultr VKE LAX. Single `vhf-8c-32gb` node pool, distributed
RW chart, free egress via Bandwidth Ally.

Steady-state operation has been clean. Under bursty / sustained ingest
(e.g. GLEIF Golden Copy bulk into `vertex_legal_entity`, or any
multi-minute write loop), we observe a degenerate cluster mode:

| Metric | Healthy | Observed |
|---|---|---|
| Probe INSERT visibility (`vertex_repo_commit`) | ~10 s | **228 s** |
| `barrier_interval_ms × checkpoint_frequency` budget | 1 s × 10 = 10 s | — |
| `cluster marked as blocked / ready` flap rate | 0 | 3-6 / 10 min |
| B2 `S3Error code=NoSuchUpload` on SST sync | 0 | 7 / 10 min |
| Effective sustained write throughput | nominal 50-500 rec/s | **2-3 rec/s** |
| Recovery path | not needed | only after ~1 h B2 multipart TTL OR compute pod restart |

Compute / network is healthy through this:
- compute-0 / compute-1 sit at ~28-32 % CPU and RAM
- Vultr LAX → B2 us-west-004 RTT = 38-46 ms sequential, 41-69 ms × 10 parallel
- B2 bucket has no per-rps quota; HEAD probes succeed at all observed concurrencies
- All 3 VKE nodes Ready

## Root cause

RisingWave's Hummock SST sink is `opendal://s3` against B2. The default
RW config has:

    [storage.object_store]
    opendal_writer_abort_on_err = false
    
    [storage.object_store.s3]
    keepalive_ms = 600000   # 10 min

When a streaming SST upload hits a transient error (TCP `connection
closed before message completed` from B2 nginx idle drop, or any
upstream blip), `opendal_writer_abort_on_err = false` keeps the
multipart upload session **open** and the writer retries against the
*same* multipart ID. B2 silently aborts a multipart upload that goes
inactive for ~1 hour. RW does not learn this until its next attempt
returns `404 NoSuchUpload`.

When that happens, RW's barrier scheduler flips `cluster marked as
blocked`, all DML rejects with `DML is not permitted during cluster
recovery (no available table reader in streaming executors)`, and
checkpoint-commit stalls until either the bad multipart session ages
out (~1 h) or a compute pod restart resets the in-memory writer state.

Reads against this state observe stale rows for the duration: an
INSERT that the frontend acked may take several minutes (we measured
228 s on `vertex_repo_commit`, 286 s on `vertex_bpmn_lexicon_binding`)
to become visible, and DML during the window is occasionally **lost**
(acked but not persisted across the next checkpoint).

The OpenDAL retry-on-`writer.close()` path is the upstream pathology
(see opendal commits mailing list), but RW exposes a knob — also see
RW's `src/config/example.toml` — to short-circuit it: abort the
in-flight multipart on first error so the next attempt opens a fresh
session.

Separately, `s3.keepalive_ms = 600000` (10 min) is longer than B2
nginx's idle close window (~60 s), so RW holds dead connections in
its pool, and the first SST sync after an idle period hits a TCP
`connection closed before message completed` error. Tightening
keepalive below the B2 idle window avoids that class of spurious
failure.

## Decision

Add the following block to RisingWave's `[storage.*]` configuration in
`50-infra/vultr/risingwave/helm/values.yaml`:

    [storage.object_store]
    opendal_writer_abort_on_err = true
    
    [storage.object_store.s3]
    keepalive_ms = 30000

Apply via `helm upgrade`. The compute and compactor pods rolling
through this revision pick up the new config; verify with
`kubectl logs … | grep "ObjectStoreConfig"` — the boot-time RwConfig
dump shows `opendal_writer_abort_on_err: true` and `keepalive_ms:
Some(30000)`.

Also bump compactor replicas 1 → 2 (this revision only adds defense in
depth — does not address the root cause above):

    compactorComponent:
      replicas: 2

so that bursty SST emit doesn't backlog behind a single compactor pod
during catch-up after a B2-induced barrier flap.

## Consequences

Positive:
- Stale multipart upload sessions are immediately released on first
  error → next sync attempt opens a fresh session → no `NoSuchUpload`
  cascade → no `cluster marked as blocked` flaps → DML visibility
  stays at the configured `barrier_interval_ms × checkpoint_frequency`
  budget (~10 s) under sustained load.
- TCP keepalive 30 s < B2 idle 60 s → RW always sees live connections
  → the `connection closed before message completed` error class
  drops to ~0.
- Compactor 2× → 2 replicas absorb burst SST output, halving the
  compaction backlog window after a write spike.
- No data path change; `vertex_*` tables, MV graph, and Hummock layout
  remain untouched. Helm upgrade is config-only, no migration.

Negative / cost:
- `opendal_writer_abort_on_err = true` does an explicit `AbortMultipartUpload`
  RPC to B2 on every transient write error. Adds 1 B2 Class B
  transaction per abort; cost is negligible (B2 Class B = $0.004 /
  10k transactions; estimated < $0.01/month at our error rate).
- A second compactor adds ~$10/mo (2c req × 4 GiB) — fits inside the
  existing `risingwave-pool-32gb` headroom (3 nodes × 8 vCPU × 32 GiB,
  current usage ~30 % per node).
- Slightly more aggressive keepalive churn — measurable in connection
  count, not in cost.

Reversal:
- Set `opendal_writer_abort_on_err = false`, `keepalive_ms = 600000`,
  `compactorComponent.replicas = 1` and `helm upgrade`. Reverts
  cleanly within one rollout.

## References

- RW boot-time config dump on `risingwave-compute-0` after this
  revision: `ObjectStoreConfig { … opendal_writer_abort_on_err: true,
  s3: S3ObjectStoreConfig { keepalive_ms: Some(30000), … } }`
- RW `src/config/example.toml`:
  https://github.com/risingwavelabs/risingwave/blob/main/src/config/example.toml
- OpenDAL retry-on-close pathology (mailing list discussion):
  https://www.mail-archive.com/commits@opendal.apache.org/msg24602.html
- B2 S3 abort multipart upload semantics:
  https://www.backblaze.com/apidocs/s3-abort-multipart-upload
- This session's diagnostic data: probe INSERT visibility 228 s on
  `vertex_repo_commit`, 286 s on `vertex_bpmn_lexicon_binding`,
  GLEIF sub-pilot at 50 rec/s nominal degraded to 2-3 rec/s sustained,
  7 NoSuchUpload errors / 10 min on compute-0, 3-6 barrier flaps /
  10 min on meta-0.

## Notes for next session

- Re-run a 5-10K GLEIF sub-pilot after 1 h soak to confirm the
  sustained write rate recovers toward the 50-100 rec/s range. If yes,
  Task #21 (GLEIF Phase 2 bulk, 3.29 M rows) becomes viable as a
  multi-hour overnight run instead of multi-week grind.
- If sustained throughput still < 20 rec/s after this fix, the
  remaining bottleneck is one of: (a) RW MV cascade memory limit on a
  single compute pod under bursty INSERT, (b) B2 endpoint packet-loss
  outside our control, or (c) compactor backlog despite 2 replicas. We
  would investigate in that order.
- Pair with planned weekly compute pod recycle (independent
  intervention) — even with abort-on-err, periodic restart guards
  against accumulated state in OpenDAL's connection pool.
