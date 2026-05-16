import { Kysely, sql } from 'kysely';

/** Migration 0044: add seq index for vertex_repo_commit. */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_repo_commit_seq ON vertex_repo_commit(seq)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_repo_commit_seq`.execute(db);
}
