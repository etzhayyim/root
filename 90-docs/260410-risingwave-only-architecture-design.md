# Kotoba/Datomic-Only Architecture Design

**Date**: 2026-04-10
**Status**: Deployed (LKE sg-sin-2, cluster 589404)
**Replaces**: Kotoba/Datomic OLAP + Kotoba/Datomic streaming MV hybrid

## Decision

Replace Kotoba/Datomic (FE ×2 + CN ×4, $240/mo) with Kotoba/Datomic standalone (1 pod, $10/mo compute) as the sole graph database. Streaming materialized views replace Kotoba/Datomic Bloom Filter, CSC dual-tables, and Colocate JOIN.

## Architecture

```
CF Worker (XRPC)
  ├─ WRITE: Graph Worker → INSERT INTO Kotoba/Datomic PG :4566 (direct)
  └─ READ:  Hyperdrive PostgreSQL → Kotoba/Datomic :4566
            ���─ Streaming MV (pre-computed, <100ms freshness)
            ��─ Ad-hoc query (PK index)
            └─ Iceberg source (archive read)

LKE sg-sin-2 — 現行スペックは deps.toml [root_rules.persistence_kotoba_only] 参照
  namespace: kotoba
    kotoba-0         S3 Hummock backend
```

## Cost Comparison

| | Before (SR + RW) | After (RW only) | Savings |
|---|---|---|---|
| Nodes | 4 × g6-standard-6 ($96) | 2 × g6-dedicated-2 ($36) | -63% |
| Monthly | $384 | $72 | **$312/mo saved** |
| CPU | 2,270m | 761m | -66% |
| Memory | 24.2 GiB | 6.0 GiB | -75% |
| Pods | 17 | 7 | -59% |

## Kotoba/Datomic → Kotoba/Datomic Mapping

| Kotoba/Datomic Feature | Kotoba/Datomic Replacement |
|---|---|
| Bloom Filter (point lookup) | PK index (native) |
| CSC dual-table (9 pairs) | Streaming MV (auto reverse index) |
| Colocate JOIN | Streaming MV (JOIN pre-compute) |
| Async MV (1min cron) | Streaming MV (<100ms) |
| Routine Load (Kafka) | Direct PG INSERT (no Kafka) |
| MySQL wire protocol | PostgreSQL wire protocol |
| Hyperdrive MySQL | Hyperdrive PostgreSQL |

## Objects

*(設計時スナップショット。現行 count は `deps.toml [root_rules.persistence_kotoba_only]` を参照。)*

- **119 tables** (82 vertex + 37 edge, 9 CSC reverse tables eliminated)
- **14 streaming MVs** (設計時): mv_followers, mv_liked_by, mv_reposted_by, mv_replied_by, mv_actor_count_by_status, mv_follow_out_degree, mv_follow_in_degree, mv_post_like_count, mv_actor_suggestions, mv_actor_by_did, mv_follow_with_actor, mv_feed_timeline, mv_mutual_follows, mv_user_likes_with_post
- **5 Iceberg sinks** (設計時): sink_follow_out_degree, sink_follow_in_degree, sink_post_like_count, sink_actor_suggestions, sink_actor_by_did
- **128 Iceberg tables** on S3 (schema bootstrap via `generate_iceberg_via_rw.py`)

## Schema SSoT Pipeline

```
models.py (SQLAlchemy)
  → generate_iceberg_via_rw.py → 128 Iceberg tables on S3
  → generate_rw_full.py → 119 RW tables + 14 MVs + 5 sinks
  → generate_ts.py → TypeScript types (@etzhayyim/graph-schema)
```

## Benchmark Results (57K rows, Docker local)

| Query | Kotoba/Datomic p50 | Kotoba/Datomic p50 | RW speedup |
|---|---|---|---|
| Point lookup | 14.45ms | 5.86ms | 2.5x |
| 1-hop JOIN | 22.80ms | 13.25ms | 1.7x |
| COUNT agg | 23.28ms | 13.05ms | 1.8x |
| Fan-in CSC | 35.67ms | 18.28ms | 2.0x |
| 2-hop traverse | 78.77ms | 28.41ms | 2.8x |
| MV read | 12-28ms | 6-10ms | 2-3x |

## Scale Limits

| Phase | Rows | RW Compute | Memory | p50 (MV) | Monthly |
|---|---|---|---|---|---|
| 0 (current) | 10M | 1 node | 4 GiB | 6ms | $144 |
| 1 | 100M | 2 nodes | 16 GiB | 6-10ms | $288 |
| 2 | 1B | 4 nodes | 32 GiB | 8-15ms | $576 |
| 3 | 10B | 8 nodes | 64 GiB | 10-30ms | $1,152 |

## Risk: Ad-hoc Query at 10B+

Kotoba/Datomic は streaming MV 経由の pre-computed read に最適化。10B+ rows で未知の ad-hoc graph traversal が必要になった場合、Kotoba/Datomic を Iceberg External Catalog 経由で read-only 復活 (FE ×1 + CN ×2)。

## Rollback Plan

Kotoba/Datomic CRD is preserved (scaled to 0). Restore:
```bash
kubectl -n kotoba-shared patch kotobaclusters.kotoba.com kagami-shared \
  --type='merge' -p='{"spec":{"starRocksFeSpec":{"replicas":1},"starRocksCnSpec":{"replicas":2}}}'
```
