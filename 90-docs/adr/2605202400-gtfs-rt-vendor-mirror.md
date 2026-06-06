---
id: adr-2605202400-gtfs-rt-vendor-mirror
title: "ADR-2605202400: GTFS-RT real-time transit feed stays vendor-side as read-only mirror (not migrated to etzhayyim)"
status: active
doc_type: adr
topic: gtfs-rt-vendor-mirror
authoritative: true
last_verified: 2026-05-20
priority: 5.5
axis: app-scope
weight: 0.55
priority_note: "Exception carve-out for the maps consumer migration (etzhayyim-root ADR-2605202300). GTFS-RT cadence does not fit the mst-projector flush boundary, so the real-time path stays vendor while the static GTFS-JP path migrates with the rest of maps."
status_note: "ACTIVE 2026-05-20: decision shipped. The carve-out boundary is now load-bearing for the cutover runbook (etzhayyim-root@90-docs/maps-etzhayyim-cutover-runbook.md §Stage 5 explicitly excludes GTFS-RT tables/pods/lex from vendor sunset). No code change required by this ADR itself — vendor GTFS-RT pod, MVs, XRPC handler, and lexicon remain in place exactly as they were."
authoritative_for:
  - GTFS-RT (TripUpdate / VehiclePosition / ServiceAlert) data path
  - vendor-side maps real-time read API surface
related:
  - 60-apps/etzhayyim-project-maps/CLAUDE.md
supersedes: []
superseded_by: []
---

# ADR-2605202400: GTFS-RT real-time transit feed stays vendor-side as read-only mirror

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

etzhayyim-root ADR-2605202300 migrates `maps.etzhayyim.com` to `maps.etzhayyim.com` as a consumer of the existing substrate (`com.etzhayyim.substrate.shardSnapshot` + `50-infra/mst-projector` + `@etzhayyim/sdk` + `CheckpointAnchor.sol`). The 3-axis OR-test (ADR-2605172400) passes for maps as a whole.

GTFS-RT (real-time transit feed: `vertex_maps_vehicle_position` / `vertex_maps_trip_update` / `vertex_maps_service_alert`, ingested by `bulk-ingest/workers/gtfs_rt_dumper.py`, currently `replicas=0`-gated, ADR-2604271400-era) however does not fit the mst-projector publish loop:

| Property | mst-projector best-fit | GTFS-RT requirement |
|---|---|---|
| flush cadence | 60s wall-clock or 1000 records (default), tunable to ~10s with overhead | 5-30s window for usable RT |
| record turnover | append-mostly (snapshots accumulate) | high churn (VehiclePosition rewritten every 30s per vehicle; 95% of yesterday's rows useless) |
| consumer pattern | snapshot-pinned readers, slow time travel | "what is happening RIGHT NOW", time travel uninteresting |
| substrate cost | every flush pins to IPFS + writes shardSnapshot AT record | 1 RT cycle = ~3 shards × ~60 flushes/hour ≈ 4,000 IPFS pins/day for ~1 hour of useful state |
| 3-axis Settlement | clean | clean |
| 3-axis Custody  | clean | clean |
| 3-axis Liability | clean (open data) | clean (open data) — but operator absorbs ODPT TOS compliance |

The 3-axis rule does not force GTFS-RT to vendor — all three axes are technically clean. The blocker is **architectural mismatch**: forcing 5-30s real-time updates through a snapshot+anchor pipeline burns IPFS pin budget on data that is obsolete before the L2 anchor confirms.

# Decision

GTFS-RT (the **real-time** path) stays in vendor (`etzhayyim-root`):

- `bulk-ingest/workers/gtfs_rt_dumper.py` continues to write `vertex_maps_vehicle_position` / `vertex_maps_trip_update` / `vertex_maps_service_alert` to Kotoba/Datomic via Hyperdrive direct INSERT (ADR-0036 path).
- The streaming MVs `mv_maps_recent_vehicle_position` / `mv_maps_recent_trip_update` / `mv_maps_active_alerts` (window-pruned DISTINCT ON keyed by stop/trip/alert) stay in vendor.
- The XRPC handler `cmdRealtimeDelaysAtStop` (`com.etzhayyim.apps.maps.realtimeDelaysAtStop`) stays in vendor and continues to be served from `maps.etzhayyim.com`.

GTFS-RT is the **only** maps subsystem that does not migrate to etzhayyim. Everything else (static GTFS-JP, OSM, Wikidata, ferry, openflights, gsplat preview, satellite, post EXIF, Mapraly, Murakumo Vision) follows ADR-2605202300 to the etzhayyim substrate.

## etzhayyim-side read access

`maps.etzhayyim.com` may expose a thin **public read-only proxy** to the vendor RT endpoint so etzhayyim-aligned clients do not have to know about `maps.etzhayyim.com`:

```
GET maps.etzhayyim.com/xrpc/com.etzhayyim.maps.realtimeDelaysAtStop?stopId=…
   ↓ pass-through
GET maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.realtimeDelaysAtStop?stopId=…
   ↓
Kotoba/Datomic (vendor)
```

The proxy is stateless, holds no data, just rewrites NSID + forwards. This keeps the substrate boundary visible (vendor remains the system of record) while letting etzhayyim apps consume RT data without a substrate violation.

## Re-evaluation triggers

The vendor placement is **not permanent**. Reconsider in any of:

1. mst-projector grows per-shard sub-second flush cadence (currently roadmap, not built)
2. ODPT API becomes redistributable as content-addressed snapshots (allowing batch-IPFS-then-firehose, decoupling RT cadence from substrate)
3. The vendor RW cluster goes away for other reasons and we have to find a substitute regardless

# Consequences

**Positive**:
- maps migration ships without solving an unrelated real-time problem.
- Vendor retains a clear residual responsibility (RT mirror), which justifies the vendor maps RW partition staying alive even after the static path migrates.
- The boundary is documented, not implicit — future maintainers know GTFS-RT is the carve-out, not a forgotten orphan.

**Negative**:
- Two substrates for one app's data (vendor RW for RT, etzhayyim substrate for everything else). Acceptable because the read surfaces are obviously different (`realtimeDelaysAtStop` vs `tileGeoJson` / `nextDeparturesAtStop`).
- Clients that want RT + static in one query must hit both surfaces. Acceptable because (a) RT consumers are real-time apps that already manage multi-source state, (b) the etzhayyim proxy hides the vendor URL.
- We continue to carry the GTFS-RT vendor secret (`ODPT_API_KEY`) and pod operations in vendor.

# References

- etzhayyim-root ADR-2605202300 — maps consumer migration (where the static path goes)
- etzhayyim-root ADR-2605171800 — LangGraph → MST → IPFS → L2 pipeline (the substrate that does not fit RT)
- etzhayyim-root ADR-2605191655 — mst-projector Phase 2 design
- `60-apps/etzhayyim-project-maps/CLAUDE.md` — GTFS-RT Phase 3 design + bring-up runbook
- `60-apps/etzhayyim-project-maps/bulk-ingest/workers/gtfs_rt_dumper.py`
- `00-contracts/lexicons/com/etzhayyim/apps/maps/realtimeDelaysAtStop.json`
