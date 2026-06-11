---
id: adr-2605071700-graph-sos-intel-actor
title: "Graph SoS Intel Actor: continuous vertex / edge / mv / idx intelligence loop"
status: active
doc_type: adr
topic: graph-sos-intel
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - graph system-of-systems intelligence
  - vertex / edge / mv / idx topology observation
  - graph-sos-intel actor runtime contract
depends_on:
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
  - adr-2605061300-real-world-effect-channel-boundary
  - adr-2605011200-graph-expand-bpmn-llm-edge-inference
  - adr-2604261900-kotoba-ddl-backfill-path-topology
related:
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0002-graph-storage
supersedes: []
superseded_by: []
---

# ADR-2605071700: Graph SoS Intel Actor

**Date**: 2026-05-07
**Status**: Accepted
**Decision Owner**: `did:web:graph-sos-intel.etzhayyim.com`

## Context

The platform already has separate mechanisms for actor evolution, active
inference, intelligence fusion, and System-of-Systems diagnostics:

- `shinka` schedules actor heartbeat and evolution.
- `intel` fuses cross-domain intelligence feeds.
- `vertex_agent_*` tables store active-inference observations, beliefs, ticks,
  proposals, effects, and homeostasis.
- `etzhayyim systemofsystem` scans repo-level systems, interfaces, and health.

What is missing is a resident actor that continuously treats the graph itself as
an operational intelligence object: `vertex_*`, `edge_*`, `mv_*`, and `idx_*`
relations should be inventoried, reasoned over, and converted into auditable
findings and recommendations.

## Decision

Introduce `graph-sos-intel` as a T1 MCP-composed actor.

The actor owns graph/intel observations about relation topology, index coverage,
materialized-view read models, and System-of-Systems drift. It does not execute
heavy DDL directly. Heavy DDL remains behind the existing Kotoba/Datomic DDL queue
and background-DDL governance.

## Runtime Contract

`graph-sos-intel` runs four surfaces:

- `cron R/PT15M`: inventory `vertex_*`, `edge_*`, `mv_*`, and `idx_*`, then write
  a compact `vertex_graph_sos_intel_snapshot`.
- `cron R/PT6H`: produce a human-readable topology briefing.
- `com.etzhayyim.apps.graphSosIntel.health`: return latest snapshot and rollup.
- `com.etzhayyim.apps.graphSosIntel.listRelations`: inspect current graph relations.
- `com.etzhayyim.apps.graphSosIntel.listFindings`: inspect open findings.

## Data Model

New graph tables:

- `vertex_graph_sos_intel_snapshot`
- `vertex_graph_sos_intel_finding`
- `edge_graph_sos_finding_affects_relation`
- `vertex_graph_sos_relation_inventory`

Catalog reads:

The actor reads `information_schema.tables` and `pg_indexes` directly during its
tick instead of creating catalog views. Findings, snapshots, and optional
relation inventory observations are normal graph rows so the actor can be
audited like other T1 actors.

## Guardrails

- The actor may recommend indexes, MVs, backfills, or table retirement.
- The actor must not run `CREATE INDEX`, `CREATE MATERIALIZED VIEW`, destructive
  `ALTER`, or `DROP` directly from its T1 manifest.
- External effects must go through the active-inference / BPMN gate model.
- Snapshot payloads must remain compact; raw catalog dumps stay queryable via
  catalog queries and are not copied wholesale into actor rows.

## Consequences

Positive:

- Gives the platform a dedicated graph topology and SoS intelligence loop.
- Keeps analysis data in `vertex_*` / `edge_*` form rather than ephemeral logs.
- Separates recommendation from DDL execution.

Tradeoffs:

- Catalog views are runtime-environment dependent and should be treated as
  observability surfaces, not migration-critical business tables.
- Initial reasoning is coarse. Deeper cycle detection, freshness lag analysis,
  and DDL queue correlation can be layered later through BPMN workers.
