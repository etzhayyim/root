import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);
const repoRoot   = path.resolve(__dirname, "..", "..", "..");
const ownerDid   = "did:web:bpmn.etzhayyim.com";
const createdAt  = "2026-05-01T13:00:00+09:00";
const actorId    = "sys.bpmn.seed.owl-reasoner";

const BPMN_PATH   = "00-contracts/bpmn/com/etzhayyim/owl/owlReasonerBatch.bpmn";
const PROCESS_ID  = "owl_reasoner_batch";
const PROCESS_VID = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/owl-reasoner-batch-v1";
// Timer-start process: no external NSID binding (self-scheduled R/PT1H).
// Task types (owl.el.classify / owl.dl.classify / owl.benchmark.compare / owl.ql.precompute)
// are registered via pyzeebe register_owl_tasks(worker) in zeebe_worker_main.py.

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml  = readFileSync(path.resolve(repoRoot, BPMN_PATH), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

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
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_VID}`.execute(db);
}
