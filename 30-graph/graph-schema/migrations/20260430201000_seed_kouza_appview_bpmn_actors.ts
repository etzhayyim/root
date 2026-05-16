import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:kouza.gftd.ai";
const createdAt = "2026-04-30T20:10:00+09:00";
const actorId = "sys.bpmn.seed.kouza-appview";

const seeds: Seed[] = [
  { slug: "register-connection", op: "registerConnection", processId: "kouza_register_connection", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kouza_institution_connection" },
  { slug: "sync-connection", op: "syncConnection", processId: "kouza_sync_connection", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kouza_sync_run,vertex_atrecord_kouza_institution_connection" },
  { slug: "create-financial-account", op: "createFinancialAccount", processId: "kouza_create_financial_account", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kouza_financial_account" },
  { slug: "import-statement", op: "importStatement", processId: "kouza_import_statement", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kouza_external_transaction,vertex_atrecord_kouza_sync_run,vertex_atrecord_kouza_institution_connection,vertex_atrecord_kaikei_bank_transaction" },
  { slug: "import-statement-csv", op: "importStatementCsv", processId: "kouza_import_statement_csv", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kouza_external_transaction,vertex_atrecord_kouza_sync_run,vertex_atrecord_kouza_institution_connection,vertex_atrecord_kaikei_bank_transaction" },
  { slug: "attach-document", op: "attachDocument", processId: "kouza_attach_document", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_kouza_account_document" },
  { slug: "map-kaikei-account", op: "mapKaikeiAccount", processId: "kouza_map_kaikei_account", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_kouza_financial_account" },
  { slug: "list-accounts", op: "listAccounts", processId: "kouza_list_accounts", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-transactions", op: "listTransactions", processId: "kouza_list_transactions", timeoutMs: 30000, writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/kouza/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kouza-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/kouza-${s.op}-v1`;

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
        ${bindingVertexId(s)}, ${ownerDid}, ${`ai.gftd.apps.kouza.${s.op}`}, ${s.processId}, 1,
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
