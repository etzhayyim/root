import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const CREATED_AT = "2026-05-07T13:15:00Z";
const ACTOR_ID = "sys.bpmn.seed.agent-policy-adaptation";
const SOURCE_PATH = "00-contracts/bpmn/com/etzhayyim/agent/policyAdaptation.bpmn";
const PROCESS_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/agent-policy-adaptation-v1";
const BINDING_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/agent-policy-adaptation-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, SOURCE_PATH), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id,
       actor_id, actor_did, org_did)
    SELECT
      ${PROCESS_VERTEX_ID}, ${OWNER_DID}, 'agent_policy_adaptation', 1,
      ${xml}, CAST(${size} AS integer), ${SOURCE_PATH}, 'active',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_ID},
      ${OWNER_DID}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
       result_timeout_ms, write_table_allowlist, status, created_at,
       sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)
    SELECT
      ${BINDING_VERTEX_ID}, ${OWNER_DID}, 'com.etzhayyim.apps.agent.adaptPolicy',
      'agent_policy_adaptation', 1, 120000,
      'vertex_agent_policy_adaptation_proposal,vertex_agent_prior_preference',
      'active', ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_ID},
      ${OWNER_DID}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}
  `.execute(db);
  await sql`
    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
  `.execute(db);
}
