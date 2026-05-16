import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-unispsc Phase 1 — procurement + supplier write flows (ADR-0056).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_unispsc_procurement (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      buyer_org_id     varchar NOT NULL,
      commodity_code   varchar NOT NULL,
      quantity         double precision NOT NULL,
      unit_price       double precision NOT NULL,
      currency         varchar NOT NULL,
      total_amount     double precision NOT NULL,
      dangerous_goods  boolean,
      sanctions_check  varchar,
      approval_tier    varchar NOT NULL,
      require_cab      boolean,
      status           varchar NOT NULL,
      submitted_at     varchar NOT NULL,
      approved_at      varchar,
      settled_at       varchar,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_unispsc_supplier (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      supplier_did     varchar NOT NULL,
      commodity_code   varchar NOT NULL,
      legal_name       varchar,
      country          varchar,
      kyc_cleared      boolean,
      quality_score    double precision,
      risk_tier        varchar NOT NULL,
      require_manual_kyc boolean,
      status           varchar NOT NULL,
      registered_at    varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_unispsc_procurement_commodity (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid         varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at      varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_unispsc_procurement_by_commodity AS
    SELECT commodity_code, currency,
           COUNT(*) AS procurement_count,
           SUM(total_amount) AS total_spend,
           BOOL_OR(require_cab) AS any_cab_approval,
           MAX(submitted_at) AS latest_submitted_at
    FROM vertex_open_unispsc_procurement
    WHERE status IN ('submitted','approved','settled')
    GROUP BY commodity_code, currency
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_unispsc_procurement_by_commodity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_unispsc_procurement_commodity`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_unispsc_supplier`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_unispsc_procurement`.execute(db);
}
