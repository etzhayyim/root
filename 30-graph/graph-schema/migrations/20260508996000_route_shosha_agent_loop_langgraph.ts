/**
 * ADR-2605080600 Phase 4 canary — route shosha.agentLoop to LangGraph Server.
 *
 * The shosha_agent_loop graph is already registered in langgraph_server_app.
 * This migration switches only the interactive XRPC binding:
 *
 *   ai.gftd.apps.shosha.agentLoop -> assistant_id "shosha_agent_loop"
 *
 * Other shosha write/check bindings remain on Zeebe until each graph has a
 * dedicated LangGraph replacement and rollout evidence.
 */
import { type Kysely, sql } from "kysely";

const ownerDid = "did:web:shosha.gftd.ai";
const actorTag = "sys.bpmn.route.shosha.langgraph";
const createdAt = "2026-05-08T09:56:00Z";
const bindingVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/shosha-agentLoop-langgraph-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET bpmn_process_id = 'shosha_agent_loop',
        bpmn_version = 1,
        result_timeout_ms = CAST(120000 AS integer),
        routing_target = 'langgraph'
    WHERE nsid = 'ai.gftd.apps.shosha.agentLoop'
      AND status = 'active'
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
       result_timeout_ms, status, created_at, sensitivity_ord,
       org_id, user_id, actor_id, routing_target)
    SELECT
      ${bindingVertexId}, ${ownerDid},
      'ai.gftd.apps.shosha.agentLoop',
      'shosha_agent_loop',
      1,
      CAST(120000 AS integer),
      'active', ${createdAt}, 1,
      ${ownerDid}, ${ownerDid}, ${actorTag},
      'langgraph'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding
      WHERE nsid = 'ai.gftd.apps.shosha.agentLoop'
        AND status = 'active'
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_lexicon_binding
    WHERE vertex_id = ${bindingVertexId}
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET bpmn_process_id = 'shosha_agent_loop',
        bpmn_version = 1,
        result_timeout_ms = CAST(60000 AS integer),
        routing_target = 'zeebe'
    WHERE nsid = 'ai.gftd.apps.shosha.agentLoop'
      AND status = 'active'
  `.execute(db);
}
