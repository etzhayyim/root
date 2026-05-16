/**
 * ADR-2605080600 Phase 4 — ki.synthesize → LangGraph Server.
 *
 * Routes ai.gftd.apps.ki.synthesize to LangGraph Server as assistant_id
 * 'ki.synthesize.v1'. No BPMN process_def needed for langgraph-routed
 * bindings; the binding alone instructs bpmn-dispatcher to POST /runs.
 */
import { type Kysely, sql } from "kysely";

const ownerDid = "did:web:bpmn.gftd.ai";
const actorTag = "did:web:bpmn.gftd.ai";
const createdAt = "2026-05-08T09:30:00Z";

const BINDING_VID =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/ki-synthesize-langgraph-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
       result_timeout_ms, status, created_at, sensitivity_ord,
       org_id, user_id, actor_id, routing_target)
    SELECT
      ${BINDING_VID}, ${ownerDid},
      'ai.gftd.apps.ki.synthesize',
      'ki.synthesize.v1',
      1,
      CAST(120000 AS integer),
      'active', ${createdAt}, 1,
      ${ownerDid}, ${ownerDid}, ${actorTag},
      'langgraph'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}`.execute(db);
}
