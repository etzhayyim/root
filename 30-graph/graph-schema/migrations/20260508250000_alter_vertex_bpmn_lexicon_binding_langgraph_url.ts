import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-2605080700 — per-binding LangGraph Server URL override.
 *
 * `bpmn-dispatcher` (`dispatcher_main.py`) currently dispatches every
 * binding with ``routing_target='langgraph'`` to a single global URL
 * (``LANGGRAPH_SERVER_URL`` env var, default
 * ``http://langgraph-server.mitama-udf.svc.cluster.local:8000``).
 *
 * voxelforge ships its own dedicated pool (``mitama-voxelforge-pool``)
 * exposing ``voxelforge-langgraph.mitama-udf.svc.cluster.local:8000``,
 * not the generic ``langgraph-server`` name.  We add an OPTIONAL
 * ``langgraph_url`` column so per-binding overrides are possible.
 * NULL falls back to the global env var (existing behavior unchanged).
 *
 * Forward-only.  No down() drop because RW cannot drop columns from a
 * live streaming graph; rolling back means setting all values to NULL
 * which restores the old behavior.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_bpmn_lexicon_binding ADD COLUMN IF NOT EXISTS langgraph_url varchar`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`UPDATE vertex_bpmn_lexicon_binding SET langgraph_url = NULL`.execute(db);
}
