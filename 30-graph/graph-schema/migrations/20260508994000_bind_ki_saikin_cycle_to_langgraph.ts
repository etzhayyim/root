/**
 * ADR-2605080600 Phase 4 — bind ki.cycle.v1 + saikin.cycle.v1 to LangGraph
 * Server, retire the BPMN process_defs.
 *
 * Active path going forward (per actor):
 *   K8s CronJob → POST {dispatcher}/xrpc/ai.gftd.apps.{actor}.cycle
 *     → bpmn-dispatcher routes via vertex_bpmn_lexicon_binding
 *       (routing_target='langgraph', bpmn_process_id=<assistant_id>)
 *     → POST {langgraph-server}/runs body={assistant_id, input}
 *     → ki_cycle.build_graph() / saikin_cycle.build_graph() executes
 *
 * The pyzeebe ki/saikin worker pools + BPMN process_defs become dead code
 * once LangGraph Server is the registered execution backend.
 */
import type { Kysely } from "kysely";
import { sql } from "kysely";

const OWNER = "did:web:bpmn.gftd.ai";
const CREATED_AT = "2026-05-08T11:30:00Z";

type Binding = {
  vertexId: string;
  nsid: string;
  assistantId: string;
};

const BINDINGS: Binding[] = [
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/ki-cycle-langgraph-v1",
    nsid: "ai.gftd.apps.ki.cycle",
    assistantId: "ki.cycle.v1",
  },
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/saikin-cycle-langgraph-v1",
    nsid: "ai.gftd.apps.saikin.cycle",
    assistantId: "saikin.cycle.v1",
  },
];

// Old timer-start BPMN process_defs to mark inactive (LangGraph chain replaces them).
const RETIRED_PROCESS_DEFS = [
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ki-vascular-synthesis-cycle-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/saikin-horizontal-transfer-cycle-v1",
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const b of BINDINGS) {
    await sql`
      DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId}
    `.execute(db);
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
         result_timeout_ms, status, created_at, sensitivity_ord,
         org_id, user_id, actor_id, routing_target)
      VALUES (
        ${b.vertexId}, ${OWNER}, ${b.nsid},
        ${b.assistantId}, 1,
        CAST(180000 AS integer),
        'active', ${CREATED_AT}, 1,
        ${OWNER}, ${OWNER}, ${OWNER},
        'langgraph'
      )
    `.execute(db);
  }

  for (const pdId of RETIRED_PROCESS_DEFS) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET status = 'inactive'
      WHERE vertex_id = ${pdId}
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const b of BINDINGS) {
    await sql`
      DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId}
    `.execute(db);
  }
  for (const pdId of RETIRED_PROCESS_DEFS) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET status = 'active'
      WHERE vertex_id = ${pdId}
    `.execute(db);
  }
}
