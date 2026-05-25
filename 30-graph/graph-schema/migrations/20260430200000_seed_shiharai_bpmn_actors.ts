import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:shiharai.etzhayyim.com";
const createdAt = "2026-04-30T20:00:00+09:00";
const actorId = "sys.bpmn.seed.shiharai";

const seeds: Seed[] = [
  { slug: "extract-bill", op: "extractBill", processId: "shiharai_extract_bill", timeoutMs: 30000, writeTableAllowlist: "vertex_shiharai_bill" },
  { slug: "list-pending-bills", op: "listPendingBills", processId: "shiharai_list_pending_bills", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "prepare-payment", op: "preparePayment", processId: "shiharai_prepare_payment", timeoutMs: 120000, writeTableAllowlist: "vertex_shiharai_job" },
  { slug: "confirm-payment", op: "confirmPayment", processId: "shiharai_confirm_payment", timeoutMs: 120000, writeTableAllowlist: "vertex_shiharai_payment" },
  { slug: "register-recurring", op: "registerRecurring", processId: "shiharai_register_recurring", timeoutMs: 120000, writeTableAllowlist: "vertex_shiharai_recurring" },
  { slug: "list-recurring", op: "listRecurring", processId: "shiharai_list_recurring", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "get-job-status", op: "getJobStatus", processId: "shiharai_get_job_status", timeoutMs: 30000, writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/shiharai/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shiharai-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/shiharai-${s.op}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${`app.etzhayyim.apps.shiharai.${s.op}`}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
