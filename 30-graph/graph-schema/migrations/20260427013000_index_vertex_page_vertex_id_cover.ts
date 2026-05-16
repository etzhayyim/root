import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`SET BACKGROUND_DDL = true`.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_page_vertex_id_cover
    ON vertex_page(vertex_id)
    INCLUDE (rkey, url, domain, title, status_code, content_type)
    DISTRIBUTED BY (vertex_id)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_page_vertex_id_cover`.execute(db);
}
