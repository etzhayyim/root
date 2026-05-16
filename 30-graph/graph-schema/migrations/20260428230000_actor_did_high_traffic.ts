// ADR-0095 P3 — Incremental actor_did / org_did columns for high-traffic tables.
//
// Existing tables with org_id/user_id/actor_id are grandfathered (ADR-0095 §D2).
// This migration adds actor_did + org_did alongside the old columns so new writes
// can populate both. Old columns stay in place; backfill is tracked separately in
// deps.toml [[migrations]] identity-canonical-columns-backfill.
//
// Tables covered:
//   vertex_repo_record     — 15.6M rows. actor_did = repo DID (set by PDS core.ts on new writes).
//   vertex_ipaddress_access_log — high write-rate (every XRPC). actor_did = caller_did.
//
// Indexes added for tenant-scoped queries.

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_repo_record — no old org/user columns, just add canonical ones.
  // actor_did = repo (the AT Protocol repo owner DID) — populated on new writes by PDS core.ts.
  // org_did defaults to 'anon' sentinel until org resolution is implemented.
  await sql`ALTER TABLE vertex_repo_record ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_repo_record ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_repo_record_actor_did
      ON vertex_repo_record (actor_did)
  `.execute(db);

  // vertex_ipaddress_access_log — has old org_id/user_id/actor_id; add canonical cols.
  // actor_did = caller_did (the authenticated caller's ERC725 DID or federation alias).
  await sql`ALTER TABLE vertex_ipaddress_access_log ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_ipaddress_access_log ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon'`.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_ipaddress_access_log_actor_did
      ON vertex_ipaddress_access_log (actor_did)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_ipaddress_access_log_actor_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_repo_record_actor_did`.execute(db);
  // RisingWave does not support DROP COLUMN — down() is a no-op for column additions.
}
