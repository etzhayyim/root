import type { Kysely } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await db.schema
    .createTable("vertex_aidesk_artifact")
    .ifNotExists()
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey().notNull())
    .addColumn("job_id", "varchar", (c) => c.notNull())
    .addColumn("actor_did", "varchar", (c) => c.notNull())
    .addColumn("org_did", "varchar", (c) => c.notNull())
    .addColumn("at_did", "varchar")
    .addColumn("format", "varchar", (c) => c.notNull())
    .addColumn("b2_key", "varchar", (c) => c.notNull())
    .addColumn("license_tier", "varchar", (c) => c.notNull())
    .addColumn("cadquery_code", "text")
    .addColumn("tsukuru_package_id", "varchar")
    .addColumn("created_at", "varchar", (c) => c.notNull())
    .execute();

  await db.schema
    .createTable("edge_aidesk_job_artifact")
    .ifNotExists()
    .addColumn("src_vertex_id", "varchar", (c) => c.notNull())
    .addColumn("dst_vertex_id", "varchar", (c) => c.notNull())
    .addColumn("created_at", "varchar", (c) => c.notNull())
    .addPrimaryKeyConstraint("edge_aidesk_job_artifact_pkey", ["src_vertex_id", "dst_vertex_id"])
    .execute();

  // Research artifacts — isolated from commercial path (Non-Commercial models only)
  await db.schema
    .createTable("vertex_aidesk_research_artifact")
    .ifNotExists()
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey().notNull())
    .addColumn("actor_did", "varchar", (c) => c.notNull())
    .addColumn("org_did", "varchar", (c) => c.notNull())
    .addColumn("at_did", "varchar")
    .addColumn("model_id", "varchar", (c) => c.notNull())
    .addColumn("license_tier", "varchar", (c) => c.notNull().defaultTo("adsk-noncommercial"))
    .addColumn("input_type", "varchar", (c) => c.notNull())
    .addColumn("b2_key", "varchar", (c) => c.notNull())
    .addColumn("created_at", "varchar", (c) => c.notNull())
    .execute();
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await db.schema.dropTable("vertex_aidesk_research_artifact").ifExists().execute();
  await db.schema.dropTable("edge_aidesk_job_artifact").ifExists().execute();
  await db.schema.dropTable("vertex_aidesk_artifact").ifExists().execute();
}
