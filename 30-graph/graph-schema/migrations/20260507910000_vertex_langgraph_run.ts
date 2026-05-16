/**
 * ADR-2605080600 Phase 2 — vertex_langgraph_run
 *
 * Tracks LangGraph Server /runs execution status in RisingWave.
 * Follows ADR-0095 4-column convention: actor_did / org_did / at_did / created_at.
 */
import type { Kysely } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await db.schema
    .createTable("vertex_langgraph_run")
    .ifNotExists()
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey())
    .addColumn("actor_did", "varchar", (c) => c.notNull())
    .addColumn("org_did", "varchar")
    .addColumn("thread_id", "varchar", (c) => c.notNull())
    .addColumn("checkpoint_ns", "varchar", (c) => c.notNull().defaultTo(""))
    .addColumn("assistant_id", "varchar", (c) => c.notNull())
    .addColumn("status", "varchar", (c) => c.notNull().defaultTo("pending"))
    .addColumn("input_json", "varchar")
    .addColumn("output_json", "varchar")
    .addColumn("error_message", "varchar")
    .addColumn("started_at", "bigint")
    .addColumn("completed_at", "bigint")
    .addColumn("sensitivity_ord", "integer", (c) => c.defaultTo(0))
    .addColumn("owner_did", "varchar")
    .addColumn("created_at", "bigint", (c) => c.notNull())
    .execute();

  // Index for polling pending runs by actor
  await db.schema
    .createIndex("idx_langgraph_run_actor_status")
    .ifNotExists()
    .on("vertex_langgraph_run")
    .columns(["actor_did", "status"])
    .execute();

  // Index for thread lookup
  await db.schema
    .createIndex("idx_langgraph_run_thread")
    .ifNotExists()
    .on("vertex_langgraph_run")
    .column("thread_id")
    .execute();
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await db.schema.dropTable("vertex_langgraph_run").ifExists().execute();
}
