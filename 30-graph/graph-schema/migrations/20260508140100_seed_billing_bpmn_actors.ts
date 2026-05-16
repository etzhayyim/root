import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * billing.gftd.ai BPMN-as-actor seeding (ADR-0056 + ADR-2605080000).
 *
 * 5 BPMN process defs + 1 XRPC binding (setDiscount).  No CF Worker
 * (T2 tier: pymagatama + Zeebe only).  4 timer-start BPMNs are
 * autonomous; 1 XRPC binding is reachable via bpmn-dispatcher
 * `http://dispatcher.gftd.ai:8080/xrpc/ai.gftd.apps.billing.setDiscount`.
 *
 *  Process / NSID                                    Trigger
 *  ----------------------------------------------------------------------
 *  billing_rollup_daily            (none, autonomous)   cron 0 0 1 * * ?
 *  billing_rollup_monthly          (none, autonomous)   cron 0 0 2 1 * ?
 *  billing_detect_overage          (none, autonomous)   R/PT5M
 *  billing_generate_invoice        (none, autonomous)   cron 0 0 3 1 * ?
 *  billing_apply_discount          ai.gftd.apps.billing.setDiscount
 *
 * Read-side lexicons (recordUsageEvent / getUsage / getQuotaStatus /
 * listInvoices / getInvoice / applyCredit / coverage) bind directly to
 * `generic.db.select` / `generic.db.insert` BPMNs from the upstream
 * billing tables and do not need their own dedicated process_def rows
 * here. Dispatcher answers them via a thin SELECT/INSERT BPMN binding
 * which is added in a follow-up migration once the lexicons are
 * promoted from internal to public.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T14:01:00Z";
const ownerDid = "did:web:billing.gftd.ai";
const actorTag = "sys.bpmn.seed.billing";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/billing-rollup-daily-v1",
    bpmnProcessId: "billing_rollup_daily",
    sourcePath: "00-contracts/bpmn/ai/gftd/billing/rollupDaily.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/billing-rollup-monthly-v1",
    bpmnProcessId: "billing_rollup_monthly",
    sourcePath: "00-contracts/bpmn/ai/gftd/billing/rollupMonthly.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/billing-detect-overage-v1",
    bpmnProcessId: "billing_detect_overage",
    sourcePath: "00-contracts/bpmn/ai/gftd/billing/detectOverage.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/billing-generate-invoice-v1",
    bpmnProcessId: "billing_generate_invoice",
    sourcePath: "00-contracts/bpmn/ai/gftd/billing/generateInvoice.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/billing-apply-discount-v1",
    bpmnProcessId: "billing_apply_discount",
    sourcePath: "00-contracts/bpmn/ai/gftd/billing/applyDiscount.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/billing-setDiscount-v1",
    nsid: "ai.gftd.apps.billing.setDiscount",
    bpmnProcessId: "billing_apply_discount", ownerDid, resultTimeoutMs: 30_000 },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: B): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of bindingSeeds) await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  for (const s of processSeeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
