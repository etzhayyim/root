import type { Kysely } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // Cursor-based pagination state for commonCrawl.entities.extract.
  // Avoids full-scan IS NULL filter on vertex_page (985M rows).
  // One row per domain; last_vertex_id = '' means start from beginning.
  await db.schema
    .createTable("vertex_cc_entity_cursor")
    .ifNotExists()
    .addColumn("domain", "varchar", (c) => c.notNull())
    .addColumn("last_vertex_id", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("updated_at", "varchar", (c) => c.notNull().defaultTo(""))
    .addPrimaryKeyConstraint("vertex_cc_entity_cursor_pkey", ["domain"])
    .execute();
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await db.schema.dropTable("vertex_cc_entity_cursor").ifExists().execute();
}
