import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed BPMN process_def + lexicon binding for lawfirm.engagementClose.
 *
 * End-to-end engagement close pipeline:
 *   PwC clearance → Engagement Letter draft (LangGraph) →
 *   DocuSign envelope → Stripe Checkout link → audit
 *
 * Also re-binds the existing lawfirm_payment_intake process to the
 * mailReplyWebhook nsid (no separate process; reuses payment-intake).
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T00:00:00Z";
const ownerDid = "did:web:lawfirm.etzhayyim.com";
const actorTag = "sys.bpmn.seed.lawfirm";

const PROCESS = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/lawfirm-engagement-close-v1",
  bpmnProcessId: "lawfirm_engagement_close",
  sourcePath: "00-contracts/bpmn/com/etzhayyim/lawfirm/engagementClose.bpmn",
};
const BINDINGS = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/lawfirm-engagement-close-xrpc-v1",
    nsid: "com.etzhayyim.apps.lawfirm.engagementClose",
    bpmnProcessId: "lawfirm_engagement_close",
    resultTimeoutMs: 600_000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/lawfirm-mail-reply-webhook-xrpc-v1",
    nsid: "com.etzhayyim.apps.lawfirm.mailReplyWebhook",
    bpmnProcessId: "lawfirm_payment_intake",
    resultTimeoutMs: 60_000,
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(PROCESS.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${PROCESS.vertexId}, ${ownerDid}, ${PROCESS.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${PROCESS.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId})
  `.execute(db);

  for (const b of BINDINGS) {
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${b.vertexId}, ${ownerDid}, ${b.nsid}, ${b.bpmnProcessId}, 1, CAST(${b.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const b of BINDINGS)
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId}`.execute(db);
}
