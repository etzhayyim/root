import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-06T20:00:00Z";
const OWNER_DID = "did:web:malak.gftd.ai";
const ACTOR_ID = "sys.bpmn.seed.malak-referral";

const ENTRY = {
  processVid:
    "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-draft-agency-referral-v1",
  bindingVid:
    "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-draftAgencyReferral-v1",
  bpmnProcessId: "malak_draft_agency_referral",
  nsid: "ai.gftd.apps.malak.draftAgencyReferral",
  sourcePath: "00-contracts/bpmn/ai/gftd/malak/draftAgencyReferral.bpmn",
  writeTableAllowlist: "vertex_malak_agency_referral_draft",
};

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, ENTRY.sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id,
       actor_id, actor_did, org_did)
    SELECT
      ${ENTRY.processVid}, ${OWNER_DID}, ${ENTRY.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${ENTRY.sourcePath}, 'active',
      ${CREATED_AT}, 100, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_ID},
      ${OWNER_DID}, ${OWNER_DID}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${ENTRY.processVid}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
       result_timeout_ms, write_table_allowlist, status, created_at,
       sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)
    SELECT
      ${ENTRY.bindingVid}, ${OWNER_DID}, ${ENTRY.nsid}, ${ENTRY.bpmnProcessId}, 1,
      30000, ${ENTRY.writeTableAllowlist}, 'active', ${CREATED_AT},
      100, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_ID}, ${OWNER_DID}, ${OWNER_DID}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${ENTRY.bindingVid}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${ENTRY.bindingVid}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${ENTRY.processVid}`.execute(db);
}

