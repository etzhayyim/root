import type { Kysely } from "kysely";
import { sql } from "kysely";
/**
 * open-cyber-vuln — Wave 11 cyber security cluster.
 * DDL applied 2026-04-24 via direct psql (ADR-0048 OOM mitigation).
 */
export async function up(_db: Kysely<unknown>): Promise<void> {
  // Tables: vertex_open_cyber_vuln_cve, vertex_open_cyber_vuln_patch
  // See git commit for applied schema.
}
export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_cyber_vuln_patch`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_cyber_vuln_cve`.execute(db);
}
