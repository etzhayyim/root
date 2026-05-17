import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const SEED_CREATED_AT = "2026-05-09T00:00:00Z";
const SEED_OWNER_DID = "did:web:lawfirm.etzhayyim.com";
const SEED_ACTOR_TAG = "sys.bpmn.seed.lawfirm";

/**
 * Re-seed: lawfirm_sales_cadence_tick BPMN v2.
 *
 * v1 (seeded in 20260509010000) only scanned stale leads + drafted re-outreach.
 * v2 prepends Task_DispatchDueMails (lawfirm.cadence.dispatchDueMails) so the
 * R/PT24H tick also auto-fires Tier-2 warm-intro mails as drafts when their
 * next_action_at falls due.
 *
 * Strategy: insert a NEW process_def row with version=2 + suffix vertex_id, set
 * status='active' on v2 + 'superseded' on v1. F5 watcher routes by latest active
 * version per bpmn_process_id.
 *
 * Down() flips v2 → 'inactive', restores v1 → 'active'. Idempotent.
 */
const PROCESS_V2 = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/lawfirm-sales-cadence-tick-v2",
  bpmnProcessId: "lawfirm_sales_cadence_tick",
  sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/salesCadenceTick.bpmn",
  version: 2,
};
const PROCESS_V1_VID = "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/lawfirm-sales-cadence-tick-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(PROCESS_V2.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord,
       org_id, user_id, actor_id)
    SELECT
      ${PROCESS_V2.vertexId}, ${SEED_OWNER_DID}, ${PROCESS_V2.bpmnProcessId},
      CAST(${PROCESS_V2.version} AS integer),
      ${xml}, CAST(${size} AS integer), ${PROCESS_V2.sourcePath}, 'active',
      ${SEED_CREATED_AT}, 1, ${SEED_OWNER_DID}, ${SEED_OWNER_DID}, ${SEED_ACTOR_TAG}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_V2.vertexId})
  `.execute(db);

  // Mark v1 superseded (only if currently active)
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'superseded'
    WHERE vertex_id = ${PROCESS_V1_VID}
      AND status = 'active'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'active'
    WHERE vertex_id = ${PROCESS_V1_VID}
      AND status = 'superseded'
  `.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_V2.vertexId}`.execute(db);
}
