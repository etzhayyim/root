import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T22:01:00Z";
const ownerDid = "did:web:telecom.etzhayyim.com";
const actorTag = "sys.bpmn.seed.telecom-tmf";
// bpmn-coverage gate marker: project: "telecom"
const project = "telecom";

const seeds: Seed[] = [
  { proc: "publishProductOffering", bpmnProcessId: "telecom_publish_product_offering",
    nsid: "com.etzhayyim.apps.telecom.publishProductOffering", resultTimeoutMs: 30000 },
  { proc: "submitProductOrder", bpmnProcessId: "telecom_submit_product_order",
    nsid: "com.etzhayyim.apps.telecom.submitProductOrder", resultTimeoutMs: 30000 },
  { proc: "recordProductInventoryItem", bpmnProcessId: "telecom_record_product_inventory_item",
    nsid: "com.etzhayyim.apps.telecom.recordProductInventoryItem", resultTimeoutMs: 30000 },
  { proc: "submitServiceOrder", bpmnProcessId: "telecom_submit_service_order",
    nsid: "com.etzhayyim.apps.telecom.submitServiceOrder", resultTimeoutMs: 30000 },
  { proc: "activateServiceInstance", bpmnProcessId: "telecom_activate_service_instance",
    nsid: "com.etzhayyim.apps.telecom.activateServiceInstance", resultTimeoutMs: 30000 },
  { proc: "recordServiceInventoryItem", bpmnProcessId: "telecom_record_service_inventory_item",
    nsid: "com.etzhayyim.apps.telecom.recordServiceInventoryItem", resultTimeoutMs: 30000 },
  { proc: "registerCustomerAccount", bpmnProcessId: "telecom_register_customer_account",
    nsid: "com.etzhayyim.apps.telecom.registerCustomerAccount", resultTimeoutMs: 30000 },
  { proc: "issueCustomerBill", bpmnProcessId: "telecom_issue_customer_bill",
    nsid: "com.etzhayyim.apps.telecom.issueCustomerBill", resultTimeoutMs: 60000 },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/${project}/${s.proc}.bpmn`;
const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${project}-${slug(s.proc)}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${project}-${s.proc}-v1`;

async function insertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const rel = sourcePath(s);
  const xml = readContract(rel);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${rel}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
      CAST(${s.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await insertProcessDef(db, s);
    await insertBinding(db, s);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
