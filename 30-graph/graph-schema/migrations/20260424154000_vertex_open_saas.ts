import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-saas Phase 1 — SaaS product catalog + UNSPSC mapping (ADR-0056).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_saas_product (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      product_name     varchar NOT NULL,
      vendor_did       varchar NOT NULL,
      vendor_country   varchar,
      homepage         varchar,
      category         varchar NOT NULL,
      pricing_tier     varchar,
      data_residency   varchar,
      soc2             boolean,
      iso27001         boolean,
      gdpr_compliant   boolean,
      risk_score       varchar NOT NULL,
      require_security_review boolean,
      status           varchar NOT NULL,
      registered_at    varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_saas_mapping (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      product_vid      varchar NOT NULL,
      unspsc_code      varchar NOT NULL,
      confidence       double precision,
      mapper_did       varchar,
      status           varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_saas_product_unspsc (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid         varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at      varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_saas_products_by_category AS
    SELECT category, risk_score,
           COUNT(*) AS product_count,
           BOOL_OR(require_security_review) AS any_review_required,
           MAX(registered_at) AS latest_registered_at
    FROM vertex_open_saas_product
    WHERE status='active'
    GROUP BY category, risk_score
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_saas_products_by_category`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_saas_product_unspsc`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_saas_mapping`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_saas_product`.execute(db);
}
