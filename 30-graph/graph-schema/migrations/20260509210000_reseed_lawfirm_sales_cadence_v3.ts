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
 * Re-seed: lawfirm_sales_cadence_tick BPMN v3.
 *
 * v1 (20260509010000) only scanned stale leads.
 * v2 (20260509200000) prepended Task_DispatchDueMails for T+0 warm-intro auto-fire.
 * v3 (this) inserts Task_DispatchFollowUps between dispatch and scan-stale,
 *    so the daily R/PT24H tick exercises all 3 cadence phases:
 *      T+0 warm-intro  → lawfirm.cadence.dispatchDueMails
 *      T+5d follow-up   → lawfirm.cadence.dispatchFollowUps (step 1)
 *      T+12d soft-release → lawfirm.cadence.dispatchFollowUps (step 2, sets stage='lost')
 *      stale-scan + re-outreach drafting (legacy, kept)
 *
 * Strategy: insert NEW process_def at version=3, set status='superseded' on v2.
 * F5 watcher routes by latest active version per bpmn_process_id.
 *
 * Down() restores v2 → 'active', flips v3 → 'inactive' + delete v3 row.
 */
const PROCESS_V3 = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/lawfirm-sales-cadence-tick-v3",
  bpmnProcessId: "lawfirm_sales_cadence_tick",
  sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/salesCadenceTick.bpmn",
  version: 3,
};
const PROCESS_V2_VID = "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/lawfirm-sales-cadence-tick-v2";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(PROCESS_V3.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord,
       org_id, user_id, actor_id)
    SELECT
      ${PROCESS_V3.vertexId}, ${SEED_OWNER_DID}, ${PROCESS_V3.bpmnProcessId},
      CAST(${PROCESS_V3.version} AS integer),
      ${xml}, CAST(${size} AS integer), ${PROCESS_V3.sourcePath}, 'active',
      ${SEED_CREATED_AT}, 1, ${SEED_OWNER_DID}, ${SEED_OWNER_DID}, ${SEED_ACTOR_TAG}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_V3.vertexId})
  `.execute(db);

  // Mark v2 superseded
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'superseded'
    WHERE vertex_id = ${PROCESS_V2_VID}
      AND status = 'active'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'active'
    WHERE vertex_id = ${PROCESS_V2_VID}
      AND status = 'superseded'
  `.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS_V3.vertexId}`.execute(db);
}
