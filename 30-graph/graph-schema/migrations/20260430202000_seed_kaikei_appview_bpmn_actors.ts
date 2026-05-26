import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:kaikei.etzhayyim.com";
const createdAt = "2026-04-30T20:20:00+09:00";
const actorId = "sys.bpmn.seed.kaikei-appview";

const seeds: Seed[] = [
  { slug: "get-trial-balance", op: "getTrialBalance", processId: "kaikei_get_trial_balance", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-journal-entries", op: "listJournalEntries", processId: "kaikei_list_journal_entries", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-accounts", op: "listAccounts", processId: "kaikei_list_accounts", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "get-monthly-summary", op: "getMonthlySummary", processId: "kaikei_get_monthly_summary", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "record-pf-payable", op: "recordPfPayable", processId: "kaikei_record_pf_payable", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kaikei_journal_entry" },
  { slug: "record-esi-payable", op: "recordEsiPayable", processId: "kaikei_record_esi_payable", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kaikei_journal_entry" },
  { slug: "record-gst-payable", op: "recordGstPayable", processId: "kaikei_record_gst_payable", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kaikei_journal_entry" },
  { slug: "record-advance-tax", op: "recordAdvanceTax", processId: "kaikei_record_advance_tax", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kaikei_journal_entry" },
  { slug: "recompute-withholding", op: "recomputeWithholding", processId: "kaikei_recompute_withholding", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kaikei_journal_entry" },
  { slug: "map-account", op: "mapAccount", processId: "kaikei_map_account", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kaikei_account" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/kaikei/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kaikei-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kaikei-${s.op}-v1`;

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
        ${bindingVertexId(s)}, ${ownerDid}, ${`app.etzhayyim.apps.kaikei.${s.op}`}, ${s.processId}, 1,
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
