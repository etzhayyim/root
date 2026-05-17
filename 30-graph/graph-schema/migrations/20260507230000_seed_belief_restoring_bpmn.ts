import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for Well-Becoming γ restoring force BPMN (ADR-0098 E).
// Registers wellbecoming_belief_restoring_capture process + lexicon binding so the
// F5 watcher deploys it to Zeebe and bpmn-dispatcher can trigger it via XRPC.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-07T23:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";

const PROCESS_VID =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/wellbecoming-belief-restoring-capture-v1";
const BINDING_VID =
  "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/wellbecoming-belief-restoring-capture-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(
      repoRoot,
      "00-contracts/bpmn/ai/gftd/wellbecoming/beliefRestoringCapture.bpmn",
    ),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${PROCESS_VID}, ${OWNER_DID},
      'wellbecoming_belief_restoring_capture', 1,
      ${xml}, CAST(${size} AS integer),
      '00-contracts/bpmn/ai/gftd/wellbecoming/beliefRestoringCapture.bpmn',
      'active', ${CREATED_AT}, 1,
      ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.wellbecoming'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, bpmn_process_id, nsid,
       created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${BINDING_VID}, ${OWNER_DID},
      'wellbecoming_belief_restoring_capture',
      'ai.gftd.apps.wellbecoming.beliefRestoringCapture',
      ${CREATED_AT}, 1,
      ${OWNER_DID}, ${OWNER_DID}, 'sys.bpmn.seed.wellbecoming'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}`.execute(db);
}
