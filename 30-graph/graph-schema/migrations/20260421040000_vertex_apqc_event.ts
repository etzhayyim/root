import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * vertex_apqc_event — typed storage for app.etzhayyim.apps.apqc.apqcEvent
 * OCEL 2.0 event records.
 *
 * ADR-0045 Phase 5a (2026-04-21): the projector flow runner
 * (agent/flow-runner.ts) emits OCEL events per step and stores the
 * record rkey in vertex_projector_flow_step.ocel_event_id.
 *
 * Kyber BPMN Projector (ADR-0025) currently emits the same NSID via
 * sdk.pds.dispatch → AT Repo; that path is silently dropped post
 * graph-worker consumer retirement (same Phase 2 pattern as project
 * metadata / tasks / membership). Kyber's runtime migration to
 * Hyperdrive direct is future work — until then, events land only
 * when the projector runner emits them.
 *
 * Columns:
 *   Standard 7: vertex_id / _seq / created_date / sensitivity_ord /
 *               owner_did / rkey / repo
 *   OCEL body:
 *     ocel_event_id    — Kyber-style ID (e.g. 'ocel-<ulid>'). This is
 *                        distinct from vertex_id; the projector's
 *                        vertex_projector_flow_step.ocel_event_id
 *                        column points to rkey, not ocel_event_id.
 *     apqc_code        — APQC L1 "1.0".."13.0" or L2 "9.1.2"; empty
 *                        for projector-only events.
 *     apqc_l1_name     — human-readable L1 name, denormalized.
 *     task_id          — BPMN taskId when this event corresponds to a
 *                        Kyber BPMN_CATALOG entry; empty otherwise.
 *     event_type       — Phase 3 naming: flow.* / agent.iteration.* /
 *                        tool.* / agent.* — or catalog-specific
 *                        (journal.posted, po.approved, ...).
 *     case_id          — OCEL case identifier (flow_run vertex_id for
 *                        projector emits; order/invoice id for Kyber).
 *     objects_json     — OCEL object refs array (JSON string).
 *     attributes_json  — OCEL attributes map (JSON string).
 *     timestamp        — ISO event timestamp.
 *   Projector cross-ref:
 *     run_vertex_id    — vertex_projector_flow_run.vertex_id when the
 *                        emit came from the projector runner (NULL
 *                        for Kyber emits).
 *     node_key         — vertex_projector_flow_node.node_key of the
 *                        step that emitted, same provenance.
 *   RLS 4: created_at / org_id / user_id / actor_id
 *
 * Indexes:
 *   idx_apqc_event_run     (run_vertex_id, _seq)  — projector audit
 *                           trail lookup for a given run
 *   idx_apqc_event_case    (case_id, timestamp)   — OCEL case-level
 *                           event timeline
 *   idx_apqc_event_type    (event_type, _seq)     — event-type filter
 *                           used by process-mining MVs
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_apqc_event (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      ocel_event_id VARCHAR, apqc_code VARCHAR, apqc_l1_name VARCHAR,
      task_id VARCHAR, event_type VARCHAR, case_id VARCHAR,
      objects_json VARCHAR, attributes_json VARCHAR, timestamp VARCHAR,
      run_vertex_id VARCHAR, node_key VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_apqc_event_run
            ON vertex_apqc_event (run_vertex_id, _seq)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_apqc_event_case
            ON vertex_apqc_event (case_id, timestamp)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_apqc_event_type
            ON vertex_apqc_event (event_type, _seq)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_apqc_event_type`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_apqc_event_case`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_apqc_event_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_apqc_event`.execute(db);
}
