// Live tracker tables (Flightradar24 + N2YO equivalent for maps.gftd.ai).
//
// 4 tables:
//   - vertex_aircraft_state    (real-time ADS-B / OpenSky state vectors, 24h TTL)
//   - vertex_aircraft_track    (compacted flight trajectories per icao24)
//   - vertex_satellite_tle     (TLE catalog refreshed every 6h)
//   - vertex_satellite_pass    (pre-computed visibility windows per H3 cell)
//
// Writers: pyzeebe handlers (aircraft_live.py, satellite_live.py) write
// directly via psycopg3 sync_cursor (ADR-0036 worker-direct, no PDS).
//
// RisingWave constraints: no ON CONFLICT, no transactions. Use idempotent
// PK INSERTs (RW silently overwrites same-PK rows, [[conventions]] rw-implicit-upsert).

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_aircraft_state (real-time state vectors, snapshot per tick) ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_aircraft_state (
      vertex_id           VARCHAR PRIMARY KEY,
      icao24              VARCHAR,
      callsign            VARCHAR,
      tail_number         VARCHAR,
      lat                 DOUBLE PRECISION,
      lon                 DOUBLE PRECISION,
      baro_altitude_m     DOUBLE PRECISION,
      geo_altitude_m      DOUBLE PRECISION,
      velocity_ms         DOUBLE PRECISION,
      heading_deg         DOUBLE PRECISION,
      vertical_rate_ms    DOUBLE PRECISION,
      on_ground           BOOLEAN,
      squawk              VARCHAR,
      origin_country      VARCHAR,
      source              VARCHAR,
      ts_ms               BIGINT,
      ingested_at_ms      BIGINT,
      actor_did           VARCHAR DEFAULT 'did:web:maps.gftd.ai:flightradar',
      org_did             VARCHAR DEFAULT 'anon',
      sensitivity_ord     INTEGER DEFAULT 1,
      owner_did           VARCHAR DEFAULT 'did:web:maps.gftd.ai'
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_state_icao_ts ON vertex_aircraft_state (icao24, ts_ms DESC)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_state_ts ON vertex_aircraft_state (ts_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_state_country ON vertex_aircraft_state (origin_country)`.execute(db);

  // ── vertex_aircraft_track (compacted trajectory per flight) ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_aircraft_track (
      vertex_id           VARCHAR PRIMARY KEY,
      icao24              VARCHAR,
      callsign            VARCHAR,
      flight_start_ms     BIGINT,
      flight_end_ms       BIGINT,
      origin_iata         VARCHAR,
      dest_iata           VARCHAR,
      path_geojson        VARCHAR,
      max_altitude_m      DOUBLE PRECISION,
      max_velocity_ms     DOUBLE PRECISION,
      point_count         INTEGER,
      actor_did           VARCHAR DEFAULT 'did:web:maps.gftd.ai:flightradar',
      org_did             VARCHAR DEFAULT 'anon',
      sensitivity_ord     INTEGER DEFAULT 1,
      owner_did           VARCHAR DEFAULT 'did:web:maps.gftd.ai',
      created_at          VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_track_icao ON vertex_aircraft_track (icao24, flight_start_ms DESC)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_aircraft_track_callsign ON vertex_aircraft_track (callsign)`.execute(db);

  // ── vertex_satellite_tle (TLE catalog from CelesTrak / Space-Track) ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_satellite_tle (
      vertex_id           VARCHAR PRIMARY KEY,
      norad_id            INTEGER,
      intl_designator     VARCHAR,
      name                VARCHAR,
      line1               VARCHAR,
      line2               VARCHAR,
      epoch_ms            BIGINT,
      mean_motion         DOUBLE PRECISION,
      eccentricity        DOUBLE PRECISION,
      inclination_deg     DOUBLE PRECISION,
      source              VARCHAR,
      catalog_group       VARCHAR,
      ingested_at_ms      BIGINT,
      actor_did           VARCHAR DEFAULT 'did:web:maps.gftd.ai:n2yo',
      org_did             VARCHAR DEFAULT 'anon',
      sensitivity_ord     INTEGER DEFAULT 1,
      owner_did           VARCHAR DEFAULT 'did:web:maps.gftd.ai'
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_satellite_tle_norad ON vertex_satellite_tle (norad_id, epoch_ms DESC)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_satellite_tle_group ON vertex_satellite_tle (catalog_group)`.execute(db);

  // ── vertex_satellite_pass (pre-computed visibility windows) ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_satellite_pass (
      vertex_id           VARCHAR PRIMARY KEY,
      norad_id            INTEGER,
      observer_h3         VARCHAR,
      observer_lat        DOUBLE PRECISION,
      observer_lon        DOUBLE PRECISION,
      aos_ms              BIGINT,
      los_ms              BIGINT,
      tca_ms              BIGINT,
      max_elevation_deg   DOUBLE PRECISION,
      peak_azimuth_deg    DOUBLE PRECISION,
      visible_at_night    BOOLEAN,
      magnitude           DOUBLE PRECISION,
      computed_at_ms      BIGINT,
      actor_did           VARCHAR DEFAULT 'did:web:maps.gftd.ai:n2yo',
      org_did             VARCHAR DEFAULT 'anon',
      sensitivity_ord     INTEGER DEFAULT 1,
      owner_did           VARCHAR DEFAULT 'did:web:maps.gftd.ai'
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_satellite_pass_observer ON vertex_satellite_pass (observer_h3, aos_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_satellite_pass_norad ON vertex_satellite_pass (norad_id, aos_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_satellite_pass_aos ON vertex_satellite_pass (aos_ms)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_satellite_pass`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_satellite_tle`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_aircraft_track`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_aircraft_state`.execute(db);
}
