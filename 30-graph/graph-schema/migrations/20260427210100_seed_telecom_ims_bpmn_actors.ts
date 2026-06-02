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
const createdAt = "2026-04-27T21:01:00Z";
const ownerDid = "did:web:telecom.etzhayyim.com";
const actorTag = "sys.bpmn.seed.telecom-ims";
// bpmn-coverage gate marker: project: "telecom"
const project = "telecom";

const seeds: Seed[] = [
  { proc: "registerImsSubscription", bpmnProcessId: "telecom_register_ims_subscription",
    nsid: "com.etzhayyim.apps.telecom.registerImsSubscription", resultTimeoutMs: 30000 },
  { proc: "registerSipEndpoint", bpmnProcessId: "telecom_register_sip_endpoint",
    nsid: "com.etzhayyim.apps.telecom.registerSipEndpoint", resultTimeoutMs: 15000 },
  { proc: "establishVoiceCall", bpmnProcessId: "telecom_establish_voice_call",
    nsid: "com.etzhayyim.apps.telecom.establishVoiceCall", resultTimeoutMs: 30000 },
  { proc: "terminateVoiceCall", bpmnProcessId: "telecom_terminate_voice_call",
    nsid: "com.etzhayyim.apps.telecom.terminateVoiceCall", resultTimeoutMs: 15000 },
  { proc: "applySupplementaryService", bpmnProcessId: "telecom_apply_supplementary_service",
    nsid: "com.etzhayyim.apps.telecom.applySupplementaryService", resultTimeoutMs: 15000 },
  { proc: "routeEmergencyCall", bpmnProcessId: "telecom_route_emergency_call",
    nsid: "com.etzhayyim.apps.telecom.routeEmergencyCall", resultTimeoutMs: 15000 },
  { proc: "bridgeVoiceToInterconnect", bpmnProcessId: "telecom_bridge_voice_to_interconnect",
    nsid: "com.etzhayyim.apps.telecom.bridgeVoiceToInterconnect", resultTimeoutMs: 15000 },
  { proc: "emitImsBillingEvent", bpmnProcessId: "telecom_emit_ims_billing_event",
    nsid: "com.etzhayyim.apps.telecom.emitImsBillingEvent", resultTimeoutMs: 15000 },
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
  for (const s of seeds) await insertProcessDef(db, s);
  for (const s of seeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
  }
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
