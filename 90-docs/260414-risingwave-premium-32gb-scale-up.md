---
id: doc-260414-kotoba-premium-32gb-scale-up
title: Kotoba/Datomic Premium 32GB Scale-Up — Runbook & Post-Mortem
status: active
doc_type: how-to
topic: infrastructure
authoritative: true
last_verified: 2026-04-14
related:
  - adr-0020-kotoba-premium-single-node
  - 30-graph/graph-schema/migrations/0025_world_coverage_live_mv.ts
---

# Kotoba/Datomic Premium 32GB Scale-Up — Runbook & Post-Mortem

## Goal

Document the end-to-end procedure used on 2026-04-14 to migrate the
Kotoba/Datomic production cluster from `g6-dedicated-4 × 2` (8 vCPU / 16 GiB
total) to `g7-premium-16 × 1` (Premium 32GB) in a zero-downtime fashion,
and record the observations that drove the design.

## Scope

- Cluster: `lke589404` (LKE in `sg-sin-2`).
- Namespace: `kotoba`.
- Components: Kotoba/Datomic compute/compactor/meta/frontend, external
  PostgreSQL metastore.

## Executive Summary

Streaming MV backfill (migration 0025 world coverage) + bulk INSERT from
`etzhayyim collect` triggered 3 compute-pod OOM restarts in a 3-hour window.
Per Kotoba/Datomic official guidance, scaled up to Premium 32GB single-node.
Net cost delta: **+$202/mo** ($144 → $346). Outcome: stable MV execution,
block cache locality, single-node shuffle.

## Pre-migration symptoms

| Observation | Evidence |
|---|---|
| compute-0 OOM restart × 3 | `kubectl get pod kotoba-compute-0` RESTARTS 3 in 3h |
| Barrier latency warnings | `NOTICE: CREATE MATERIALIZED VIEW has taken more than 30 secs, barrier latency might be high` during backfill |
| MV build failure mid-backfill | `gRPC request to stream service failed: connection reset` while building `mv_world_record_per_host` |
| Block cache thrash | Frequent Hummock `cache miss → S3 GET` in compute logs |

## Decision

See ADR 0020. Summary: vertical scale to **Premium 32GB × 1** with all
Kotoba/Datomic components consolidated on one node.

## Migration runbook

Automated via `50-infra/linode/kotoba-iceberg/helm/scale-up-premium.sh`.
Six phases; zero downtime on the read path.

### Phase 0 — Preflight

- `kubectl`, `helm`, `linode-cli` installed and authenticated.
- `LINODE_CLI_TOKEN` / `LINODE_API_KEY_*` exported.
- `values.yaml` already updated for Premium 32GB (this commit).

### Phase 1 — Create Premium pool

```bash
linode-cli lke pool-create "$LINODE_CLUSTER_ID" \
  --type g7-premium-16 \
  --count 1 \
  --tags rw-compute-premium \
  --text --no-headers
# Then label the new node from kubectl:
kubectl label node <new-node> rw-role=compute rw-compute-premium=true --overwrite
```

### Phase 2 — Scale to `replicas=2`

```bash
helm upgrade kotoba kotobalabs/kotoba --version 0.2.49 \
  -n kotoba -f values.yaml \
  --set computeComponent.replicas=2
```

Two compute pods run concurrently — one on old node, one on Premium —
during Kotoba/Datomic actor rebalance. Reads stay online.

### Phase 2a — Transient 2-Premium capacity

**Observed issue during migration**: the new `values.yaml` compute pod
requests (8 vCPU / 24 GiB) do not fit on the old `g6-dedicated-4` (4 vCPU
/ 8 GiB), so both compute-0 and compute-1 must schedule on Premium nodes.
Premium 32GB can host only one 24 GiB-request pod at a time. Mitigation:

```bash
# Temporarily scale Premium pool to 2 nodes during the transition.
linode-cli lke pool-update 589404 <premium-pool-id> --count 2 --text
```

This adds ~$0.52/hr of overlap cost (negligible).

### Phase 3 — Drain old pool

```bash
kubectl cordon <old-compute-node>
kubectl cordon <old-control-node>
kubectl label node <old-compute-node> rw-role- --overwrite
kubectl label node <old-control-node> rw-role- --overwrite
```

### Phase 4 — Consolidate control pods (single-node mode)

Update `values.yaml`:

- `metaComponent.nodeSelector: rw-role=compute` (was `control`).
- `frontendComponent.nodeSelector: rw-role=compute` (was `control`).
- `compactorComponent.nodeSelector: rw-role=compute` (was `control`).
- `computeComponent.resources.requests: { cpu: 6, memory: 20Gi }` to
  leave room for the control-plane pods.

```bash
helm upgrade kotoba ... --set computeComponent.replicas=1
# Then evict the old pods so they reschedule to Premium:
kubectl -n kotoba delete pod \
  kotoba-compactor-<old> \
  kotoba-frontend-<old> \
  kotoba-meta-0 \
  kotoba-metastore-<old>
```

StatefulSet drops compute-1 (highest ordinal); compute-0 ends up on the
Premium node chosen as the "keeper" (the one it was already running on).

### Phase 5 — Shrink Premium pool

```bash
linode-cli lke pool-update "$LINODE_CLUSTER_ID" <premium-pool-id> --count 1 --text
```

LKE removes the cordoned (unused) Premium node.

### Phase 6 — Delete old pool

```bash
linode-cli lke pool-delete "$LINODE_CLUSTER_ID" <old-pool-id>
```

### Validation

```bash
kubectl get nodes -L rw-role -L rw-compute-premium
kubectl -n kotoba get pods -o wide
psql "postgres://root@<pf>:14566/dev?sslmode=disable" \
  -c "SELECT domain, collected, world_total FROM mv_world_coverage_live
      WHERE collected > 0 ORDER BY collected DESC LIMIT 10;"
```

Expected: 1 node, 5 pods all on that node, `mv_world_coverage_live`
returning nonzero rows.

## Observations / lessons

1. **Kotoba/Datomic streaming vnode mapping lag.** Immediately after compute
   restarts, MV reads fail with `Streaming vnode mapping not found for
   fragment N` for 30-90 s. Retry loop required in ops tooling.
2. **pgx extended protocol hang on MV reads.** After a prior compute
   restart, `SELECT FROM mv_world_coverage_live` via pgx Extended
   Protocol hung forever; Simple Protocol worked. `db.RawQuery` now
   uses Simple Protocol; `collect.go` does likewise.
3. **Numeric columns from SUM/COUNT come back as `pgtype.Numeric`**
   (not int64) — our Go CLI needed a `Numeric → Float64Value` branch in
   `toInt` to avoid silent zero-reads.
4. **StatefulSet ordinal + nodeSelector quirk.** With both compute pods
   forced onto Premium and only one Premium node available, `compute-0`
   hangs Pending. Pool resize to 2 Premium during the overlap window is
   the clean fix; running with smaller transient compute requests is
   possible but complicates values.yaml rollback.

## Cost summary

| State | Pool composition | $/mo |
|---|---|---|
| Pre-migration | g6-dedicated-4 × 2 (control + compute) | $144 |
| Transient (2 Premium overlap, ~30 min) | g6-dedicated-4 × 2 + g7-premium-16 × 2 | peak ~$836/hr-prorated |
| Final (single-node) | g7-premium-16 × 1 | **$346** |

## References

- `50-infra/linode/kotoba-iceberg/helm/values.yaml` — live config.
- `50-infra/linode/kotoba-iceberg/helm/scale-up-premium.sh` — script.
- https://docs.kotoba.com/performance/performance-best-practices
- ADR 0020 — Decision record.
