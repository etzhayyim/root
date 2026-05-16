import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Persist GLEIF cursor pagination checkpoints per shard.
 *
 * The official GLEIF API rejects page[number] pagination beyond 10,000
 * records, so long-running backfills must resume from the previous
 * links.next cursor instead of replaying cursor pages from the beginning.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_open_lei_gleif_shard
    ADD COLUMN IF NOT EXISTS request_url VARCHAR
  `.execute(db);

  await sql`
    ALTER TABLE vertex_open_lei_gleif_shard
    ADD COLUMN IF NOT EXISTS next_url VARCHAR
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_open_lei_gleif_shard
    DROP COLUMN IF EXISTS next_url
  `.execute(db);

  await sql`
    ALTER TABLE vertex_open_lei_gleif_shard
    DROP COLUMN IF EXISTS request_url
  `.execute(db);
}
