---
id: adr-2605210000-yatabase-deploy-first-query
title: yatabase Deploy-First Query — streaming MV as pre-deployed graph traversal
status: accepted
doc_type: adr
topic: yatabase-query-architecture
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - yatabase-deploy-first-query-architecture
  - yata-deployQuery-executeDeployedQuery-lexicon
related:
  - adr-2605080000-yatabase-yata-retail-cloud
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605080000-yatabase-yata-retail-cloud
supersedes: []
amends:
  - adr-2605080000-yatabase-yata-retail-cloud
---

# Decision

yatabase adopts **deploy-first query** as its primary graph traversal model.
Tenants deploy a structured pattern spec once; the platform compiles it to
a streaming materialized view (MV) + indexes on the tenant's Kotoba/Datomic
database. Subsequent reads are `SELECT * FROM mv WHERE idx_col = $1 LIMIT $2`
— O(1), always-fresh, incrementally maintained by Kotoba/Datomic's streaming engine.

This replaces the planned ad-hoc Cypher/SPARQL runtime evaluation for the
primary query path. Cypher/SPARQL text parsing remains in scope as a future
*compiler front-end* that emits the same structured pattern spec.

## Problem

Kotoba/Datomic is a streaming OLAP database, not a graph engine. Ad-hoc
variable-depth traversal requires recursive CTE, which Kotoba/Datomic does not
support in streaming mode. Translating Cypher at query time also means each
request pays the join-planning cost on a hot path.

## Solution: deploy = compile + DDL; execute = index lookup

```
deployQuery(stepsJson, selectJson, indexOnJson)
  → compiler: pattern spec → CREATE MATERIALIZED VIEW + CREATE INDEX DDL
  → pod executes DDL against graphar schema in tenant DB
  → vertex_yata_deployed_query row inserted (status='ready')
  → quota: 1 MV slot consumed

executeDeployedQuery(queryId, bindJson, limit)
  → pod: SELECT * FROM graphar.mv_yata_{orgHash}_{queryHash}
         WHERE {bound_index_cols}
         LIMIT {limit}
  → returns rowsJson
```

## Constraints

| Rule | Value |
|---|---|
| Max hops | 8 (9 steps: v-e-v-e-v-e-v-e-v) |
| Min hops | 1 (3 steps: v-e-v) |
| Steps alternation | must be vertex → edge → vertex → … |
| Unbounded `[*]` | rejected at compile time |
| MV quota | per-plan limit (Free=5, Starter=20, Pro=100, Business=unlimited) |
| DDL execution | pod only (CF Worker never connects to Kotoba/Datomic) |
| Tenant isolation | per-org RW database `yata_<sha256(did)[:16]>` |

## MV naming

```
graphar.mv_yata_{orgHash8}_{queryHash8}
```
where `orgHash8 = sha256(orgDid)[:8]` and `queryHash8 = sha256(stepsJson+selectJson)[:8]`.
The name is deterministic — re-deploying same pattern is idempotent.

## Quota flow

```
Worker:  getQuotaStatus(orgDid, 'mv_slots') → {used, limit}
         if used >= limit → 429 with quotaExceededResponse
Pod:     after DDL success → INSERT vertex_yata_deployed_query
Worker:  quota increments on next read (from MV count query)
```

## Why not recursive CTE / AGE / Neo4j?

- Kotoba/Datomic does not support `WITH RECURSIVE` in streaming mode
- Apache AGE adds operational complexity and a separate query path
- Neo4j AuraDB is the right tool for exploratory unbounded traversal;
  yatabase targets high-throughput known-pattern workloads

## Positioning vs Neo4j AuraDB

| | Neo4j AuraDB | yatabase deploy-first |
|---|---|---|
| Query style | ad-hoc Cypher | deploy once, read many |
| Execute latency | ~10–100ms (graph traversal) | ~1ms (index lookup) |
| Throughput | moderate | high (streaming MV) |
| Data freshness | immediate | streaming (sub-second lag) |
| Variable depth | yes | bounded only (≤8 hops) |
| Best for | exploration, deep traversal | production, known patterns |

## Implementation phases

- **P0 (this ADR)**: structured pattern spec → MV + index. Lexicons deployed.
- **P1**: Cypher text → pattern spec compiler front-end (~3K LoC)
- **P2**: SPARQL SELECT → pattern spec compiler front-end
- **P3**: Bolt :7687 protocol (Neo4j driver compat)
