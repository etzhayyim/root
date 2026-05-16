import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (sanctions list — public PII (legal entities + designated persons)
//          but exposes regulatory-determined identity, not financial data)

/**
 * shosha.gftd.ai Phase 2b — live sanctions list (OFAC SDN first).
 *
 * Replaces the static curated sieve in `task_shosha_comply_sanctions_check`
 * with a daily-refreshed table. Phase 2b ingests OFAC SDN only; EU
 * consolidated / UN 1267 / JP MOFA deferred to Phase 2b-extended (parser
 * complexity higher). Static `_SANCTIONED_COUNTRIES` /
 * `_SANCTIONED_ENTITY_KEYWORDS` constants stay as defense-in-depth fast
 * path for hard-coded country / entity blocks.
 *
 * Tables (1 vertex + 1 streaming MV):
 *   vertex_shosha_sanctions_list  one row per (list_source, source_ref)
 *   mv_shosha_sanctions_count_by_source
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_sanctions_list (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      list_source varchar NOT NULL,
      source_ref varchar NOT NULL,
      entity_type varchar,
      name varchar NOT NULL,
      name_normalized varchar NOT NULL,
      aliases varchar,
      country varchar,
      nationality varchar,
      list_program varchar,
      title varchar,
      remarks varchar,
      listed_at date,
      raw_json varchar,
      refreshed_at varchar NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_sanctions_count_by_source AS
      SELECT
        list_source,
        entity_type,
        COUNT(*) AS active_count
      FROM vertex_shosha_sanctions_list
      WHERE status = 'active'
      GROUP BY list_source, entity_type;
  `.execute(db);

  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_sanctions_list TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_sanctions_list TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`REVOKE ALL ON vertex_shosha_sanctions_list FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_shosha_sanctions_list FROM root`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shosha_sanctions_count_by_source`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_sanctions_list`.execute(db);
}
