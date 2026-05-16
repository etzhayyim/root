import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604261717 Phase 4: register claim_auto_challenge timer-start BPMN
// (R/PT1H unchallenged sweep) so the F5 watcher deploys it to Zeebe.
// BPMN runs claim.unchallenged.sweep on the Python claim-consumer actor, which
// delegates to authz /internal/claim-unchallenged-sweep for on-chain
// claimUnchallenged() submission and emits a witness-alarm OCEL audit event.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const createdAt = "2026-04-28T19:00:00Z";

const PROCESS_VERTEX_ID =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/claim-auto-challenge-v1";
const BINDING_VERTEX_ID =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/claim-unchallengedSweep-v1";
const OWNER_DID = "did:web:claim-consumer.gftd.ai";
const BPMN_PROCESS_ID = "claim_auto_challenge";
const SOURCE_PATH = "00-contracts/bpmn/ai/gftd/claim/claimAutoChallenge.bpmn";
const NSID = "ai.gftd.apps.claim.unchallengedSweep";
const RESULT_TIMEOUT_MS = 120_000;

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(SOURCE_PATH);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id,
      owner_did,
      bpmn_process_id,
      version,
      xml,
      xml_byte_size,
      source_path,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${PROCESS_VERTEX_ID},
      ${OWNER_DID},
      ${BPMN_PROCESS_ID},
      1,
      ${xml},
      CAST(${xmlByteSize} AS integer),
      ${SOURCE_PATH},
      'active',
      ${createdAt},
      1,
      ${OWNER_DID},
      ${OWNER_DID},
      'sys.bpmn.seed.claim_auto_challenge'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VERTEX_ID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id,
      owner_did,
      nsid,
      bpmn_process_id,
      bpmn_version,
      result_timeout_ms,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${BINDING_VERTEX_ID},
      ${OWNER_DID},
      ${NSID},
      ${BPMN_PROCESS_ID},
      1,
      CAST(${RESULT_TIMEOUT_MS} AS integer),
      'active',
      ${createdAt},
      1,
      ${OWNER_DID},
      ${OWNER_DID},
      'sys.bpmn.seed.claim_auto_challenge'
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
