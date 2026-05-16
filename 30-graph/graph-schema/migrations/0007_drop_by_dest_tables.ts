import { Kysely, sql } from 'kysely';

/**
 * Drop _by_dest reverse tables (CSC dual-write).
 *
 * CSC reads now use streaming MVs (mv_followers, mv_liked_by, mv_reposted_by, mv_replied_by).
 * Remaining _by_dest tables (has_author, links_to, membership, list_item, contains) have no
 * MV equivalent but are unused — no active read paths reference them after Phase 1 migration.
 *
 * RisingWave streaming MVs auto-track base table INSERTs (< 100ms freshness).
 * Manual dual-write to _by_dest tables is no longer needed.
 *
 * See: deps.toml [[migrations."csc-mv-consolidation"]] Phase 3
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_follows_by_dest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_likes_by_dest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_reposts_by_dest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_has_author_by_dest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_reply_by_dest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_links_to_by_dest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_membership_by_dest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_list_item_by_dest`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_contains_by_dest`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  // Re-create would require full DDL from 0001_initial_schema.ts.
  // Intentionally left empty — restore from 0001 if rollback needed.
}
