import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed BPMN process_def + lexicon binding for kaisya.memberChat.
 *
 * XRPC app.etzhayyim.apps.kaisya.memberChat → kaisya_member_chat BPMN →
 * kaisya.member.chat task → LangGraph kaisya-member-assistant.
 *
 * Note: kaisya_outlook_auth_callback is NOT a Zeebe process — it lives
 * as CF Worker /auth/outlook/callback route. We do NOT seed it here.
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T00:00:00Z";
const ownerDid = "did:web:kaisya.etzhayyim.com";
const actorTag = "sys.bpmn.seed.kaisya";

const PROCESS = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kaisya-member-chat-v1",
  bpmnProcessId: "kaisya_member_chat",
  sourcePath: "00-contracts/bpmn/ai/gftd/kaisya/memberChat.bpmn",
};
const BINDING = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kaisya-member-chat-xrpc-v1",
  nsid: "app.etzhayyim.apps.kaisya.memberChat",
  bpmnProcessId: "kaisya_member_chat",
  resultTimeoutMs: 120_000,
};

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(PROCESS.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${PROCESS.vertexId}, ${ownerDid}, ${PROCESS.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${PROCESS.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId})
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${BINDING.vertexId}, ${ownerDid}, ${BINDING.nsid}, ${BINDING.bpmnProcessId}, 1, CAST(${BINDING.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId}`.execute(db);
}
