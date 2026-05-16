import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 0018: vertex_ip_address table for collector IP/GeoIP intelligence.
 *
 * Stores IP addresses with GeoIP enrichment (MaxMind GeoLite2 via local
 * geoip-server). Linked to vertex_dns_observation via A record props.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ip_address (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      label             VARCHAR,
      did               VARCHAR,
      address           VARCHAR,
      country_code      VARCHAR,
      city              VARCHAR,
      region            VARCHAR,
      lat               DOUBLE PRECISION,
      lon               DOUBLE PRECISION,
      asn               VARCHAR,
      asn_org           VARCHAR,
      isp               VARCHAR,
      is_proxy          BOOLEAN,
      is_datacenter     BOOLEAN,
      is_tor            BOOLEAN,
      ptr_record        VARCHAR,
      observed_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_ip_address`.execute(db);
}
