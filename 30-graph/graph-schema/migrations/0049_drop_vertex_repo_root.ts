import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/** Migration 0049: replace vertex_repo_root with repo+seq index on commit log. */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_repo_commit_repo_seq ON vertex_repo_commit(repo, seq)`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_repo_root_rev`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_repo_root`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_repo_root`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`CREATE TABLE IF NOT EXISTS vertex_repo_root (
    did VARCHAR PRIMARY KEY,
    cid VARCHAR NOT NULL,
    rev VARCHAR NOT NULL,
    indexed_at VARCHAR NOT NULL,
    created_at VARCHAR NOT NULL
  )`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_repo_root_rev ON vertex_repo_root(rev)`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_repo_commit_repo_seq`.execute(db);
}
