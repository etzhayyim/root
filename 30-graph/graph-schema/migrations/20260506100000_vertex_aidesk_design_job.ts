import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await db.schema
    .createTable("vertex_aidesk_design_job")
    .ifNotExists()
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey().notNull())
    .addColumn("actor_did", "varchar", (c) => c.notNull())
    .addColumn("org_did", "varchar", (c) => c.notNull())
    .addColumn("at_did", "varchar")
    .addColumn("input_type", "varchar", (c) => c.notNull())
    .addColumn("model_id", "varchar", (c) => c.notNull())
    .addColumn("license_tier", "varchar", (c) => c.notNull())
    .addColumn("status", "varchar", (c) => c.notNull())
    .addColumn("input_b2_keys", sql`text[]`)
    .addColumn("error_message", "varchar")
    .addColumn("created_at", "varchar", (c) => c.notNull())
    .execute();
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await db.schema.dropTable("vertex_aidesk_design_job").ifExists().execute();
}
