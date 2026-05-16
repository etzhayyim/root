import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_other_count`.execute(db);
  // Drop MVs that depend on edge_other / vertex_other (CASCADE handles transitives)
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_domain_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_procedure_full`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_filing_path`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_court_hierarchy`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_state_fee_variant`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_authority_chain`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_lawyer_capability`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_in_appeal_path`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_other`.execute(db);
  await sql`DROP VIEW IF EXISTS view_actor_universal`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_other`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No down migration: catch-all graph tables are intentionally prohibited.
}
