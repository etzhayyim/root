import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seeds vertex_bpmn_process_def + vertex_bpmn_lexicon_binding for
// training.startExport (ADR-0056 BPMN-as-actor pattern).
//
// F5 watcher picks up the process_def row and deploys trainingExport.bpmn
// to Zeebe within 30s. bpmn-dispatcher then routes
//   POST /xrpc/com.etzhayyim.apps.training.startExport
// to a new Zeebe process instance.
//
// Applied via: psql (ADR-2604241342 out-of-band pattern)

const __filename  = fileURLToPath(import.meta.url);
const __dirname   = path.dirname(__filename);
const repoRoot    = path.resolve(__dirname, "..", "..", "..");
const ownerDid    = "did:web:bpmn.etzhayyim.com";
const createdAt   = "2026-05-02T13:00:00+09:00";
const actorId     = "sys.bpmn.seed.training-export";

const BPMN_PATH   = "00-contracts/bpmn/com/etzhayyim/training/trainingExport.bpmn";
const PROCESS_ID  = "training_export";
const PROCESS_VID = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/training-export-v1";
const NSID        = "com.etzhayyim.apps.training.startExport";
const BINDING_VID = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/training-export-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml  = readFileSync(path.resolve(repoRoot, BPMN_PATH), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  // Process definition — F5 watcher deploys to Zeebe within 30s of insert.
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord,
      org_id, user_id, actor_id, actor_did, org_did
    )
    SELECT
      ${PROCESS_VID}, ${ownerDid}, ${PROCESS_ID}, 1,
      ${xml}, CAST(${size} AS integer), ${BPMN_PATH}, 'active',
      ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
      ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}
    )
  `.execute(db);

  // Lexicon binding — bpmn-dispatcher routes NSID → Zeebe process instance.
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id,
      status, created_at, sensitivity_ord,
      org_id, user_id, actor_id, actor_did, org_did
    )
    SELECT
      ${BINDING_VID}, ${ownerDid}, ${NSID}, ${PROCESS_ID},
      'active', ${createdAt}, 100,
      ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING_VID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${PROCESS_VID}`.execute(db);
}
