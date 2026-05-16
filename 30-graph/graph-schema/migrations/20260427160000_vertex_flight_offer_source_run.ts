import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Per-fetch run log for ingest source observability.
 *
 * Every call to flight.offer.fetchFromSource (incl. those issued internally
 * by pollWatchlist's multi-source fan-out) appends one row. The companion MV
 * mv_flight_offer_source_health rolls up success rate + latency over 24h so
 * operators can see which sources are healthy without scanning offer rows.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_flight_offer_source_run (
      vertex_id          VARCHAR PRIMARY KEY,
      run_id             VARCHAR,
      source_id          VARCHAR,
      resolved_source    VARCHAR,
      origin_iata        VARCHAR,
      destination_iata   VARCHAR,
      outbound_date      VARCHAR,
      return_date        VARCHAR,
      currency           VARCHAR,
      status             VARCHAR,
      error_class        VARCHAR,
      error_message      VARCHAR,
      offers_fetched     BIGINT,
      offers_written     BIGINT,
      latency_ms         BIGINT,
      observed_at        VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_flight_offer_source_health AS
    SELECT
      source_id,
      COUNT(*)::BIGINT                                              AS runs_total,
      SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END)::BIGINT        AS runs_ok,
      SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END)::BIGINT     AS runs_error,
      SUM(CASE WHEN status = 'fallback' THEN 1 ELSE 0 END)::BIGINT  AS runs_fallback,
      AVG(latency_ms)::DOUBLE PRECISION                             AS avg_latency_ms,
      SUM(offers_written)::BIGINT                                   AS offers_written_total,
      MAX(observed_at)                                              AS last_run_at,
      MAX(CASE WHEN status = 'ok' THEN observed_at ELSE NULL END)   AS last_ok_at
    FROM vertex_flight_offer_source_run
    GROUP BY source_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_flight_offer_source_health`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_flight_offer_source_run`.execute(db);
}
