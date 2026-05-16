import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def + vertex_bpmn_lexicon_binding for Phase 2
// AIF policy dispatch BPMN (ADR-2604291800, ADR-0056).
// F5 watcher deploys to Zeebe within 30s of INSERT.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-07T20:00:00Z";
const OWNER_DID = "did:web:bpmn.gftd.ai";

const DISPATCH_PROCESS_VID =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/rl-policy-dispatch-v1";
const DISPATCH_BINDING_VID =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/rl-policy-dispatch-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/rl/rlPolicyDispatch.bpmn"),
    "utf8",
  );
  const byteSize = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${DISPATCH_PROCESS_VID}, ${OWNER_DID}, 'rl_policy_dispatch', 1,
      ${xml}, CAST(${byteSize} AS integer),
      '00-contracts/bpmn/ai/gftd/rl/rlPolicyDispatch.bpmn',
      'active', ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${DISPATCH_PROCESS_VID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, bpmn_process_id, nsid,
       created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${DISPATCH_BINDING_VID}, ${OWNER_DID}, 'rl_policy_dispatch',
      'ai.gftd.apps.rl.policyDispatch',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.rl'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${DISPATCH_BINDING_VID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${DISPATCH_BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${DISPATCH_PROCESS_VID}`.execute(db);
}
