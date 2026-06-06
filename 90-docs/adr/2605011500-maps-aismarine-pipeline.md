---
id: adr-2605011500-maps-aismarine-pipeline
title: "ADR-2605011500: Maps AIS Marine Vessel Tracking Pipeline (MarineTraffic-equivalent)"
status: active
doc_type: adr
topic: maps-aismarine-pipeline
authoritative: true
last_verified: 2026-05-01
authoritative_for:
  - global AIS vessel position ingest
  - vertex_vessel / vertex_vessel_position / vertex_vessel_voyage schema
  - aisstream.io WebSocket consumer Deployment
  - aismarine BPMN actors (consumer / voyage-detector / master-refresh / density-refresh)
  - com.etzhayyim.apps.maps.aismarine.* XRPC surface
  - kami-geo vessel rendering layer
related:
  - adr-0017-maritime-energy-cluster-topology
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0044-kotoba-udf-language-strategy
  - adr-0048-kotoba-vultr-b2-primary
  - adr-0056-bpmn-as-actor
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-2604280900-maps-transit-pipeline-gtfs-rt
  - adr-2604282300
  - adr-2604241342-kotoba-out-of-band-migration-pattern
---

# ADR-2605011500 — Maps AIS Marine Vessel Tracking Pipeline

**Status**: active
**Date**: 2026-05-01
**Authors**: Jun Kawasaki + Claude Code

## Goal

Provide a MarineTraffic-equivalent global vessel-tracking surface on `maps.etzhayyim.com`:

- Live vessel positions worldwide (no geo filter), refreshed sub-minute
- Vessel detail (MMSI / IMO / name / type / flag / dimensions / recent track)
- Voyage detection (port arrivals/departures from nav status + port proximity)
- Density tile (H3 hex) for low-zoom rendering
- Reuses existing `vertex_open_ports` (UN/LOCODE master, ADR-0017) for port join

Constraint: **open / free data only** (no Spire / VT Explorer / IHS paid feeds).

## Scope

**In scope (Phase 1)**:
- aisstream.io WebSocket as the sole live position source (free, global, no bbox filter)
- Vessel master limited to fields broadcast over AIS itself (MMSI, IMO, name, callsign, type code, dimensions, draught) — no commercial enrichment
- 4 BPMN actors + 1 long-running K8s Deployment (consumer)
- 4 read XRPC commands on `maps.etzhayyim.com`
- Frontend vessel + density layer in kami-geo

**Out of scope**:
- Vessel photos, ownership, P&I club, last port-state inspection (require paid feeds)
- Historical replay before consumer cutover (forward-only, like Gmail incremental — ADR-0032)
- AIS satellite (S-AIS) coverage gaps; coastal/HF coverage only via aisstream.io reciprocal network
- Federation of vessel records to Bluesky AppView (domain-only writes per ADR-0036)

## Executive Summary

Add a new `aismarine` actor under `maps.etzhayyim.com` mirroring the Transit pipeline (ADR-2604280900). One K8s `Deployment` runs the long-running aisstream WebSocket consumer (BPMN unsuitable for persistent sockets); four BPMNs handle batch operations on `R/PT5M` / `R/PT15M` / `R/PT24H` cadences. All writes are Worker-direct Hyperdrive (ADR-0036). Read path is `mv_vessel_latest_position` + bbox SELECT through Hyperdrive. CF Worker stays in L3 dispatcher subset (ADR-2604251830) — no business logic, just XRPC facade.

## Decision

### Layer 1-3: CF Worker (`maps.etzhayyim.com`) XRPC surface

Add to existing `maps-ui-uqpel6i6` Worker (no new Worker, ADR-2604282300):

| NSID | Read/Write | Backing |
|---|---|---|
| `com.etzhayyim.apps.maps.aismarine.queryVesselsBbox` | read | `mv_vessel_latest_position` SELECT with `lat BETWEEN` + `lon BETWEEN` + optional `type_class IN (...)`, returns GeoJSON FeatureCollection |
| `com.etzhayyim.apps.maps.aismarine.getVesselDetail` | read | `vertex_vessel` + last 24h `vertex_vessel_position` ORDER BY ts_ms DESC LIMIT 500 + active `vertex_vessel_voyage` |
| `com.etzhayyim.apps.maps.aismarine.searchVessels` | read | prefix SELECT on `vertex_vessel.name` / MMSI / IMO |
| `com.etzhayyim.apps.maps.aismarine.getVesselDensityTile` | read | `mv_vessel_density_h3_r6` filtered by H3 cells covering bbox |

All four use `createKyselyDb(env.HYPERDRIVE)` (ADR-0036 read path). No PDS pipethrough.

### Layer 4: Kotoba/Datomic schema

Single migration `20260501XXXXXX_vertex_aismarine_phase1.ts`:

```sql
-- Vessel master (one row per MMSI, AIS Type-5 broadcast cumulative upsert)
vertex_vessel (
  vertex_id           VARCHAR PRIMARY KEY,        -- 'mmsi:${mmsi}'
  mmsi                BIGINT NOT NULL,
  imo                 BIGINT,
  callsign            VARCHAR,
  name                VARCHAR,
  type_code           SMALLINT,                   -- AIS Type 1-99
  type_class          VARCHAR,                    -- 'cargo'|'tanker'|'fishing'|'passenger'|'other' (UDF-derived)
  flag_mid            SMALLINT,                   -- first 3 digits of MMSI
  flag_iso            VARCHAR,                    -- mapped to ISO 3166-1 alpha-2
  length_m            REAL,
  width_m             REAL,
  draught_m           REAL,
  source              VARCHAR,                    -- 'aisstream'
  first_seen_ms       BIGINT NOT NULL,
  last_seen_ms        BIGINT NOT NULL
)

-- Position log (append-only, hot table; no soft-delete)
vertex_vessel_position (
  vertex_id           VARCHAR PRIMARY KEY,        -- 'mmsi:${mmsi}:ts:${ts_ms}'
  mmsi                BIGINT NOT NULL,
  ts_ms               BIGINT NOT NULL,
  lat                 DOUBLE PRECISION NOT NULL,
  lon                 DOUBLE PRECISION NOT NULL,
  sog_knot            REAL,
  cog_deg             REAL,
  heading_deg         SMALLINT,
  nav_status          SMALLINT,                   -- AIS nav status 0-15
  source              VARCHAR
)

-- Voyage (derived by voyageDetector BPMN)
vertex_vessel_voyage (
  vertex_id           VARCHAR PRIMARY KEY,        -- 'mmsi:${mmsi}:voy:${departure_ms}'
  mmsi                BIGINT NOT NULL,
  departure_port_locode VARCHAR,
  departure_ms        BIGINT,
  arrival_port_locode   VARCHAR,
  arrival_ms          BIGINT,
  declared_draught_m  REAL,
  declared_eta_ms     BIGINT,
  declared_destination VARCHAR
)

-- Visited-port edge (port → vessel reverse lookup)
edge_vessel_visited_port (
  edge_id             VARCHAR PRIMARY KEY,        -- 'mmsi:${mmsi}:port:${locode}:arr:${arrival_ms}'
  mmsi                BIGINT NOT NULL,
  port_locode         VARCHAR NOT NULL,
  arrival_ms          BIGINT NOT NULL,
  departure_ms        BIGINT
)
```

**Streaming MVs**:

```sql
-- Latest position per MMSI (read path for queryVesselsBbox)
mv_vessel_latest_position
  -- RW pattern: subquery + JOIN against MAX(ts_ms) per mmsi
  -- (DISTINCT ON unsupported; see ADR-2604241342)

-- H3 res-6 density per type_class, 1h sliding window (low-zoom layer)
mv_vessel_density_h3_r6
  -- GROUP BY h3_lat_lng_to_cell(lat, lon, 6), type_class, time bucket
```

**SQL UDFs (ADR-0044, rule UDF tier)**:

- `vessel_type_class(type_code SMALLINT) RETURNS VARCHAR` — AIS Type 70-79=`cargo`, 80-89=`tanker`, 30=`fishing`, 60-69=`passenger`, else `other`
- `vessel_flag_iso(mmsi BIGINT) RETURNS VARCHAR` — MID (first 3 digits) → ISO 3166-1 alpha-2 lookup table

### Layer 7: BPMN actors (ADR-0056)

| BPMN | trigger | task |
|---|---|---|
| `aisStreamConsumer.bpmn` | manual / supervisor restart | none — placeholder for catalog visibility; actual loop is K8s Deployment (see L8) |
| `voyageDetector.bpmn` | timer-start `R/PT5M` | `aismarine.voyage.detectWindow` — scan last 5min positions, detect nav_status 5/15 + port proximity, UPSERT `vertex_vessel_voyage` + `edge_vessel_visited_port` |
| `refreshVesselMaster.bpmn` | timer-start `R/PT24H` | `aismarine.master.refresh` — backfill `vertex_vessel.flag_iso` / dimensions for rows missing them via accumulated AIS Type-5 broadcasts |
| `refreshVesselDensity.bpmn` | timer-start `R/PT15M` | `aismarine.density.verify` — sanity-check `mv_vessel_density_h3_r6` (streaming MV is autonomous; this is observability) |

Two new rows in `vertex_bpmn_process_def` + 4 in `vertex_bpmn_lexicon_binding` (BPMN-as-actor convention). F5 watcher auto-deploys to Zeebe.

### Layer 8: K8s Deployment (long-running consumer)

`50-infra/vultr/bulk-ingest/aismarine-consumer/`:

- Helm chart, `replicas: 1` (single WebSocket sufficient for global feed)
- Reuses pymagatama image, env `AISMARINE_CONSUMER_MODE=1` switches main entry to `aismarine_consumer_loop()`
- WebSocket subscribes to aisstream.io with **no `BoundingBoxes` filter** (global)
- In-process queue, batch flush every 5s **or** 500 messages (whichever first)
- Batch INSERT via `task_aismarine_position_batch_insert` (psycopg3, `flush=False`)
- Restart policy: `Always`; CrashLoopBackOff acceptable, supervisor-style
- Secret `aismarine-credentials` carries `AIS_STREAM_API_KEY` (registered to `etzhayyim.comsstream/API_KEY` in macOS Keychain + 1Password mirror per Root-Only Rule)

**Why Deployment, not BPMN timer-start**: WebSocket needs a persistent socket with sub-second message arrival; BPMN R/PT* loops would re-handshake every fire and drop messages between fires. This mirrors `kafka-consumer` / `firehose-consumer` patterns elsewhere in the repo.

### pyzeebe primitives

`20-actors/magatama/py/src/pymagatama/primitives/aismarine.py`:

```python
def aismarine_consumer_loop()
    # WebSocket reconnect-on-disconnect; bounded backoff; metrics emit
def task_aismarine_position_batch_insert(rows: list[dict])
    # INSERT into vertex_vessel_position (batch); flush=False; no ON CONFLICT
def task_aismarine_master_upsert(rows: list[dict])
    # INSERT into vertex_vessel; PK overwrite (RW implicit upsert per ADR-2604241121)
def task_aismarine_voyage_detect_window(window_minutes: int = 5)
    # nav_status ∈ {1,5,15} + within 5km of vertex_open_ports row → arrival/departure
    # writes vertex_vessel_voyage + edge_vessel_visited_port
def task_aismarine_master_refresh(limit: int = 1000)
    # SELECT vertex_vessel WHERE flag_iso IS NULL OR length_m IS NULL LIMIT {int(limit)}
    # update from accumulated Type-5 broadcasts
def task_aismarine_density_verify()
    # Observability only; SELECT count(*) from mv_vessel_density_h3_r6
def task_aismarine_query_bbox(bbox, types, limit)
    # Used by CF Worker XRPC; LIMIT {int(limit)} (psycopg3 prepared-stmt rule)
```

**Mandatory conventions**:
- `flush: bool = False` default (yoro-social fix, CLAUDE.md 2026-04-30)
- `LIMIT {int(n)}` not `LIMIT %s` (`rw-psycopg3-no-param-limit`)
- No `ON CONFLICT` (RW implicit upsert via PK)
- `SET dml_rate_limit` before bulk batch INSERT (ADR-0048 incident_2026_04_25)

### Lexicons

`00-contracts/lexicons/com/etzhayyim/maps/aismarine/`:
- `queryVesselsBbox.json` — input: `{bbox:[w,s,e,n], types?:[...], limit?:int}`; output: `{features:[GeoJSON]}`
- `getVesselDetail.json` — input: `{mmsi:int}`; output: `{vessel, recentTrack:[...], voyage}`
- `searchVessels.json` — input: `{q:string, limit?:int}`; output: `{results:[...]}`
- `getVesselDensityTile.json` — input: `{bbox, h3Resolution:int}`; output: `{cells:[{h3, count, byClass}]}`
- `ingestAisStream.json` — internal: invoked by K8s Deployment (`x-internal-trust`)
- `refreshVesselMaster.json` — internal: BPMN dispatcher only

### Frontend (kami-geo)

- New `vessels` layer (icon-by-`type_class`, rotation = `cog_deg`)
- Zoom < 8: render `mv_vessel_density_h3_r6` as hex polygons (existing `polygon_to_fill_earcut` post-2026-04-30 fix)
- Zoom ≥ 8: render individual vessel icons via existing sprite system
- Click on vessel → fetch `getVesselDetail`, popup with last 24h polyline overlay

## Comparison

| Choice | Selected | Reason |
|---|---|---|
| Live source: aisstream.io vs AISHub vs Spire | **aisstream.io** | Free, WebSocket (sub-second), global, no bbox required, reciprocity not enforced |
| Master enrichment: paid (VT Explorer / IHS) vs open AIS-only | **AIS-only** | Open-only constraint; AIS Type-5 broadcast covers MMSI/IMO/name/dims; gaps acceptable |
| Geo filter: bbox subscribe vs global | **global** | Operator decision; aisstream global subscribe ~100-500 msg/s is within single-replica budget |
| Consumer placement: BPMN timer-start vs K8s Deployment | **K8s Deployment** | WebSocket is persistent; timer-start would handshake per fire and drop in-flight messages |
| Position table partition: time-range vs append | **append-only, no partition (Phase 1)** | Kotoba/Datomic Hummock cold-tiering handles aging; partitioning deferred until row count justifies |
| Read path: PDS pipethrough vs Worker-direct Hyperdrive | **Worker-direct** | ADR-0036 mandates domain reads via Hyperdrive; PDS reserved for social/federation/messaging/vault/signal |
| Tile rendering: PMTiles bake vs live MV | **live MV** | `tileGeoJson` XRPC + `mv_vessel_density_h3_r6` matches recent decision to retire PMTiles (ADR-2604280900 superseded `maps-tile-server-deploy`) |

## Rationale

**Layered placement**: This is a textbook L4-L8 split (ADR-2604251830). CF Worker stays L1-L3 facade only; the actor identity (`did:web:maps.etzhayyim.com:aismarine`) lives in `vertex_actor_registry`; business logic is in pyzeebe primitives invoked from BPMN; long-running socket is L8 K8s. Mirrors the Transit pipeline (ADR-2604280900) almost line-for-line.

**Why not extend `vertex_oil_tanker_phase2a`**: That table is for opaque-fleet detection (ADR-0017 §dark-fleet detection), curated subset, multi-source-correlated. AIS live feed is a different concern: high-volume, low-curation, all-vessels. Joining at query time on MMSI is preferred over conflating tables.

**Forward-only ingest**: Like Gmail (ADR-0032), no historical backfill. AIS history is available from NOAA bulk ZIPs but is out of scope for Phase 1; can be added later as a `bulk-ingest-ais-noaa-history` parallel pod without disturbing the live consumer.

**No federation**: Vessel positions are not social content. PDS dispatch path (ADR-2604282300 §Addendum 2026-04-30) is bypassed; writes go straight to Hyperdrive (ADR-0036). No `app.bsky.*` or `com.atproto.*` records emitted.

## Exceptions

- **`aisStreamConsumer.bpmn` is a stub**: it exists in the BPMN catalog for actor-discovery uniformity (ADR-0056) but contains no executable tasks. The actual consumer is the K8s Deployment. This is the only non-executable BPMN in the maps catalog; flagged here to preempt drift.
- **`SET dml_rate_limit` is required for the consumer batch path** even though it normally applies only to bulk-backfill. AIS bursts at port arrivals (e.g. Singapore Strait) can spike to >2000 msg/s and would otherwise saturate B2 SlowDown thresholds (ADR-0048 §incident_2026_04_25 retraction).
- **`mv_vessel_latest_position` cannot use `DISTINCT ON`** (Kotoba/Datomic limitation). Use the documented "MAX subquery + JOIN" pattern from ADR-2604241342.

## Implementation Order (single ADR, four sequential PRs)

1. **PR-A schema** — migration + 6 lexicon JSONs
2. **PR-B pyzeebe** — `aismarine.py` primitive + tests
3. **PR-C BPMN** — 4 BPMN files + Zeebe binding seed migration
4. **PR-D worker + frontend + K8s** — `maps.etzhayyim.com` XRPC + kami-geo vessel layer + `aismarine-consumer` Helm chart + Keychain/1Password registration of `etzhayyim.comsstream/API_KEY`

Each PR is independently deployable. Live cutover is at PR-D (consumer start).

## Addendum 2026-05-05 — Phase 1 RW 2.8.1 compatibility deltas

During runbook step-1 cutover (2026-05-05) three Kotoba/Datomic 2.8.1 limitations
were hit. Phase 1 absorbs the deltas; Phase 2 will re-introduce the original
design once the upstream RW gaps are filled.

### A. `CREATE OR REPLACE FUNCTION` is not supported

RW 2.8.1 returns `XX000 Feature is not yet implemented: CREATE OR REPLACE
FUNCTION`. Both UDFs in the migration switched to `DROP FUNCTION IF EXISTS`
+ `CREATE FUNCTION`. Idempotency preserved at the cost of a 2-statement
window where the function is missing.

### B. Simple-CASE form does not match integer literals reliably

`vessel_flag_iso` originally used a nested `CASE (mmsi/1000000)::int WHEN N
THEN 'XX' …`. On RW 2.8.1 this returns `OTHER` even when the inner
expression equals `N`:

```sql
SELECT (431999000::bigint / 1000000)::int = 431
  -- → t
SELECT CASE (431999000::bigint / 1000000)::int
         WHEN 431 THEN 'JP' ELSE 'OTHER' END
  -- → OTHER  (bug)
SELECT CASE
         WHEN (431999000::bigint / 1000000)::int = 431 THEN 'JP'
         ELSE 'OTHER' END
  -- → JP    (works)
```

All 118 WHEN clauses rewritten to searched-CASE form. Phase 2 may revert
to simple-CASE if upstream fixes the matcher.

### C. No `h3_lat_lng_to_cell` builtin → 0.1° lat/lon grid

RW 2.8.1 ships no H3 spatial functions. The original
`mv_vessel_density_h3_r6` cannot bind. Phase 1 substitutes
`mv_vessel_density_grid` — a 0.1°×0.1° lat/lon grid (~11km equator) using
`FLOOR(p.lat * 10) / 10.0` and `FLOOR(p.lon * 10) / 10.0` as `lat_bin` /
`lon_bin`, with `cell_id` = `'lat:N|lon:N'` opaque text key.

The `getVesselDensityTile` lexicon adds `cellSchema: 'grid_0p1deg' |
'h3_r6'` to the response so clients can render either path without schema
churn. The Worker handler reads `mv_vessel_density_grid` and returns
`cellSchema: 'grid_0p1deg'` + `lat_bin` / `lon_bin` per cell. The kami-geo
overlay renders axis-aligned rectangles in Phase 1; h3-js stays in
package.json for Phase 2 lazy import.

`h3Resolution` request parameter is **accepted but ignored** in Phase 1
(forward-compat).

### Phase 2 plan (separate ADR amendment)

- Add Python External UDF `h3_lat_lng_to_cell(lat, lon, res)` to the RW
  cluster (wraps `h3o` Rust crate via `pyo3` or `arrow-udf`).
- New migration: `CREATE MATERIALIZED VIEW mv_vessel_density_h3_r6 AS …`
  alongside (not replacing) `mv_vessel_density_grid`.
- Worker handler: pick MV by request `h3Resolution` (≥3 → H3 MV, absent →
  grid MV) and set `cellSchema` accordingly. No new lexicon revision.
- Frontend overlay already supports both schemas; no change needed.

### D. `ON CONFLICT DO NOTHING` not supported

`apply-pending.sh` already documents this. Not used by the aismarine
migration.

## References

- ADR-0017 — Maritime + Energy Cluster Topology (vertex_open_ports, oil tanker)
- ADR-0036 — Worker-direct Hyperdrive Persistence (write path)
- ADR-0044 — Kotoba/Datomic UDF Language Strategy (SQL UDF for type_class / flag_iso)
- ADR-0048 — Kotoba/Datomic Vultr+B2 Primary (dml_rate_limit, B2 SlowDown lessons)
- ADR-0056 — BPMN-as-actor (process_def + lexicon_binding pattern)
- ADR-2604251830 — Shannon-Optimal 8-Layer Architecture (CF=L1-L3 only)
- ADR-2604280900 — Maps Transit Pipeline (sister pipeline, same shape)
- ADR-2604282300 — CF Worker = Edge Layer Only (T1/T2/T3 placement)
- ADR-2604241342 — Kotoba/Datomic Migration Failure Modes (DISTINCT ON, ON CONFLICT)
- aisstream.io API docs (free WebSocket AIS relay)
