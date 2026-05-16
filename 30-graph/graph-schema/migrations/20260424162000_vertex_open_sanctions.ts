import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-sanctions Phase 1 — consolidated sanctions lists (OFAC/EU/UN/UK).
 * Entries are authority-published list rows. Screenings record caller-submitted
 * candidates + match score + gateway decision (block / manual-review / pass).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_sanctions_entry (
      vertex_id     varchar PRIMARY KEY,
      _seq          bigint, created_date date, sensitivity_ord int, owner_did varchar,
      program       varchar NOT NULL,
      list_id       varchar NOT NULL,
      entity_name   varchar NOT NULL,
      entity_type   varchar NOT NULL,
      country       varchar,
      sanction_type varchar,
      aliases       varchar,
      listed_at     varchar NOT NULL,
      delisted_at   varchar,
      status        varchar NOT NULL,
      created_at    varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_sanctions_screening (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      caller_org_id  varchar NOT NULL,
      candidate_name varchar NOT NULL,
      candidate_country varchar,
      candidate_lei  varchar,
      best_match_name varchar,
      best_match_program varchar,
      match_score    double precision NOT NULL,
      decision       varchar NOT NULL,
      require_manual_review boolean,
      screened_at    varchar NOT NULL,
      created_at     varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_sanctions_screening_entry (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_sanctions_blocks_by_program AS
    SELECT best_match_program AS program, decision,
           COUNT(*) AS screening_count,
           MAX(screened_at) AS latest_screened_at
    FROM vertex_open_sanctions_screening
    WHERE decision IN ('block','manual-review')
    GROUP BY best_match_program, decision
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_sanctions_blocks_by_program`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_sanctions_screening_entry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_sanctions_screening`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_sanctions_entry`.execute(db);
}
