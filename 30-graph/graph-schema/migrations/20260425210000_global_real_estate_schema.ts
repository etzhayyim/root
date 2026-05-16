import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Global real-estate graph base.
 *
 * Scope: sale/rental listings, land/building/condo parcels, transaction events,
 * parties, source registries, provenance, and rollups for search/dedup.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_real_estate_source (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      source_id varchar NOT NULL,
      source_kind varchar NOT NULL,
      country_iso2 varchar,
      country_iso3 varchar,
      jurisdiction varchar,
      base_url varchar,
      license varchar,
      refresh_cadence varchar,
      terms_url varchar,
      status varchar,
      last_success_at varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_real_estate_party (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      party_id varchar NOT NULL,
      party_kind varchar NOT NULL,
      name_hash varchar,
      display_name varchar,
      lei varchar,
      did varchar,
      country_iso2 varchar,
      source_id varchar,
      confidence double precision,
      status varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_real_estate_property (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      property_id varchar NOT NULL,
      canonical_property_key varchar NOT NULL,
      property_type varchar NOT NULL,
      country_iso2 varchar NOT NULL,
      country_iso3 varchar,
      admin1 varchar,
      admin2 varchar,
      city varchar,
      postal_code varchar,
      address_text varchar,
      latitude double precision,
      longitude double precision,
      geohash varchar,
      land_area_sqm double precision,
      floor_area_sqm double precision,
      building_area_sqm double precision,
      rooms double precision,
      bedrooms int,
      bathrooms double precision,
      year_built int,
      land_rights_type varchar,
      registry_number varchar,
      cadastral_id varchar,
      source_id varchar,
      source_url varchar,
      data_hash varchar,
      observed_at varchar,
      status varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_real_estate_listing (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      listing_id varchar NOT NULL,
      property_vid varchar,
      canonical_property_key varchar,
      listing_kind varchar NOT NULL,
      offer_status varchar NOT NULL,
      country_iso2 varchar NOT NULL,
      city varchar,
      postal_code varchar,
      geohash varchar,
      currency varchar,
      price double precision,
      rent_period varchar,
      deposit_amount double precision,
      fees_amount double precision,
      price_per_sqm double precision,
      listed_at varchar,
      first_seen_at varchar,
      last_seen_at varchar,
      source_id varchar,
      source_url varchar,
      title varchar,
      summary varchar,
      media_count int,
      agent_party_vid varchar,
      seller_party_vid varchar,
      landlord_party_vid varchar,
      data_hash varchar,
      status varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_real_estate_transaction (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      transaction_id varchar NOT NULL,
      property_vid varchar,
      listing_vid varchar,
      transaction_kind varchar NOT NULL,
      country_iso2 varchar NOT NULL,
      currency varchar,
      amount double precision,
      rent_period varchar,
      contract_start_date varchar,
      contract_end_date varchar,
      signed_at varchar,
      registered_at varchar,
      source_id varchar,
      source_url varchar,
      buyer_party_vid varchar,
      seller_party_vid varchar,
      tenant_party_vid varchar,
      landlord_party_vid varchar,
      broker_party_vid varchar,
      confidence double precision,
      status varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_real_estate_property_party (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      role varchar NOT NULL,
      share_pct double precision,
      valid_from varchar,
      valid_until varchar,
      source_id varchar,
      source_url varchar,
      confidence double precision,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_real_estate_listing_property (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      match_kind varchar NOT NULL,
      confidence double precision,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_real_estate_transaction_party (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      role varchar NOT NULL,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_real_estate_transaction_property (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      match_kind varchar NOT NULL,
      confidence double precision,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  // Deferred: RisingWave 2.8.1 repeatedly cancelled CREATE INDEX jobs in the
  // live dev cluster on 2026-04-25. Keep base table apply idempotent; add
  // indexes out-of-band once DDL settles.
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_property_canonical ON vertex_real_estate_property (canonical_property_key)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_property_country_geo ON vertex_real_estate_property (country_iso2, geohash)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_property_registry ON vertex_real_estate_property (country_iso2, registry_number)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_listing_property ON vertex_real_estate_listing (property_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_listing_market ON vertex_real_estate_listing (country_iso2, listing_kind, offer_status, last_seen_at)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_listing_city_market ON vertex_real_estate_listing (country_iso2, city, listing_kind, offer_status)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_listing_source ON vertex_real_estate_listing (source_id, listing_id)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_transaction_property ON vertex_real_estate_transaction (property_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_re_transaction_kind_at ON vertex_real_estate_transaction (country_iso2, transaction_kind, signed_at)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_edge_re_property_party_src ON edge_real_estate_property_party (src_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_edge_re_property_party_dst ON edge_real_estate_property_party (dst_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_edge_re_listing_property_src ON edge_real_estate_listing_property (src_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_edge_re_listing_property_dst ON edge_real_estate_listing_property (dst_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_edge_re_transaction_party_src ON edge_real_estate_transaction_party (src_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_edge_re_transaction_party_dst ON edge_real_estate_transaction_party (dst_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_edge_re_transaction_property_src ON edge_real_estate_transaction_property (src_vid)`.execute(db);
  // await sql`CREATE INDEX IF NOT EXISTS idx_edge_re_transaction_property_dst ON edge_real_estate_transaction_property (dst_vid)`.execute(db);

  // Deferred for the same DDL stability reason as indexes above.
  // await sql`
  //   CREATE MATERIALIZED VIEW IF NOT EXISTS mv_real_estate_property_latest AS
  //   SELECT
  //     canonical_property_key,
  //     max(vertex_id) AS representative_property_vid,
  //     max(country_iso2) AS country_iso2,
  //     max(property_type) AS property_type,
  //     max(city) AS city,
  //     max(postal_code) AS postal_code,
  //     max(geohash) AS geohash,
  //     max(observed_at) AS latest_observed_at,
  //     count(*) AS source_row_count
  //   FROM vertex_real_estate_property
  //   GROUP BY canonical_property_key
  // `.execute(db);

  // await sql`
  //   CREATE MATERIALIZED VIEW IF NOT EXISTS mv_real_estate_active_listing_market AS
  //   SELECT
  //     country_iso2,
  //     city,
  //     listing_kind,
  //     currency,
  //     count(*) AS listing_count,
  //     avg(price) AS avg_price,
  //     min(price) AS min_price,
  //     max(price) AS max_price,
  //     avg(price_per_sqm) AS avg_price_per_sqm,
  //     max(last_seen_at) AS latest_seen_at
  //   FROM vertex_real_estate_listing
  //   WHERE offer_status IN ('active', 'pending')
  //   GROUP BY country_iso2, city, listing_kind, currency
  // `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_real_estate_active_listing_market`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_real_estate_property_latest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_real_estate_transaction_property`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_real_estate_transaction_party`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_real_estate_listing_property`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_real_estate_property_party`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_real_estate_transaction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_real_estate_listing`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_real_estate_property`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_real_estate_party`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_real_estate_source`.execute(db);
}
