// Streaming MVs for live tracker.
//
// 3 narrow MVs (low-cardinality GROUP BY, no wide MAX(varchar) — guardrail
// 30-graph/graph-schema/CLAUDE.md §MV Memory Safety):
//
//   - mv_aircraft_currently_airborne  : latest non-ground state per icao24, last 90s
//   - mv_aircraft_country_count       : per origin_country airborne count, last 5min
//   - mv_satellite_visible_now        : passes whose AOS..LOS straddles wallclock now
//
// Cardinality bounds:
//   airborne: ~12k icao24 globally
//   country:  ~250 distinct
//   visible:  ~28k satellites × few observer cells active = <50k pass rows live
//
// RisingWave temporal-filter constraint: `now()` may only appear as
// `input_expr cmp now_expr`, where `input_expr` is a column without now()
// and `now_expr` is monotonic. Hence we compare `to_timestamp(ts_ms/1000)`
// (a column expression) against `now() - INTERVAL '...'` (monotonic).

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // Latest state per aircraft, only those seen in the last 90s and not on ground.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_aircraft_currently_airborne AS
    SELECT
      icao24,
      callsign,
      lat,
      lon,
      baro_altitude_m,
      velocity_ms,
      heading_deg,
      vertical_rate_ms,
      origin_country,
      source,
      ts_ms
    FROM vertex_aircraft_state
    WHERE on_ground = false
      AND to_timestamp(ts_ms / 1000.0) > now() - INTERVAL '90 seconds'
  `.execute(db);

  // Per-country airborne count (last 5 minutes).
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_aircraft_country_count AS
    SELECT
      origin_country,
      COUNT(*) AS airborne_count
    FROM vertex_aircraft_state
    WHERE on_ground = false
      AND to_timestamp(ts_ms / 1000.0) > now() - INTERVAL '5 minutes'
    GROUP BY origin_country
  `.execute(db);

  // Currently-overhead satellite passes.
  // RW temporal filter: only one column-vs-now() comparison per side; combine
  // via two separate predicates each in canonical form.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_satellite_visible_now AS
    SELECT
      norad_id,
      observer_h3,
      observer_lat,
      observer_lon,
      aos_ms,
      los_ms,
      max_elevation_deg,
      peak_azimuth_deg,
      visible_at_night,
      magnitude
    FROM vertex_satellite_pass
    WHERE to_timestamp(aos_ms / 1000.0) <= now() + INTERVAL '0 seconds'
      AND to_timestamp(los_ms / 1000.0) >= now() - INTERVAL '0 seconds'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_satellite_visible_now`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_aircraft_country_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_aircraft_currently_airborne`.execute(db);
}
