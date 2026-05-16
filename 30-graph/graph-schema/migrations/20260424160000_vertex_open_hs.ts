import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-hs Phase 1 — WCO Harmonized System write NSID vertex tables (ADR-0056).
 * Classifications: shipment/good -> 6/8/10-digit HS code.
 * Concordances: HS <-> UNSPSC / SITC / NACE / CPC.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_hs_classification (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint, created_date date, sensitivity_ord int, owner_did varchar,
      shipper_org_id  varchar NOT NULL,
      hs_code         varchar NOT NULL,
      product_description varchar,
      country_of_origin varchar,
      value_usd       double precision,
      quantity        double precision,
      unit_code       varchar,
      confidence      double precision NOT NULL,
      verification    varchar NOT NULL,
      status          varchar NOT NULL,
      classified_at   varchar NOT NULL,
      created_at      varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_hs_concordance (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      hs_code        varchar NOT NULL,
      other_taxonomy varchar NOT NULL,
      other_code     varchar NOT NULL,
      relation       varchar NOT NULL,
      confidence     double precision,
      source         varchar,
      status         varchar NOT NULL,
      created_at     varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_hs_classification_class (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_hs_shipments_by_code AS
    SELECT hs_code, country_of_origin,
           COUNT(*) AS shipment_count,
           SUM(value_usd) AS total_value_usd,
           AVG(confidence) AS avg_confidence,
           MAX(classified_at) AS latest_classified_at
    FROM vertex_open_hs_classification
    WHERE status='confirmed'
    GROUP BY hs_code, country_of_origin
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_hs_shipments_by_code`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_hs_classification_class`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_hs_concordance`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_hs_classification`.execute(db);
}
