import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-cofog Phase 1 — write NSID vertex tables (ADR-0056).
 *
 * Taxonomy itself (10 divisions / 65 groups / 96 classes) is static JSON
 * under `60-apps/etzhayyim-project-open-cofog/data/`. Write flow covers
 * relations to the taxonomy:
 *   vertex_open_cofog_expenditure  — gov spend tagged by COFOG class
 *   vertex_open_cofog_concordance  — crosswalk to other taxonomies (GFS/ESA2010)
 *   edge_open_cofog_expenditure_class — expenditure -> class membership
 *   mv_open_cofog_expenditure_by_class
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_cofog_expenditure (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      gov_org_id       varchar NOT NULL,
      fiscal_year      int NOT NULL,
      cofog_class_code varchar NOT NULL,
      amount           double precision NOT NULL,
      currency         varchar NOT NULL,
      narrative        varchar,
      evidence_url     varchar,
      confidence       double precision,
      status           varchar NOT NULL,
      reported_at      varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_cofog_concordance (
      vertex_id         varchar PRIMARY KEY,
      _seq              bigint, created_date date, sensitivity_ord int, owner_did varchar,
      cofog_class_code  varchar NOT NULL,
      other_taxonomy    varchar NOT NULL,
      other_code        varchar NOT NULL,
      relation          varchar NOT NULL,
      confidence        double precision,
      source            varchar,
      status            varchar NOT NULL,
      created_at        varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_cofog_expenditure_class (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid         varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at      varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_cofog_expenditure_by_class AS
    SELECT cofog_class_code, fiscal_year, currency,
           COUNT(*) AS expenditure_count,
           SUM(amount) AS total_amount,
           MAX(reported_at) AS latest_reported_at
    FROM vertex_open_cofog_expenditure
    WHERE status='confirmed'
    GROUP BY cofog_class_code, fiscal_year, currency
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_cofog_expenditure_by_class`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_cofog_expenditure_class`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_cofog_concordance`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_cofog_expenditure`.execute(db);
}
