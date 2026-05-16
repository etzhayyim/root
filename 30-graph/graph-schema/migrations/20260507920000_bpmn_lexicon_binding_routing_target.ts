/**
 * ADR-2605080600 Phase 3 — add routing_target to vertex_bpmn_lexicon_binding.
 *
 * routing_target values:
 *   'zeebe'      (default) — existing pyzeebe / Zeebe gRPC path
 *   'langgraph'            — LangGraph Server /runs HTTP path
 *                            (http://langgraph-server.mitama-udf.svc:8000/runs)
 *
 * bpmn-dispatcher reads this column at binding lookup time and routes
 * accordingly. Existing rows default to 'zeebe' via coalesce in the query.
 */
import { type Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_bpmn_lexicon_binding ADD COLUMN routing_target varchar`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_bpmn_lexicon_binding DROP COLUMN routing_target`.execute(db);
}
