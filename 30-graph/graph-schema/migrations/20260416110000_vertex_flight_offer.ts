import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Flight offer price spine:
 * - dedicated offer table for crawler/metasearch prices with booking links
 * - cheapest offer MV by route/date/currency for fast list queries
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_flight_offer (
      vertex_id          VARCHAR PRIMARY KEY,
      offer_id           VARCHAR,
      provider           VARCHAR,
      airline            VARCHAR,
      flight_number      VARCHAR,
      origin_iata        VARCHAR,
      destination_iata   VARCHAR,
      outbound_date      VARCHAR,
      return_date        VARCHAR,
      base_price         DOUBLE PRECISION,
      taxes              DOUBLE PRECISION,
      total_price        DOUBLE PRECISION,
      currency           VARCHAR,
      booking_url        VARCHAR,
      deeplink_url       VARCHAR,
      observed_at        VARCHAR,
      source_url         VARCHAR,
      props              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_flight_offer_cheapest_by_route_date AS
    WITH best AS (
      SELECT
        origin_iata,
        destination_iata,
        outbound_date,
        currency,
        MIN(total_price)::DOUBLE PRECISION AS cheapest_total_price
      FROM vertex_flight_offer
      WHERE origin_iata IS NOT NULL AND origin_iata <> ''
        AND destination_iata IS NOT NULL AND destination_iata <> ''
        AND outbound_date IS NOT NULL AND outbound_date <> ''
        AND currency IS NOT NULL AND currency <> ''
        AND total_price IS NOT NULL
      GROUP BY origin_iata, destination_iata, outbound_date, currency
    )
    SELECT
      b.origin_iata,
      b.destination_iata,
      b.outbound_date,
      b.currency,
      b.cheapest_total_price,
      MAX(v.booking_url) AS cheapest_booking_url,
      MAX(v.provider) AS cheapest_provider,
      MAX(v.observed_at) AS cheapest_observed_at
    FROM best b
    LEFT JOIN vertex_flight_offer v
      ON v.origin_iata = b.origin_iata
      AND v.destination_iata = b.destination_iata
      AND v.outbound_date = b.outbound_date
      AND v.currency = b.currency
      AND v.total_price = b.cheapest_total_price
    GROUP BY
      b.origin_iata,
      b.destination_iata,
      b.outbound_date,
      b.currency,
      b.cheapest_total_price
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_flight_offer_cheapest_by_route_date`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_flight_offer`.execute(db);
}
