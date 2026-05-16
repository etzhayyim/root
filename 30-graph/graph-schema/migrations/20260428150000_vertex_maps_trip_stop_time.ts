import { Kysely, sql } from 'kysely';

/**
 * GTFS-JP per-trip + per-stop-time tables (Phase 2 of bus/train/海路/空路 ingest).
 *
 * Phase 1 collapsed each route to a single vertex_spatial row with a JSON
 * timetable summary in props. That is fine for "show route shape on map"
 * but cannot answer the canonical user query "what is the next train at
 * stop X". A full 47-pref index pushes stop_times to 50-200M rows, which
 * cannot live as nested JSON on the route row.
 *
 * Two new tables, sized for the (a) "next train at stop X" read pattern:
 *
 *   vertex_maps_trip
 *     PK (feed_id, trip_id) — one row per published trip.
 *     route_id / service_id link back to vertex_spatial(label='Railway'|'BusRoute')
 *     and to vertex_maps_stop_time. headsign / direction_id help the UI.
 *
 *   vertex_maps_stop_time
 *     PK (feed_id, trip_id, stop_sequence) — one row per scheduled call.
 *     stop_id is a string ref to vertex_spatial(label='Station'|'BusStop').
 *     departure_time is HH:MM:SS string (GTFS allows >24:00:00 for past-midnight
 *     trips, so we keep it textual and parse client-side).
 *
 * Idempotency on RisingWave (no ON CONFLICT, append-only): the dumper
 * MUST `DELETE FROM <tbl> WHERE feed_id = ?` before re-INSERTing a feed.
 * See ADR-0036 / root CLAUDE.md "Record-log semantics, not MST" for why
 * delete-then-insert is the canonical pattern.
 *
 * Indexes:
 *   idx_maps_stop_time_stop_dep (stop_id, departure_time)
 *     serves the (a) read pattern. departure_time is sortable as text under
 *     GTFS's HH:MM:SS convention (lexicographic == chronological for any
 *     given service-day).
 *   idx_maps_trip_route (feed_id, route_id)
 *     serves "all trips on this route" backfill.
 *   idx_maps_trip_service (feed_id, service_id)
 *     serves day-of-week filtering against vertex_spatial(props.service_days).
 *
 * Not added (deliberately, per advisor #5): a (feed, route_id, stop_sequence)
 * index for "this route's full timetable". Add it only when a Phase 2.x read
 * pattern actually needs it.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_trip (
      feed_id        VARCHAR NOT NULL,
      trip_id        VARCHAR NOT NULL,
      route_id       VARCHAR NOT NULL,
      service_id     VARCHAR,
      shape_id       VARCHAR,
      direction_id   SMALLINT,
      headsign       VARCHAR,
      short_name     VARCHAR,
      block_id       VARCHAR,
      wheelchair_accessible SMALLINT,
      bikes_allowed  SMALLINT,
      agency         VARCHAR,
      prefecture     VARCHAR,
      created_at     TIMESTAMPTZ DEFAULT now(),
      PRIMARY KEY (feed_id, trip_id)
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_stop_time (
      feed_id        VARCHAR NOT NULL,
      trip_id        VARCHAR NOT NULL,
      stop_sequence  INT     NOT NULL,
      stop_id        VARCHAR NOT NULL,
      arrival_time   VARCHAR,
      departure_time VARCHAR,
      pickup_type    SMALLINT,
      drop_off_type  SMALLINT,
      stop_headsign  VARCHAR,
      shape_dist_traveled DOUBLE PRECISION,
      timepoint      SMALLINT,
      PRIMARY KEY (feed_id, trip_id, stop_sequence)
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_stop_time_stop_dep
      ON vertex_maps_stop_time (stop_id, departure_time)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_trip_route
      ON vertex_maps_trip (feed_id, route_id)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_trip_service
      ON vertex_maps_trip (feed_id, service_id)
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_maps_trip_service`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_maps_trip_route`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_maps_stop_time_stop_dep`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps_stop_time`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps_trip`.execute(db);
}
