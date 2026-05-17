import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604281400 Phase 3 — seed contributionSourceRegister BPMN actor.
// One process_def + one lexicon_binding (XRPC-triggered, no timer).
// NSID: ai.gftd.authz.registerContributionSource
// Zeebe task: contribution.registerSource (off-chain DB write only)

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-04-29T12:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const BPMN_PROCESS_ID = "contribution_source_register";
const NSID = "ai.gftd.authz.registerContributionSource";
const SOURCE_PATH = "00-contracts/bpmn/ai/gftd/contribution/contributionSourceRegister.bpmn";

const PROCESS_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/contribution-source-register-v1";
const BINDING_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/contribution-registerSource-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, SOURCE_PATH), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${PROCESS_VERTEX_ID}, ${OWNER_DID}, ${BPMN_PROCESS_ID}, 1,
      ${xml}, CAST(${size} AS integer), ${SOURCE_PATH}, 'active',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.contribution'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${BINDING_VERTEX_ID}, ${OWNER_DID}, ${NSID}, ${BPMN_PROCESS_ID}, 1,
      CAST(30000 AS integer), 'active',
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.contribution'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VERTEX_ID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}`.execute(db);
}
