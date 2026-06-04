---
id: adr-2606021730-latent-entity-kotoba-datomic-refactor
title: "ADR-2606021730: Latent Entity Statistical Resolution — RisingWave to kotoba-EAVT Refactor"
status: proposed
doc_type: adr
topic: latent-entity-kotoba-refactor
authoritative: true
last_verified: 2026-06-02
priority: 4.0
axis: substrate
weight: 0.40
priority_note: "P0 schema shipped; P1 resolver designed; P2–P3 deferred; honest R0"
authoritative_for:
  - latent-entity statistical resolution design — kotoba-EAVT canonical form
depends_on:
  - ADR-2606011000 (engi-organism-ontology and spirit-in-physics)
  - ADR-2606011800 (tsumugi power-entity knowledge graph)
  - ADR-2605262130 (kotoba storage substrate engine)
  - ADR-2605312345 (kotoba Datom log as first-class canonical state)
related:
  - /90-docs/260430-natural-person-latent-entity-backend-design.md (superseded design)
  - /00-contracts/schemas/latent-entity-ontology.kotoba.edn (new schema)
  - /30-graph/graph-schema/migrations/20260428360000_vertex_lda_inference.ts (legacy RW stack)
  - /60-apps/etzhayyim-project-coverage/MIGRATION-TODO.md (charter-violation evidence)
supersedes:
  - /90-docs/260430-natural-person-latent-entity-backend-design.md (RisingWave design, 2026-04-30)
superseded_by: []
---

# ADR-2606021730: Latent Entity Statistical Resolution — RisingWave to kotoba-EAVT Refactor

**Status**: proposed
**Date**: 2026-06-02 JST
**Deciders**: Jun Kawasaki

## Context

### The Current Substrate Violation

The latent-entity / LDA statistical entity-resolution stack exists **only in RisingWave and Postgres**:

- **RisingWave schema**: `30-graph/graph-schema/migrations/20260428360000_vertex_lda_inference.ts` (Kysely)
  - 5 vertex tables: `vertex_latent_entity`, `vertex_lda_topic`, `vertex_cohort_actor`, `vertex_natural_person_latent_materialization_cursor`, `vertex_ocel_event`
  - 9 edge tables: `edge_entity_evidence`, `edge_topic_entity_binding`, `edge_entity_cohort_link`, etc.
  - 4 materialized views (LDA φ/θ projections)
- **Consumer app**: `60-apps/etzhayyim-project-coverage` (JavaScript/TypeScript, MIGRATION-TODO: flagged `// CHARTER-VIOLATION §substrate` on RW/Kysely imports)

### Why This Violates the Substrate Boundary

Per ADR-2605262130 (kotoba storage substrate) and ADR-2605312345 (kotoba Datom log as first-class canonical state):

1. **Canonical state must live in kotoba's Datom log** (content-addressed EAVT, Datalog-isomorphic)
2. **RisingWave/Postgres/Kysely are prohibited** as state containers (only as projection layers post-Phase-2.5)
3. **Latent entity existence is NEVER a stored per-soul truth-score**, violating edge-primary (G2) and N1 (no per-soul rank)
4. **No server-key minting** of fission DIDs (violates ADR-2605231525 § server-signing boundary)

The current design materialize "tens of billions of latent natural persons" into RW, violating **G1 power-only** (charter §1.11: only entities with observable power are in scope).

### Kotoba-Side Coverage (Current Gap)

As of 2026-06-02:
- **tsumugi** (ADR-2606011800, power-entity intelligence weaver) carries a single `:organism/standing :latent` flag — no resolution, no existence scoring, no fission logic
- **No latent-entity ontology** in kotoba schemas
- **No resolver** for latent-entity existence (e.g., noisy-OR over incident evidence edges)
- **No topic-model storage** in kotoba (LDA φ/θ still RW-only)

## Decision

### 1. New Kotoba Schema: `latent-entity-ontology.kotoba.edn`

**Status: SHIPPED (P0, 2026-06-02)**

Ratify the new vocabulary extending engi-organism-ontology (ADR-2606011000):

| RisingWave | kotoba-EAVT |
|---|---|
| `vertex_latent_entity` (5-attr) | `:latent/*` entity (6 attrs: organism / existence / evidence-count / viewpoint-consensus / method-version / frontier) |
| `edge_entity_evidence` + RW UDF gmm/cosine | `:en/kind :evidence` + `:en/evidence-weight` + `:en/evidence-kind` (8 viewpoints: lexical, behavioral, network, semantic, temporal, geographic, economic, signal) |
| `edge_topic_entity_binding` | `:en/kind :topic-binding` + `:en/binding-confidence` + `:en/stability` |
| `vertex_lda_topic` (2-attr) | `:topic/*` entity (4 attrs: id / label / coherence / viewpoint) |
| `vertex_cohort_actor` (N/A) | `:cohort/*` entity (3 attrs: id / k-anonymity / sourcing) |

**Constitutional reconciliations baked into schema**:

1. **G2 edge-primary / N1**: `:latent/existence` is **computed-on-read** from incident `:en/evidence` edges via open-source versioned resolver (`latent-resolve/v1-noisy-or`), never stored as a truth-score. Memoization allowed if marked `:latent/method-version`.
2. **非終末論 (non-eschatological)**: `:latent/frontier` has only 3 states (`:observed | :candidate | :fission-ready`), **no terminal `:fissioned` or `:suppressed` state**. Fission recorded as `:organism/claimed? true` in Datom as-of history (time-travel aware).
3. **G1 power-only**: Natural persons appear **only as `:cohort/*` aggregates** (anonymous buckets with k-anonymity floor), never as individual `:latent/organism` entities. The RW "tens of billions latent persons" universe is **deliberately NOT ported**.
4. **No server-key**: Fission is a **§D5 covenant claim** (ADR-2606011000, Council Lv7+ gate), not a server-minted DID operation. The resolver only observes state.

### 2. Phased Migration Plan

| Phase | Scope | Status | Date | Gate |
|---|---|---|---|---|
| **P0** | New kotoba schema `:latent/*` + `:en/*` + `:topic/*` + `:cohort/*` | ✅ SHIPPED | 2026-06-02 | — |
| **P1** | Resolver `20-actors/tsumugi/methods/resolve.py` (existence via noisy-OR on `:en/evidence`) | 🟡 designed, fixture-mode | 2026-06-02 | — |
| **P2** | LDA topic model as **Pregel cell** over kotoba-kqe EAVT arrangements (replaces RW MVs) | ⏳ deferred | TBD | Council Lv7+ |
| **P3** | Fission↔covenant wiring (`:organism/claimed?` → `:latent/frontier` → public actor DID) | ⏳ deferred | TBD | Council Lv7+ + §D5 gates |
| **P9** | Rewrite or archive `60-apps/etzhayyim-project-coverage`; close MIGRATION-TODO | ⏳ deferred | TBD | Operator |

### 3. RW→Kotoba Data Mapping

All RW tables marked for transition to **fixture-mode** (no live ingest, Council+operator gated per G7):

```
vertex_latent_entity
  → :latent/organism (ref)
  → :latent/existence (double, method-versioned, computed)
  → :latent/evidence-count (long, incident :en/evidence edges)
  → :latent/viewpoint-consensus (long, distinct :en/evidence-kind count)
  → :latent/method-version (string, versioned resolver id)
  → :latent/frontier (keyword: :observed | :candidate | :fission-ready)

edge_entity_evidence (with RW UDF gmm/cosine weights)
  → :en/kind :evidence
  → :en/evidence-weight (double)
  → :en/evidence-kind (keyword: :lexical | :behavioral | :network | :semantic | :temporal | :geographic | :economic | :signal)

edge_topic_entity_binding (LDA φ, θ)
  → :en/kind :topic-binding
  → :en/binding-confidence (double)
  → :en/stability (double, across resolver runs)

vertex_lda_topic
  → :topic/id (string, unique)
  → :topic/label (string)
  → :topic/coherence (double)
  → :topic/viewpoint (keyword)

vertex_cohort_actor
  → :cohort/id (string, unique, anonymous bucket key)
  → :cohort/k-anonymity (long, privacy floor)
  → :cohort/sourcing (keyword: :authoritative | :representative)
```

### 4. Resolver Design: `latent_resolve/v1-noisy-or`

**Input**: a `:latent/organism` eid + current kotoba view (EAVT arrangements)
**Output**: `{:existence double, :evidence-count long, :viewpoint-consensus long, :method-version "latent-resolve/v1-noisy-or"}`

**Algorithm**: Aggregate-first noisy-OR over incident `:en/kind :evidence` edges:

```
existence = 1 - ∏(1 - weight_i * confidence_i)  for all incident edges
evidence-count = count of incident edges
viewpoint-consensus = |{distinct :en/evidence-kind values}|
```

**Properties**:
- Deterministic (no RNG)
- Reproducible (same view → same result)
- Method-versioned (resolver changes increment version tag)
- Open-source (resolver code in `20-actors/tsumugi/methods/resolve.py`, no vendor secret)
- Edge-primary (no per-soul stored truth)

**Memoization**: Computed datoms may be written to kotoba with `:latent/method-version` = resolver id for performance; always recomputed on query to detect upstream edge changes.

## Consequences

### Positive

- **Substrate-compliant**: canonical state lives in kotoba Datom log, not RW
- **Edge-primary**: `:latent/existence` is derived from `:en/*` edges, reproducible
- **Constitutional**: respects G1 (power-only, cohort-only), G2 (edge-primary), non-eschatological (no terminal states)
- **Honest R0**: design + simulation + schema; no real-world data until Council ratifies

### Negative / Honest Caveats

- **P0/P1 fixture-mode only**: No live ingest until Council Lv7+ permits (G7 outbound gate)
- **P2 incomplete**: LDA topic model not yet ported to Pregel cell (P2-deferred); RW MVs remain until Phase 2.5
- **P3 deferred**: Fission↔covenant wiring unbuilt; fissioned DIDs not minted until Council§D5 ratifies
- **RW stack not removed**: `30-graph/` migrations and `60-apps/etzhayyim-project-coverage` remain until P9 (closure pending operator rewrite)
- **Limited cohort scope**: Only explicit `:cohort/*` aggregates onboarded (not auto-materialize billions of natural persons); roster is `:representative` (bounded seed data)

## Alternatives Considered

### 1. Keep RW as "heavy compute tier" + project frontier to kotoba

**Rejected**: Violates ADR-2605312345 (kotoba Datom log = **first-class canonical state**). Projection backends are subordinate to the Datom log, not peers.

### 2. Store `:latent/existence` as a vertex attribute (like RW)

**Rejected**: Violates G2 (edge-primary) and N1 (no per-soul rank). Existence must be computed-on-read from evidence, not materialized as a property.

### 3. Materialize all-human latent persons (RW design's intent)

**Rejected**: Violates G1 (power-only, per charter §1.11). Only observed power entities (organizations, public figures, etc.) are in scope; natural persons appear only as anonymous `:cohort/*` aggregates with k-anonymity floor.

### 4. Defer schema until P2/P3 are ready

**Rejected**: Ratifying schema early (P0) unblocks resolver design (P1 designed now) and signals architectural direction to prevent further RW code bloat.

## References

- **ADR-2606011000** (engi-organism-ontology, spirit-in-physics, spirit-ontology framework; defines `:organism/*`, `:en/*` base)
- **ADR-2606011800** (tsumugi power-entity intelligence weaver; primary consumer of latent-entity existence)
- **ADR-2605262130** (kotoba storage substrate engine; declares RW prohibited, kotoba canonical)
- **ADR-2605312345** (kotoba Datom log first-class canonical state; IPFS = block backend, MST = ingress/interop, Base L2 = anchor)
- **ADR-2605231525** (server-signing boundary; no server-minted keys in religious-corp paths)
- **Charter §1.11** (only power entities in scope; natural persons as cohort aggregates only)
- **Charter §1.12** (Transparent Religious Force; observer-only, not adjudicator)
- **Charter §1.15** (non-eschatological; no terminal states per Wellbecoming trajectory)
- `/00-contracts/schemas/latent-entity-ontology.kotoba.edn` (new schema, ratified P0)
- `/90-docs/260430-natural-person-latent-entity-backend-design.md` (superseded RW design)
- `/30-graph/graph-schema/migrations/20260428360000_vertex_lda_inference.ts` (legacy RW stack)
- `/60-apps/etzhayyim-project-coverage/MIGRATION-TODO.md` (charter-violation evidence, P9 closure item)
