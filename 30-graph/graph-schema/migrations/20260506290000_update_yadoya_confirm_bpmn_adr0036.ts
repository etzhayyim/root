import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// yadoya confirmReservation BPMN ADR-0036 fix.
//
// The prior seed (20260428150100) registered confirmReservation.bpmn with
// Task_EmitCurrency / Task_EmitService using generic.pds.dispatch +
// com.atproto.repo.createRecord (T1 PDS path), which violates ADR-0036.
//
// This migration overwrites vertex_bpmn_process_def with the corrected
// BPMN XML that replaces those two tasks with generic.db.insert writing
// directly to vertex_resource_flow_currency / vertex_resource_flow_service
// (T2 Hyperdrive path).  RisingWave PK implicit upsert overwrites the row.
// The F5 watcher in bpmn-dispatcher will re-deploy to Zeebe on next tick.

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);
const repoRoot   = path.resolve(__dirname, "..", "..", "..");

const PROC_VID   = "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/yadoya-confirm-reservation-v1";
const OWNER_DID  = "did:web:yadoya.gftd.ai";
const ACTOR_TAG  = "sys.bpmn.seed.yadoya-confirm";
const REL_PATH   = "00-contracts/bpmn/ai/gftd/yadoya/confirmReservation.bpmn";
const CREATED_AT = "2026-05-06T00:00:00Z";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml  = readFileSync(path.resolve(repoRoot, REL_PATH), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  // PK implicit upsert: same vertex_id overwrites the existing row in RisingWave.
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    ) VALUES (
      ${PROC_VID}, ${OWNER_DID}, ${"yadoya_confirm_reservation"}, 1,
      ${xml}, CAST(${size} AS integer), ${REL_PATH}, ${"active"},
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Re-apply original seed to restore the pre-fix XML.
  const origPath = "00-contracts/bpmn/ai/gftd/yadoya/confirmReservation.bpmn";
  const xml = readFileSync(path.resolve(repoRoot, origPath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    ) VALUES (
      ${PROC_VID}, ${OWNER_DID}, ${"yadoya_confirm_reservation"}, 1,
      ${xml}, CAST(${size} AS integer), ${origPath}, ${"active"},
      ${CREATED_AT}, 1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    )
  `.execute(db);
}
