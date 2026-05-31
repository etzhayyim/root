import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const CREATED_AT = "2026-05-07T13:12:00Z";
const ACTOR_ID = "sys.bpmn.seed.agent-autonomous-dispatch";

const ENTRY = {
  processVid:
    "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/agent-realworld-autonomous-dispatch-v1",
  bindingVid:
    "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/agent-realworld-autonomous-dispatch-v1",
  bpmnProcessId: "agent_realworld_autonomous_dispatch",
  nsid: "app.etzhayyim.apps.agent.planRealWorldDispatch",
  sourcePath: "00-contracts/bpmn/ai/gftd/agent/realWorldAutonomousDispatch.bpmn",
  writeTableAllowlist:
    "vertex_agent_realworld_effect,vertex_agent_observation,vertex_agent_dispatch_ledger",
};

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, ENTRY.sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id,
       actor_id, actor_did, org_did)
    SELECT
      ${ENTRY.processVid}, ${OWNER_DID}, ${ENTRY.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${ENTRY.sourcePath}, 'active',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_ID},
      ${OWNER_DID}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${ENTRY.processVid}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
       result_timeout_ms, write_table_allowlist, status, created_at,
       sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)
    SELECT
      ${ENTRY.bindingVid}, ${OWNER_DID}, ${ENTRY.nsid}, ${ENTRY.bpmnProcessId}, 1,
      120000, ${ENTRY.writeTableAllowlist}, 'active', ${CREATED_AT},
      1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_ID}, ${OWNER_DID}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${ENTRY.bindingVid}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${ENTRY.bindingVid}
  `.execute(db);
  await sql`
    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${ENTRY.processVid}
  `.execute(db);
}
