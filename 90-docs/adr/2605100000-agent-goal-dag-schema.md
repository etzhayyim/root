---
id: adr-2605100000-agent-goal-dag-schema
title: Agent Goal-DAG Schema (vertex_agent_topo_*)
status: active
doc_type: adr
topic: agent-goal-dag
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - agent-goal-dag-schema
related: []
supersedes: []
superseded_by: []
---

# ADR-2605100000: Agent Goal-DAG Schema (vertex_agent_topo_*)

**Status**: accepted (2026-05-10)
**Scope**: cross-app, generic
**Supersedes**: none. Complements `vertex_projector_flow_*` which models *runtime flow execution*; this ADR models *world-state dependency*.

## Context

Every autonomous agent that pursues a complex goal (kafun-bokumetsu, lawfirm,
shinka, society6, …) needs to reason about the dependency DAG of "what must
become true in the world before X is reachable". So far each app reinvented
this with hardcoded constants in handler code. That made the DAG invisible to
RisingWave (no MV), unobservable in yoro, and impossible to reuse across apps.

The 16-node kafun eradication DAG (L0 evidence → L1 capacity → L2 funding →
L3 execution → L4 measurement → L5 goal) made the lack acute: `Agent.tick`
needed Theory-of-Constraints ranking + ready-leaf detection, both pure
relational. Embedding this in TS handlers was wasteful when a single
streaming MV does the work.

## Decision

Adopt a generic 3-table + 2-MV schema for goal-DAGs. Per-app concrete
vertices link via `edge_agent_topo_concerns`.

### Tables

| Object | Promoted columns |
|---|---|
| `vertex_agent_topo_node` | `app_did`, `node_id`, `layer`, `category` (evidence/capacity/funding/execution/measurement/goal), `status` (planned/in_progress/blocked/done/abandoned), `bottleneck_rank` (1=tightest, 0=unranked), `kpi_weight`, `target_metric`, `target_value`, `target_unit`, `current_value`, `owner_actor_did`, `evidence_uri` |
| `edge_agent_topo_depends` | `src_vid` (dependent), `dst_vid` (prerequisite), `dep_kind` ∈ {hard, soft}, `weight` |
| `edge_agent_topo_concerns` | `src_vid` (topo node), `dst_vid` (concrete vertex), `relation` ∈ {tracks, funds, blocks_on}, `weight` |

### Materialised views

- `mv_agent_topo_ready` — nodes whose **hard** deps are all `done` *and* whose
  status is `planned` or `blocked`. Streaming, NOT EXISTS subquery; Agent.tick
  reads `WHERE app_did=… ORDER BY (bottleneck_rank, layer, kpi_weight DESC) LIMIT 1`.
- `mv_agent_topo_progress` — `(app_did, layer)` rollup of `done / total /
  weight_total / weight_done`. Bounded cardinality (apps × layers ≪ 1k).

### Indexes

`idx_topo_node_app_layer` `(app_did, layer, status)` ·
`idx_topo_node_status` `(status, bottleneck_rank)` ·
`idx_topo_node_owner` `(owner_actor_did)` ·
`idx_topo_depends_src` `(src_vid, dep_kind)` · `idx_topo_depends_dst` `(dst_vid)` ·
`idx_topo_concerns_src` `(src_vid, relation)` · `idx_topo_concerns_dst` `(dst_vid)`.

### App pattern

1. `magatama.jsonld` declares no extra triggers — topo state changes via the
   normal `vertex_agent_topo_node` re-INSERT (record-log semantics).
2. CF Worker `Agent.tick` queries `mv_agent_topo_ready` directly (pure SQL,
   bypasses LangGraph for selection). Writes `vertex_<app>_action` with
   `dispatch_hint = {"transport":"topo","node_id":<>,"layer":<>}`.
3. Concrete per-app vertices (`vertex_kafun_nursery`, `vertex_kafun_landowner`
   etc.) attach to topo nodes via `edge_agent_topo_concerns relation='tracks'`.
4. yoro public-by-default: every `vertex_<app>_action` row is mirrored to
   `app.bsky.feed.post` under the `owner_actor_did` of the chosen topo node.

### Status semantics

| Status | When |
|---|---|
| `planned` | Initial; eligible for `mv_agent_topo_ready` once deps clear |
| `in_progress` | Worker accepted the node — *excluded* from ready (not re-pickable) |
| `blocked` | Soft block; remains in ready (deps clear) but flagged in UI |
| `done` | Target metric met; unlocks downstream nodes |
| `abandoned` | Permanently retired; treated like `done` for downstream unblocking |

## Why not …

- … reuse `vertex_projector_flow_*`? Different concern: that's "this LangGraph
  graph has these compiled nodes". This is "this agent's *world model*".
  Conflating them couples runtime execution shape to goal structure.
- … encode in YAML / per-app constants? Loses observability (no MV ready
  query, no progress dashboard, no cross-app comparison). Loses the path-DID
  ownership trail (`owner_actor_did` per node).
- … use generic `[[heuristic_weights]]` in deps.toml? Doc-only, can't be
  joined against RisingWave for selection.

## Consequences

- Every new agent app should seed its goal-DAG into `vertex_agent_topo_node`
  on first deploy (idempotent re-INSERT).
- `kafun_tick` LangGraph chain becomes optional / legacy — pure SQL ranking
  is preferred. The chain is retained for richer downstream reasoning over
  the chosen node.
- Adds 3 base tables + 2 MVs + 7 indexes. Cardinality at scale: ~10
  apps × ~30 nodes × ~3 deps = ~900 rows total — negligible.

## Reference implementation

- Schema: `30-graph/graph-schema/sql_migrations/20260510010000_vertex_agent_topo_and_kafun_concrete.up.sql`
- Alembic: `r_20260510010000_vertex_agent_topo_and_kafun_concrete`
- First user: kafun-bokumetsu (16+5 nodes, 20+6 deps, applied 2026-05-10).
- App handler: `60-apps/etzhayyim-project-public-kafun-bokumetsu/appview/.../src/app.ts` `cmdTick()` Tier-A.
