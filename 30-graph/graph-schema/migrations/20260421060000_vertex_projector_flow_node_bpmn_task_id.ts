import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 5g (ADR-0045 §D4): bridge projector flow nodes to Kyber
 * BPMN_CATALOG entries via bpmn_task_id at the node level.
 *
 * The original Phase 1 migration put bpmn_task_id on
 * vertex_projector_flow only (flow-level hint). ADR-0045 §D4
 * authoritatively scopes it to the node so that an individual tool
 * node can reference a specific catalog entry. When set, the runner
 * populates vertex_projector_flow_step.bpmn_activity_id and uses the
 * catalog's specific ocelEventType (e.g. journal.posted) — via
 * config_json.ocel_event_type — instead of the generic
 * tool.completed.
 *
 * No new index yet: bpmn_task_id lookups are currently only via
 * (flow_vertex_id, node_key) which is already covered.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_projector_flow_node
    ADD COLUMN IF NOT EXISTS bpmn_task_id VARCHAR
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_projector_flow_node
    DROP COLUMN IF EXISTS bpmn_task_id
  `.execute(db);
}
