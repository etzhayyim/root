import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Flight offer drop-alert log:
 * - one row per detected price drop above the configured threshold
 * - powers `app.etzhayyim.apps.flightOffer.checkPriceDrop` BPMN + downstream
 *   notification fan-out (kept narrow; presentation layer joins as needed)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_flight_offer_alert (
      vertex_id          VARCHAR PRIMARY KEY,
      origin_iata        VARCHAR,
      destination_iata   VARCHAR,
      outbound_date      VARCHAR,
      currency           VARCHAR,
      previous_price     DOUBLE PRECISION,
      new_price          DOUBLE PRECISION,
      drop_pct           DOUBLE PRECISION,
      provider           VARCHAR,
      booking_url        VARCHAR,
      observed_at        VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_flight_offer_alert`.execute(db);
}
