import { Kysely, sql } from 'kysely';

/**
 * GTFS-RT (realtime) tables — Phase 3 of bus/train ingest (遅延 / 運休 / 運行).
 *
 * Static schedule (Phase 2) lives in vertex_maps_trip + vertex_maps_stop_time
 * and answers "next train at stop X" without RT dependence. RT is layered
 * on top so static path keeps working when feeds drop.
 *
 * Two raw tables, append-only. The dumper writes one row per (feed_id, ts)
 * snapshot, the streaming MVs project a "last 24h" window for query paths.
 *
 *   vertex_maps_vehicle_position  — VehiclePosition entity (30s cadence)
 *     PK (feed_id, vehicle_id, ts)
 *
 *   vertex_maps_trip_update       — TripUpdate entity (60s cadence)
 *     PK (feed_id, trip_id, stop_sequence, ts)
 *     status ∈ {SCHEDULED, SKIPPED, NO_DATA}; arrival_delay_sec /
 *     departure_delay_sec are signed integers (positive = late).
 *
 *   vertex_maps_service_alert     — Alert entity (300s cadence)
 *     PK (feed_id, alert_id, ts)
 *
 * Streaming MV pattern (per 90-docs/260424-bsky-compat-risingwave-split.md
 * "Record-log semantics"):
 *   mv_maps_recent_vehicle_position — last 5 min per vehicle
 *   mv_maps_recent_trip_update      — last 30 min per (trip, stop)
 *   mv_maps_active_alerts           — alerts whose active_until > now
 * The MV WHERE-clause is parameter-less so RW evaluates it streaming;
 * stale-row eviction happens at compaction.
 *
 * Gating: this migration is forward-only and creates empty tables. The
 * dumper that populates them (workers/gtfs_rt_dumper.py) refuses to start
 * unless `ODPT_API_KEY` (or `GTFS_RT_FEED_INDEX_URL` for no-auth
 * operators) is set. So the rows stay 0 until operator unblocks Phase 3.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_vehicle_position (
      feed_id          VARCHAR NOT NULL,
      vehicle_id       VARCHAR NOT NULL,
      ts               TIMESTAMPTZ NOT NULL,
      trip_id          VARCHAR,
      route_id         VARCHAR,
      stop_id          VARCHAR,
      lat              DOUBLE PRECISION,
      lng              DOUBLE PRECISION,
      bearing          REAL,
      speed_mps        REAL,
      occupancy_status VARCHAR,
      current_status   VARCHAR,
      congestion_level VARCHAR,
      label            VARCHAR,
      raw_pb_b64       VARCHAR,
      PRIMARY KEY (feed_id, vehicle_id, ts)
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_trip_update (
      feed_id               VARCHAR NOT NULL,
      trip_id               VARCHAR NOT NULL,
      stop_sequence         INT     NOT NULL,
      ts                    TIMESTAMPTZ NOT NULL,
      stop_id               VARCHAR,
      route_id              VARCHAR,
      schedule_relationship VARCHAR,
      arrival_delay_sec     INT,
      departure_delay_sec   INT,
      arrival_time          TIMESTAMPTZ,
      departure_time        TIMESTAMPTZ,
      uncertainty_sec       INT,
      PRIMARY KEY (feed_id, trip_id, stop_sequence, ts)
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_service_alert (
      feed_id            VARCHAR NOT NULL,
      alert_id           VARCHAR NOT NULL,
      ts                 TIMESTAMPTZ NOT NULL,
      cause              VARCHAR,
      effect             VARCHAR,
      severity           VARCHAR,
      header_text        VARCHAR,
      description        VARCHAR,
      url                VARCHAR,
      active_from        TIMESTAMPTZ,
      active_until       TIMESTAMPTZ,
      affected_route_ids VARCHAR,
      affected_stop_ids  VARCHAR,
      affected_trip_ids  VARCHAR,
      PRIMARY KEY (feed_id, alert_id, ts)
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_rt_vp_feed_ts
      ON vertex_maps_vehicle_position (feed_id, ts DESC)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_rt_tu_trip_stop
      ON vertex_maps_trip_update (feed_id, trip_id, stop_id, ts DESC)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_rt_alert_active
      ON vertex_maps_service_alert (feed_id, active_until DESC)
  `.execute(db);

  // Streaming MV: last 5 min of vehicle positions, dedup to latest per
  // (feed, vehicle). Window = 5 min so map UI shows fresh dots only.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_recent_vehicle_position AS
      SELECT DISTINCT ON (feed_id, vehicle_id)
        feed_id, vehicle_id, ts, trip_id, route_id, stop_id,
        lat, lng, bearing, speed_mps,
        occupancy_status, current_status, congestion_level, label
      FROM vertex_maps_vehicle_position
      WHERE ts > now() - INTERVAL '5 minutes'
      ORDER BY feed_id, vehicle_id, ts DESC
  `.execute(db);

  // Streaming MV: latest trip_update per (feed, trip, stop). The
  // realtimeDelaysAtStop XRPC LEFT JOINs nextDeparturesAtStop against
  // this so a missing RT row falls through to the static schedule.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_recent_trip_update AS
      SELECT DISTINCT ON (feed_id, trip_id, stop_sequence)
        feed_id, trip_id, stop_sequence, stop_id, route_id, ts,
        schedule_relationship,
        arrival_delay_sec, departure_delay_sec,
        arrival_time, departure_time, uncertainty_sec
      FROM vertex_maps_trip_update
      WHERE ts > now() - INTERVAL '30 minutes'
      ORDER BY feed_id, trip_id, stop_sequence, ts DESC
  `.execute(db);

  // Streaming MV: alerts whose active window covers "now".
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_active_alerts AS
      SELECT DISTINCT ON (feed_id, alert_id)
        feed_id, alert_id, ts, cause, effect, severity,
        header_text, description, url,
        active_from, active_until,
        affected_route_ids, affected_stop_ids, affected_trip_ids
      FROM vertex_maps_service_alert
      WHERE (active_until IS NULL OR active_until > now())
        AND ts > now() - INTERVAL '24 hours'
      ORDER BY feed_id, alert_id, ts DESC
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_active_alerts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_recent_trip_update`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_recent_vehicle_position`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_maps_rt_alert_active`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_maps_rt_tu_trip_stop`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_maps_rt_vp_feed_ts`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps_service_alert`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps_trip_update`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps_vehicle_position`.execute(db);
}
