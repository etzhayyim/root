import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  actor: string;
  op: string;
  slug: string;
  processId: string;
  timeoutMs: number;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:bpmn.etzhayyim.com";
const createdAt = "2026-05-08T16:10:00+09:00";
const actorId = "sys.bpmn.seed.moneyforward-remaining";

const seeds: Seed[] = [
  { actor: "seikyu", op: "issueInvoice", slug: "issue-invoice", processId: "seikyu_issue_invoice", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_seikyu_invoice,vertex_atrecord_seikyu_recurring_schedule" },
  { actor: "seikyu", op: "sendInvoice", slug: "send-invoice", processId: "seikyu_send_invoice", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_seikyu_invoice" },
  { actor: "seikyu", op: "voidInvoice", slug: "void-invoice", processId: "seikyu_void_invoice", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_seikyu_invoice" },
  { actor: "seikyu", op: "recordPaymentReceived", slug: "record-payment-received", processId: "seikyu_record_payment_received", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_seikyu_payment_received,vertex_atrecord_seikyu_invoice" },
  { actor: "seikyu", op: "listInvoices", slug: "list-invoices", processId: "seikyu_list_invoices", timeoutMs: 30000, writeTableAllowlist: "" },
  { actor: "seikyu", op: "getInvoiceAging", slug: "get-invoice-aging", processId: "seikyu_get_invoice_aging", timeoutMs: 30000, writeTableAllowlist: "" },
  { actor: "seikyu", op: "submitPeppol", slug: "submit-peppol", processId: "seikyu_submit_peppol", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_seikyu_invoice" },
  { actor: "keiyaku", op: "draftAgreement", slug: "draft-agreement", processId: "keiyaku_draft_agreement", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_keiyaku_agreement,vertex_atrecord_seikyu_recurring_schedule" },
  { actor: "keiyaku", op: "submitForSignature", slug: "submit-for-signature", processId: "keiyaku_submit_for_signature", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_keiyaku_agreement,vertex_atrecord_keiyaku_signing_flow" },
  { actor: "keiyaku", op: "signAgreement", slug: "sign-agreement", processId: "keiyaku_sign_agreement", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_keiyaku_agreement,vertex_atrecord_keiyaku_signing_flow" },
  { actor: "keiyaku", op: "voidAgreement", slug: "void-agreement", processId: "keiyaku_void_agreement", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_keiyaku_agreement" },
  { actor: "keiyaku", op: "listActiveAgreements", slug: "list-active-agreements", processId: "keiyaku_list_active_agreements", timeoutMs: 30000, writeTableAllowlist: "" },
  { actor: "kousuu", op: "createProject", slug: "create-project", processId: "kousuu_create_project", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kousuu_project" },
  { actor: "kousuu", op: "recordTimeEntry", slug: "record-time-entry", processId: "kousuu_record_time_entry", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kousuu_time_entry" },
  { actor: "kousuu", op: "approveTimeEntry", slug: "approve-time-entry", processId: "kousuu_approve_time_entry", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_kousuu_time_entry" },
  { actor: "kousuu", op: "getProjectBurn", slug: "get-project-burn", processId: "kousuu_get_project_burn", timeoutMs: 30000, writeTableAllowlist: "" },
  { actor: "keihi", op: "submitExpense", slug: "submit-expense", processId: "keihi_submit_expense", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_keihi_expense" },
  { actor: "keihi", op: "approveExpense", slug: "approve-expense", processId: "keihi_approve_expense", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_keihi_expense,vertex_atrecord_kaikei_journal_entry" },
  { actor: "jinji", op: "upsertEmployee", slug: "upsert-employee", processId: "jinji_upsert_employee", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_jinji_employee" },
  { actor: "jinji", op: "recordAttendance", slug: "record-attendance", processId: "jinji_record_attendance", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_jinji_attendance" },
  { actor: "jinji", op: "completePayrollRun", slug: "complete-payroll-run", processId: "jinji_complete_payroll_run", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_jinji_payroll_run,vertex_atrecord_kaikei_journal_entry" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/${s.actor}/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/${s.actor}-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${s.actor}-${s.op}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  const existingProcesses = new Set(
    (await sql<{ vertex_id: string }>`
      SELECT vertex_id FROM vertex_bpmn_process_def
      WHERE vertex_id IN (${sql.join(seeds.map(processVertexId))})
    `.execute(db)).rows.map((r) => r.vertex_id),
  );
  const existingBindings = new Set(
    (await sql<{ vertex_id: string }>`
      SELECT vertex_id FROM vertex_bpmn_lexicon_binding
      WHERE vertex_id IN (${sql.join(seeds.map(bindingVertexId))})
    `.execute(db)).rows.map((r) => r.vertex_id),
  );

  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    const actorDid = `did:web:${s.actor}.etzhayyim.com`;

    if (!existingProcesses.has(processVertexId(s))) {
      await sql`
        INSERT INTO vertex_bpmn_process_def (
          vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
          source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
          actor_did, org_did
        )
        VALUES (
          ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
          ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
          ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
          ${actorDid}, 'anon'
        )
      `.execute(db);
    }

    if (!existingBindings.has(bindingVertexId(s))) {
      await sql`
        INSERT INTO vertex_bpmn_lexicon_binding (
          vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
          result_timeout_ms, write_table_allowlist, status, created_at,
          sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
        )
        VALUES (
          ${bindingVertexId(s)}, ${ownerDid}, ${`ai.gftd.apps.${s.actor}.${s.op}`}, ${s.processId}, 1,
          CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
          100, ${ownerDid}, ${ownerDid}, ${actorId}, ${actorDid}, 'anon'
        )
      `.execute(db);
    }
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
