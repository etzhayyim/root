/**
 * ADR-2605080600 Phase 4 — Re-seed ki / saikin / webmk / newsletter BPMNs with fixed XML.
 *
 * Prior seed migrations used WHERE NOT EXISTS guards so they won't re-apply.
 * The original BPMN files had structural errors that caused Zeebe ProcessInvalidError:
 *   - ki: timeCycle R/PT60M → R/PT1H (Zeebe 8.5 rejects non-standard durations)
 *   - saikin: Task_Audit had <incoming>Flow_AfterColony</incoming> but Flow_AfterColony
 *             targets Task_HandoffToKi; corrected to Flow_AfterKi
 *   - webmk: dangling intermediateCatchEvent (no incoming/outgoing) + missing F4_no condition
 *   - newsletter: missing conditionExpression on F4_no exclusive gateway branch
 *
 * Fix: DELETE existing rows + INSERT fresh with corrected XML from disk files.
 * Rows are set to status='active' and deployed_zeebe_key=NULL so the F5 watcher
 * will redeploy them to Zeebe on the next poll cycle.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const OWNER_DID = "did:web:bpmn.gftd.ai";
const CREATED_AT = "2026-05-08T09:50:00Z";
const ACTOR_TAG = "sys.bpmn.reseed.phase4-fix";

interface Entry {
  vertexId: string;
  processId: string;
  bpmnPath: string;
  version: number;
}

const ENTRIES: Entry[] = [
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ki-vascular-synthesis-cycle-v1",
    processId: "ki_vascular_synthesis_cycle",
    bpmnPath: "00-contracts/bpmn/ai/gftd/ki/vascular-synthesis-cycle.bpmn",
    version: 2,
  },
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/saikin-horizontal-transfer-cycle-v1",
    processId: "saikin_horizontal_transfer_cycle",
    bpmnPath: "00-contracts/bpmn/ai/gftd/saikin/horizontal-transfer-cycle.bpmn",
    version: 2,
  },
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webmk-createProposal-v1",
    processId: "webmk_create_proposal",
    bpmnPath: "00-contracts/bpmn/ai/gftd/webmk/createProposal.bpmn",
    version: 2,
  },
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/newsletter-weeklySend-v1",
    processId: "newsletter_weekly_send",
    bpmnPath: "00-contracts/bpmn/ai/gftd/newsletter/weeklySend.bpmn",
    version: 2,
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    const xml = readFileSync(path.resolve(repoRoot, e.bpmnPath), "utf-8");
    const byteSize = Buffer.byteLength(xml, "utf-8");

    // Delete the existing row (old XML) so we can re-insert with fixed XML.
    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vertexId}
    `.execute(db);

    // Insert fresh with fixed XML and status='active'.
    // deployed_zeebe_key left NULL so the F5 watcher redeploys on the next poll.
    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      VALUES (
        ${e.vertexId}, ${OWNER_DID}, ${e.processId}, ${e.version},
        ${xml}, CAST(${byteSize} AS integer),
        ${e.bpmnPath}, 'active', ${CREATED_AT},
        1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vertexId}
    `.execute(db);
  }
}
