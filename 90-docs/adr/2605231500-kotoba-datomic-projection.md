---
id: adr-2605231500-kotoba-datomic-projection
title: "ADR-2605231500: kotoba-datomic-projection — regenerable cache layer for hot-path queries (SUPERSEDED by 2605262130)"
status: superseded
doc_type: adr
topic: kotoba-datomic-projection
authoritative: true
last_verified: 2026-05-23
priority: 8.5
axis: substrate-boundary
weight: 0.9
authoritative_for:
  - "kotoba-datomic-projection definition and conformance levels"
  - "ADR-2605172000 hot-path escape hatch (when RW / Lance / Iroh / index serving range queries is permitted)"
  - "Bluesky AppView analog — PDS = state, projection = derivable cache"
depends_on:
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
related:
  - adr-2605222330-etzhayyim-com-substrate-violation-transition-window
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
supersedes: []
superseded_by:
  - adr-2605262130-kotoba-storage-substrate-unification
---

# ADR-2605231500: kotoba-datomic-projection — regenerable cache layer for hot-path queries

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

[ADR-2605172000](/90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) mandates kotoba substrate
(`AT Protocol MST + IPFS + Base L2 anchor`) as the **state store**. [ADR-2605231400](/90-docs/adr/2605231400-kotoba-datomic-holochain-iso-substrate.md)
names the composed architecture `kotoba-datomic` and defines three conformance levels
(L0 nominal / L1 witnessed / L2 anchored). Neither ADR addresses **derived read
paths** — i.e., the question:

> If `kotoba-datomic-chain` is the source of truth and `kotoba-datomic-dht` is the content
> store, **how does the maps app serve a sub-100ms bbox spatial query that
> requires scanning millions of `vertex_spatial` rows with a label filter and
> a PostGIS-style geometry intersection?**

MST prefix scan cannot do this. IPFS DAG traversal cannot do this. Per the
[`MIGRATION-TODO.md`](../../60-apps/etzhayyim-project-maps/MIGRATION-TODO.md) Tier C
inventory, ~60 of 172 maps commands fall into this category (`tileGeoJson`,
`getChunk`, `nextDeparturesAtStop`, `realtimeDelaysAtStop`, `graph_traverse`,
`graph_neighbors`, `search_resources`, `infra_query`, `spatial_event_query`,
`spot_search`, `sensor_query`, etc.).

This pattern is not unique to maps. Any app with range / aggregate / spatial /
full-text / vector-similarity read patterns will hit it — including yoro, yorishiro,
murakumo, joucho, etzhayyim-k2, baien, and the BMC commercial-evidence surfaces
in yatabase.

The pattern is also already solved by the broader AT Protocol ecosystem:
**Bluesky AppView**. Bluesky's PDS is the state store; the AppView is a
PostgreSQL-backed derived index that consumes the PDS firehose and produces
optimized read paths. The AppView is **not** the source of truth — drop it,
replay the firehose, get an identical AppView back.

This ADR generalizes that pattern as `kotoba-datomic-projection` and defines when it
is Charter-compliant to use RW / Lance / Iroh-synced docs / in-memory indices
for hot-path reads.

## Decision

A `kotoba-datomic-projection` is a derived read-path artifact that:

1. is **deterministically rebuildable** from `kotoba-datomic-chain` (PDS MST) and
   `kotoba-datomic-dht` (IPFS) without any operator-held state, AND
2. is **never the only place a write lives** — every write hits `kotoba-datomic-chain`
   first and only then propagates into the projection, AND
3. is **explicitly marked** in code (`// kotoba-datomic-projection` line comment OR a
   `kotoba-datomic-projection.edn` manifest in the projection's directory) so the
   substrate-boundary lint allow-lists it.

If all three properties hold, the projection MAY use any storage technology —
including those listed in ADR-2605172000 `state_prohibited` — without violating
the substrate boundary, because the projection is **derived**, not **canonical**.

### Three conformance levels

Mirroring kotoba-datomic's L0/L1/L2:

| Level | Requirements |
|---|---|
| **L0-projection nominal** | (1) and (3) hold. Rebuild procedure is documented (a markdown runbook is sufficient). No automated rebuild required. |
| **L1-projection automated** | L0 + (2) verified by lint OR by structural guarantee (e.g., the projection consumer subscribes to the PDS firehose and refuses out-of-order writes). Rebuild tool exists and is exercised in CI. |
| **L2-projection verified** | L1 + cross-validation tool that replays a randomly-chosen 1% slice and asserts the projection is byte-identical (modulo intentional non-determinism, which must be enumerated in the projection manifest). |

The current `60-apps/etzhayyim-project-maps/` RW-backed reads are **pre-L0**
(no manifest, no rebuild runbook, no firehose subscription). Phase 4-5 of the
maps migration brings the Tier C commands to **L0-projection** first, then to
L1.

### Allowed substrates for projections

| Substrate | Suitable for | Notes |
|---|---|---|
| Kotoba/Datomic | range / aggregate / window / spatial queries | the canonical Bluesky-AppView analog; firehose → SQL materialized views |
| Lance (via `50-infra/yata/`) | mixed graph + vector queries | already in use for `yatabase`; reframe as projection |
| Iroh docs | intra-cohort sync, cross-replica consistency | content-addressed, Bao-verifiable; good for projection between Murakumo nodes |
| Postgres / SQLite | small-N apps, embedded reads | acceptable; document the rebuild step |
| In-memory LRU | sub-ms hot path, accept restart cost | acceptable iff rebuild on startup completes within app SLO |
| Vector index (Faiss / IVF / HNSW) | similarity search | acceptable; rebuild step = re-embed from MST records |

### Prohibited even for projections

- **Stripe / PayPal / fiat processors** — payment substrate is not a projection
  question. ADR-2605172100 hard rule.
- **Cloudflare KV / Workers KV as primary write surface** — KV writes are
  fire-and-forget without commit ack, which violates (2). KV is acceptable for
  read-only projection caches but not as the write surface a Worker confirms
  back to the client.

### The "rebuild" requirement (the load-bearing clause)

A projection is kotoba-datomic-compliant only if there exists a documented procedure
that, given:

- access to a PDS instance hosting the relevant collection(s)
- access to an IPFS gateway with the relevant CIDs pinned
- no operator-held secret state

reproduces the projection's contents in a finite, monotonically-progressing
operation.

The rebuild may take hours. It may require Murakumo fleet capacity. It may
require re-running expensive embedding pipelines. What it MAY NOT require:

- a "snapshot" file that the operator must produce manually
- a hand-curated config that is not in the repo
- access to a deleted system

**Rationale**: the rebuild requirement is what makes the projection *not* a
state store. If a third party can rebuild the projection from public substrate,
then the operator is not centrally holding state — they're holding a cache.

### Marking convention

Every projection-bound file MUST have either:

**Option A — line comment** (for individual call sites in mixed-purpose files):

```typescript
// kotoba-datomic-projection: tileGeoJson reads from vertex_spatial RW; rebuild via
//   60-apps/etzhayyim-project-maps/tools/rebuild-spatial-projection.ts
const rows = await db.selectFrom("vertex_spatial").where(...).execute();
```

**Option B — directory manifest** (for projection-only directories):

```toml
# kotoba-datomic-projection.edn
[projection]
name = "maps-spatial-rw"
level = "L0-projection"   # bumped to L1 when rebuild tool exists in CI
rebuild_runbook = "../tools/rebuild-spatial-projection.md"
source_collections = [
  "com.etzhayyim.maps.feature",
  "com.etzhayyim.maps.building",
  # ...
]
rebuild_estimated_minutes = 240
adr = "2605231500"
```

The substrate-boundary lint (`70-tools/scripts/lint/substrate-boundary.mjs`)
gets a new allow-rule: a Kysely / asyncpg call site is allowed iff it has a
`kotoba-datomic-projection` line comment within 3 lines OR its containing directory
has a `kotoba-datomic-projection.edn`.

### Anti-pattern: "projection of the projection"

A projection MUST be rebuildable from `kotoba-datomic-chain + kotoba-datomic-dht`, not
from another projection. If projection B reads from projection A and forgets
about MST, projection B is not kotoba-datomic-compliant — even if projection A is.

Concretely: if a Murakumo cell consumes Kotoba/Datomic (projection A) to populate
an in-memory cache (projection B), that cache must also have a documented path
back to MST. The shortcut "rebuild B from A" is acceptable as long as the
overall chain back to MST is documented.

## Consequences

### Positive

- **maps Phase 4-5 unblocks** — 60 Tier C commands get a Charter-compliant
  home immediately (mark with line comments, document rebuild, ship). Full L1
  upgrade can land later without changing the read API surface.
- **yatabase BaaS surface is salvageable** — the commercial product can be
  reframed as "we sell access to a kotoba-datomic-projection-as-a-service" rather
  than "we sell access to a centralized DB" (Charter §4 carve-out for
  non-profit領収書用途 still applies; the projection framing makes the legal
  story consistent with the technical story).
- **Bluesky AppView pattern is canonical** — etzhayyim apps that want to
  federate to / from Bluesky have a precedent-aligned story.
- **Lint allows precise enforcement** — current substrate-boundary lint is
  binary (RW import = block); the projection marking turns this into
  three-state (block / require-comment / allow), reducing carve-out churn.

### Negative

- **Rebuild requirement is real work** — each projection needs a rebuild tool
  or runbook, which is non-trivial for the maps `vertex_spatial` table
  (estimated 4 h replay for current size). This is *the* gate that ensures
  honesty; making it real is the cost.
- **Lint complexity** — substrate-boundary lint must learn to parse the line
  comment / manifest. Pre-commit time will grow slightly.
- **Bait for misuse** — operators may mark things "projection" that aren't,
  hoping no one rebuilds. Mitigation: L1-projection requires CI-exercised
  rebuild tool, so claiming L1 without a working rebuild fails CI.

### Neutral

- **Does not deprecate or amend ADR-2605172000** — the prohibitions on
  centralized DB as **state store** remain absolute. This ADR adds a
  parallel category (**derived read path**) with its own rules.
- **Does not require Council vote** — the substrate boundary table in root
  CLAUDE.md gets an additive row; nothing existing is changed.

## Implementation plan

| # | Step | Owner | Target |
|---|---|---|---|
| 1 | This ADR | session 2026-05-23 | shipped with this commit |
| 2 | Update [`10-protocol/kotoba-datomic/SPEC.md`](../../10-protocol/kotoba-datomic/SPEC.md) §"Conformance levels" — add L0/L1/L2-projection column | follow-up | 0.5-day |
| 3 | Update root `CLAUDE.md` Substrate boundary table — add `kotoba-datomic-projection` row | follow-up | 0.5-day |
| 4 | Extend `70-tools/scripts/lint/substrate-boundary.mjs` — parse `// kotoba-datomic-projection` line comment and `kotoba-datomic-projection.edn` manifest | follow-up | 1-day |
| 5 | Author **first L0-projection manifest**: `60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6/kotoba-datomic-projection.edn` covering the existing RW reads, with markdown rebuild runbook | follow-up | 1-day |
| 6 | Author **first L1-projection** (RW MV replay tool + CI smoke): `60-apps/etzhayyim-project-maps/tools/rebuild-spatial-projection.ts` + CI step | follow-up | 1-week |
| 7 | Apply marking sweep across yatabase / yoro / yorishiro / joucho / murakumo / etzhayyim-k2 / baien (every app with RW reads gets either a projection manifest or a removal task) | follow-up | 2-week |

## Future Work

- **Streaming projection ADR**: define the firehose → MV pattern formally
  (atproto `com.atproto.sync.subscribeRepos` → projection update). Kotoba/Datomic
  streaming MVs are the natural fit but the contract should be substrate-
  agnostic so Iroh / Postgres CDC also qualify.
- **Cross-app projection ADR**: when projection B in app X reads from MST commits
  authored by app Y, do we need a cross-app capability token or is read access
  PDS-public? Probably the latter for public records, capability for encrypted.
- **Projection drift detection ADR**: how do we know a projection has silently
  diverged from canonical state? Periodic random-slice replay + alert; cost
  budget per projection.
- **Council deliberation projection**: the council deliberation cell (per
  [ADR-2605192300](/90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md)) is itself a
  projection (votes derived from `com.etzhayyim.governance.*` records). This
  ADR's framing applies — but the rebuild path must preserve the
  cryptographic chain of attestations, not just summarize them. Tracked as
  TBD.
