import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Flight offer watchlist:
 * - one row per (origin, destination, outbound_date, currency) the platform
 *   should keep refreshing on a cadence
 * - drives the timer-start `flight_offer_poll_watchlist` BPMN
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_flight_offer_watch (
      vertex_id          VARCHAR PRIMARY KEY,
      origin_iata        VARCHAR,
      destination_iata   VARCHAR,
      outbound_date      VARCHAR,
      return_date        VARCHAR,
      currency           VARCHAR,
      threshold_pct      DOUBLE PRECISION,
      cadence_minutes    BIGINT,
      provider_hint      VARCHAR,
      max_offers         BIGINT,
      notify_did         VARCHAR,
      status             VARCHAR,
      last_polled_at     VARCHAR,
      next_due_at        VARCHAR,
      created_at         VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_flight_offer_watch`.execute(db);
}
