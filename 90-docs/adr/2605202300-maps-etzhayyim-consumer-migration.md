---
id: adr-2605202300-maps-etzhayyim-consumer-migration
title: "ADR-2605202300: maps.etzhayyim.com — consumer of shardSnapshot + mst-projector (no new substrate)"
status: proposed
doc_type: adr
topic: maps-etzhayyim-consumer-migration
authoritative: true
last_verified: 2026-05-20
priority: 6.5
axis: app-migration
weight: 0.65
priority_note: "First non-trivial vendor app to migrate to the etzhayyim substrate. Establishes the consumer-only pattern (no new substrate primitives — reuse shardSnapshot + mst-projector + @etzhayyim/sdk) that subsequent app migrations (sanctions-list / open-data / A-B-C-group datasets / yobel ledger reader) will follow."
authoritative_for:
  - maps.etzhayyim.com app boundary and namespace
  - com.etzhayyim.maps.* lexicons (consumer of com.etzhayyim.substrate.shardSnapshot)
depends_on:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605191655-mst-projector-phase2-design
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
related: []
supersedes: []
superseded_by: []
---

# ADR-2605202300: maps.etzhayyim.com — consumer of shardSnapshot + mst-projector (no new substrate)

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

`maps.etzhayyim.com` is the largest Kotoba/Datomic-dependent vendor app (`vertex_spatial` + 12 `vertex_maps_*` tables + 6 streaming MV + Hyperdrive direct write + GraphAr traversal). Applying the 3-axis split rule (ADR-2605172400):

| Axis | Verdict | Reason |
|------|---------|--------|
| Liability | clean | OSM / Wikidata / Mapillary-derived open data; no fiduciary counterparty |
| Custody  | clean | public spatial data; user EXIF is opt-in; operator holds no PII master |
| Settlement | clean | no Stripe; Mapillary / RunPod are internal operator cost, not customer billing |

3/3 clean → maps qualifies for etzhayyim. The substrate constraint (ADR-2605172000) requires kotoba implementation.

A prior draft (vendor ADR-2605201800, reverted) proposed a parallel "AT record + Iceberg-on-IPFS" scheme with its own `org.etzhayyim.storage.*` lexicons and Python projector pod. That draft was authored without visibility into the existing etzhayyim-root infrastructure and substantially duplicates work already shipped here:

| What was re-derived | What already exists in etzhayyim-root |
|---|---|
| snapshot record | `com.etzhayyim.substrate.shardSnapshot` (Phase 1 JSON manifest + Phase 2 MST CAR + `rootCid` + `snapshotCid`) |
| projector pod | `50-infra/mst-projector` + `@etzhayyim/sdk` (`checkpointer.ts` / `ipfs.ts` / `l2.ts`) — Python shim + TS sidecar via Unix socket IPC |
| MV / publish / L2 anchor architecture | ADR-2605171800 + ADR-2605191655 + ADR-2605191559 / 1608 / 1625 (Stage 2/3/4 activation) |

# Decision

`maps.etzhayyim.com` migrates to etzhayyim as a **pure consumer** of the existing substrate. No new storage primitives are introduced.

## App boundary

| Item | Value |
|---|---|
| Domain | `maps.etzhayyim.com` (primary), `maps.etzhayyim.com` (federation alias only, AT layer) |
| Publisher DID | `did:web:maps.etzhayyim.com` |
| Operating entity | etzhayyim (3/3 axes clean) |
| Substrate | AT MST + IPFS + Base L2 anchor (ADR-2605172000) |
| Settlement | none (no paid surface) |

## Namespace + lexicons

| NSID | Type | Role |
|---|---|---|
| `com.etzhayyim.maps.feature` | record | 1 spatial feature = 1 record. Geometry as GeoJSON string, bbox as integer microdegrees, h3Cell + h3Resolution carried in record so indexers do not re-parse |
| `com.etzhayyim.maps.tileGeoJson` | query | bbox + labels → GeoJSON, read against latest (or pinned-generation) `com.etzhayyim.substrate.shardSnapshot` for `shardKey = "com.etzhayyim.maps.feature"` |

Both lexicons land in `00-contracts/lexicons/com/etzhayyim/maps/` in this commit.

## Pipeline (reusing existing components)

```
maps app
  └─ createRecord com.etzhayyim.maps.feature  ──▶  PDS / MST
                                                       │
                                                       ▼ (firehose-style projection)
                                              50-infra/mst-projector
                                              (shardKey = "com.etzhayyim.maps.feature")
                                                       │
                                              MstCheckpointSaver (py shim)
                                                       │ Unix socket
                                                       ▼
                                              @etzhayyim/sdk checkpointer sidecar (TS)
                                                       │
                                                       ▼ MST CAR
                                                     IPFS (kubo + remote pinning)
                                                       │
                                                       ▼ periodic batch
                                                     Base L2 anchor (CheckpointAnchor.sol)
                                                       │
                                                       ▼
                                              com.etzhayyim.substrate.shardSnapshot record
```

`tileGeoJson` reads the latest `shardSnapshot` for the maps shardKey, resolves the MST root from IPFS, walks the MST for features matching the bbox, and emits a GeoJSON FeatureCollection. Phase 1 readers walk the JSON manifest; Phase 2 readers walk the MST CAR.

## What is explicitly NOT introduced

- No new `org.etzhayyim.storage.*` namespace (would have duplicated `com.etzhayyim.substrate.*`)
- No Iceberg manifest format on IPFS (the MST CAR + shardSnapshot already serve this role for AT-Protocol-shaped data)
- No standalone Python projector for maps (the central `50-infra/mst-projector` handles all shards by `shardKey`)
- No new XRPC procedures for publish / get / list snapshot (caller uses the standard `com.atproto.repo.*` record APIs against `com.etzhayyim.substrate.shardSnapshot`)
- No new Base L2 anchor contract (the existing `CheckpointAnchor.sol` from ADR-2605171800 is shared)

# Consequences

**Positive**:
- maps becomes the first non-trivial vendor app proving the etzhayyim substrate end-to-end. The same consumer pattern unlocks sanctions / open-data / A-B-C-group / yobel ledger reader migrations.
- Adds only 2 lexicon files and 1 ADR — minimal surface area for review.
- No fragmentation of the substrate (one snapshot record type, one projector, one anchor contract).
- Time travel and audit anchor come for free via the existing pipeline.

**Negative**:
- The H3-aware partition optimisation we would have wanted (`partitions[].key = h3Cell`) is not first-class in `shardSnapshot`. Bbox queries against a large feature collection will walk the MST; if performance becomes an issue, the right next step is a **separate** spatial side-index shard (e.g., `com.etzhayyim.maps.h3Index` with `shardKey = "com.etzhayyim.maps.h3Index"`) projected by the same mst-projector. This keeps the substrate uniform and defers optimisation until measurement justifies it.
- Real-time GTFS-RT (30s update cadence) does not fit the snapshot publish loop and stays vendor-side as a read-only mirror — same exception class as discussed in the reverted ADR-2605201800.

# Alternatives Considered

1. **Parallel Iceberg-on-IPFS substrate** (the reverted vendor ADR-2605201800). Rejected: duplicates `com.etzhayyim.substrate.shardSnapshot`, fragments the substrate, doubles operator cost.
2. **Keep maps on vendor RW**, expose etzhayyim-side as a read-only mirror. Rejected: defers the substrate migration that the 3-axis rule mandates; leaves the largest RW dependency in vendor indefinitely.
3. **Skip H3 indexing entirely**, do all bbox queries via MST walk. Acceptable as the Phase 1 starting point — adopted here. The side-index shard is queued as a follow-up only when query latency demands it.

# References

- ADR-2605171800 — LangGraph → MstCheckpointSaver → MST → IPFS → L2 anchor pipeline
- ADR-2605191655 — mst-projector Phase 2 design
- ADR-2605172000 — etzhayyim kotoba substrate
- ADR-2605172400 — etzhayyim / vendor 3-axis split rule
- `00-contracts/lexicons/com/etzhayyim/substrate/shardSnapshot.json` — the snapshot record consumed by `tileGeoJson`
- `50-infra/mst-projector/` — projector daemon
- `20-actors/etzhayyim-sdk/src/{checkpointer.ts,ipfs.ts,l2.ts}` — substrate-client sidecar
- Reverted vendor commit: etzhayyim-root@54898e99111 (revert of 1fa63bf1f0b)
