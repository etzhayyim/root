---
id: cohort-lineage-dual-source-consistency-260415
title: "Cohort Lineage Dual-Source Consistency (vertex_cohort_actor.derived_from ↔ edge_cohort_derived)"
status: active
doc_type: how-to
topic: cohort-evaluation
authoritative: false
last_verified: 2026-04-15
related:
  - adr-0026-agent-only-reverse-identity-topology
  - cohort-coverage-evaluation-baseline-260414
supersedes: []
superseded_by: []
---

# Goal

ADR-0026 fission 経路で生成される lineage が **2 箇所** に同時記録される運用前提の consistency 検査ルールを固定。

| Source | 型 | 役割 |
|---|---|---|
| `vertex_cohort_actor.derived_from` | column | 個体 actor row の親 cohort_did (genesis 時点で fixed) |
| `edge_cohort_derived` | edge table | parent cohort_did → fissioned individual_did の typed edge (`mv_cohort_lineage_depth` source) |

両者は `handleCohortFission` で同一 transaction では書かれず、別の INSERT で書かれるため **drift 可能性** がある。

# Drift パターン

| シナリオ | vertex_cohort_actor | edge_cohort_derived | 結果 |
|---|---|---|---|
| 正常 | row exists | edge exists | OK |
| edge insert 失敗 (catch だけで継続) | row exists | edge missing | mv_cohort_lineage_depth が under-count |
| vertex insert 失敗 (early throw) | row missing | (edge も書かれない) | OK (両方とも missing) |
| 別経路で edge のみ手動 INSERT | row missing | edge exists | mv が over-count、孤立 edge |

# Consistency 検査クエリ

## 1. edge missing (vertex 側にあるが edge 側にない)

```sql
SELECT v.cohort_did AS individual_did, v.derived_from AS parent_did
FROM vertex_cohort_actor v
LEFT JOIN edge_cohort_derived e
  ON e.src_vid = v.derived_from AND e.dst_vid = v.cohort_did
WHERE v.kind = 'fissioned'
  AND v.derived_from IS NOT NULL
  AND e.edge_id IS NULL
```

→ output 0 row が健全。1+ row なら fission 直後の edge insert が落ちた可能性。

## 2. orphan edge (edge 側にあるが vertex 側にない)

```sql
SELECT e.src_vid AS parent_did, e.dst_vid AS individual_did
FROM edge_cohort_derived e
LEFT JOIN vertex_cohort_actor v
  ON v.cohort_did = e.dst_vid AND v.kind = 'fissioned'
WHERE v.cohort_did IS NULL
```

→ output 0 row が健全。

## 3. parent invariance (子の derived_from が edge.src_vid と一致)

```sql
SELECT v.cohort_did, v.derived_from AS vertex_parent, e.src_vid AS edge_parent
FROM vertex_cohort_actor v
JOIN edge_cohort_derived e ON e.dst_vid = v.cohort_did
WHERE v.kind = 'fissioned' AND v.derived_from <> e.src_vid
```

→ output 0 row が健全。

# Repair 方針

| Drift | Repair |
|---|---|
| edge missing | `etzhayyim cohort repair-edge --did <individual>` (TODO) で `vertex_cohort_actor.derived_from` から edge を再生成 |
| orphan edge | `DELETE FROM edge_cohort_derived WHERE dst_vid NOT IN (SELECT cohort_did FROM vertex_cohort_actor WHERE kind='fissioned')` |
| parent mismatch | manual review (data corruption sign) |

# Scheduled Audit

cohort-watchdog cron tick (6h) に上記 3 query を追加し、drift 件数を OCEL `com.etzhayyim.cohort.lineageDrift` index に emit する。閾値超 (例: 10 件以上) で repair-edge を自動発火。

実装: `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` に `runCohortLineageAudit()` を追加 (次 iter)。

# References

- `30-graph/graph-schema/migrations/0053_vertex_cohort_actor.ts`
- `30-graph/graph-schema/migrations/0056_cohort_lineage_edges.ts`
- `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` `handleCohortFission`
- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
