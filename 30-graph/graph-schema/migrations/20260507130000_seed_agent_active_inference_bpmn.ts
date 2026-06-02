import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const CREATED_AT = "2026-05-07T13:00:00Z";
const ACTOR_ID = "sys.bpmn.seed.agent-active-inference";

const ENTRIES = [
  {
    processVid:
      "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/agent-active-inference-tick-v1",
    bindingVid:
      "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/agent-active-inference-tick-v1",
    bpmnProcessId: "agent_active_inference_tick",
    nsid: "com.etzhayyim.apps.agent.activeInferenceTick",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/agent/activeInferenceTick.bpmn",
    writeTableAllowlist: "vertex_agent_active_inference_tick",
  },
  {
    processVid:
      "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/agent-homeostasis-watch-v1",
    bindingVid:
      "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/agent-homeostasis-watch-v1",
    bpmnProcessId: "agent_homeostasis_watch",
    nsid: "com.etzhayyim.apps.agent.recordHomeostasis",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/agent/homeostasisWatch.bpmn",
    writeTableAllowlist: "vertex_agent_homeostasis_snapshot",
  },
  {
    processVid:
      "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/agent-realworld-effect-dispatch-v1",
    bindingVid:
      "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/agent-realworld-effect-dispatch-v1",
    bpmnProcessId: "agent_realworld_effect_dispatch",
    nsid: "com.etzhayyim.apps.agent.classifyRealWorldEffect",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/agent/realWorldEffectDispatch.bpmn",
    writeTableAllowlist: "vertex_agent_realworld_effect",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const entry of ENTRIES) {
    const xml = readFileSync(path.resolve(repoRoot, entry.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");

    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord, org_id, user_id,
         actor_id, actor_did, org_did)
      SELECT
        ${entry.processVid}, ${OWNER_DID}, ${entry.bpmnProcessId}, 1,
        ${xml}, CAST(${size} AS integer), ${entry.sourcePath}, 'active',
        ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_ID},
        ${OWNER_DID}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${entry.processVid}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
         result_timeout_ms, write_table_allowlist, status, created_at,
         sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)
      SELECT
        ${entry.bindingVid}, ${OWNER_DID}, ${entry.nsid}, ${entry.bpmnProcessId}, 1,
        120000, ${entry.writeTableAllowlist}, 'active', ${CREATED_AT},
        1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_ID}, ${OWNER_DID}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${entry.bindingVid}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const entry of [...ENTRIES].reverse()) {
    await sql`
      DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${entry.bindingVid}
    `.execute(db);
    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${entry.processVid}
    `.execute(db);
  }
}
