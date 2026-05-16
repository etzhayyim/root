import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Flight ingester registry (multi-airline, multi-source).
 *
 * Architecture (ADR-0056-shaped):
 *  - vertex_airline               : 1 row per IATA airline (~5000 globally; we
 *                                   seed top 30 by 2024 RPK and grow as needed)
 *  - vertex_flight_offer_source   : 1 row per ingest source. Sources fall into
 *                                   classes (gds | gds_ndc | metasearch |
 *                                   direct_ndc | scrape | stub) and either
 *                                   cover many airlines (Amadeus / Duffel /
 *                                   Kiwi / Travelpayouts) or a single carrier
 *                                   (ana-ndc, jal-ndc, ryanair-direct, ...).
 *  - edge_flight_offer_source_covers_airline : N:M coverage matrix.
 *  - mv_flight_offer_source_coverage : per-source last observation rollup
 *                                      derived from vertex_flight_offer.
 *
 * Adding a new source = INSERT one vertex_flight_offer_source row + register
 * an adapter function in pymagatama.ingest.flight_offer._SOURCE_ADAPTERS keyed
 * by source_id. The pyzeebe primitive `flight.offer.fetchFromSource` looks up
 * the adapter by source_id at runtime; no new primitive per source needed.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_airline (
      vertex_id          VARCHAR PRIMARY KEY,
      iata_code          VARCHAR,
      icao_code          VARCHAR,
      name               VARCHAR,
      country_code       VARCHAR,
      alliance           VARCHAR,
      accepts_ndc        VARCHAR,
      ingest_status      VARCHAR,
      created_at         VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_flight_offer_source (
      vertex_id          VARCHAR PRIMARY KEY,
      source_id          VARCHAR,
      source_type        VARCHAR,
      adapter_key        VARCHAR,
      base_url           VARCHAR,
      auth_scheme        VARCHAR,
      auth_env_key       VARCHAR,
      cadence_minutes    BIGINT,
      rate_limit_rpm     BIGINT,
      airlines_count     BIGINT,
      coverage_note      VARCHAR,
      status             VARCHAR,
      created_at         VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_flight_offer_source_covers_airline (
      edge_id            VARCHAR PRIMARY KEY,
      src_vertex_id      VARCHAR,
      dst_vertex_id      VARCHAR,
      source_id          VARCHAR,
      iata_code          VARCHAR,
      coverage_class     VARCHAR,
      observed_at        VARCHAR,
      created_at         VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_flight_offer_source_coverage AS
    SELECT
      provider AS source_id,
      airline AS iata_code,
      COUNT(*)::BIGINT AS offers_observed,
      MIN(total_price)::DOUBLE PRECISION AS min_total_price,
      MAX(observed_at) AS last_observed_at
    FROM vertex_flight_offer
    WHERE provider IS NOT NULL AND provider <> ''
      AND airline IS NOT NULL AND airline <> ''
    GROUP BY provider, airline
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_flight_offer_source_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_flight_offer_source_covers_airline`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_flight_offer_source`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_airline`.execute(db);
}
