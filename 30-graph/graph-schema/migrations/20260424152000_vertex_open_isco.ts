import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_isco_classification (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      worker_did       varchar NOT NULL,
      isco_code        varchar NOT NULL,
      code_level       varchar NOT NULL,
      employer_did     varchar,
      certificate_url  varchar,
      years_experience double precision,
      confidence       double precision NOT NULL,
      verification     varchar NOT NULL,
      status           varchar NOT NULL,
      classified_at    varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_isco_concordance (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      isco_code        varchar NOT NULL,
      other_taxonomy   varchar NOT NULL,
      other_code       varchar NOT NULL,
      relation         varchar NOT NULL,
      confidence       double precision,
      source           varchar,
      status           varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_isco_classification_occ (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid         varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at      varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_isco_workers_by_occupation AS
    SELECT isco_code, code_level,
           COUNT(*) AS worker_count,
           AVG(confidence) AS avg_confidence,
           AVG(years_experience) AS avg_years_experience,
           MAX(classified_at) AS latest_classified_at
    FROM vertex_open_isco_classification
    WHERE status='confirmed'
    GROUP BY isco_code, code_level
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_isco_workers_by_occupation`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_isco_classification_occ`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_isco_concordance`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_isco_classification`.execute(db);
}
