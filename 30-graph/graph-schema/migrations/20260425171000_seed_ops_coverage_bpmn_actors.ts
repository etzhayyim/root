import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Entry = {
  project: string;
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  ownerDid: string;
  timeoutMs: number;
};

type ProcessSeed = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
  ownerDid: string;
};

type BindingSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  ownerDid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-25T17:10:00Z";
const actorTag = "sys.bpmn.seed.ops-coverage";

const entries: Entry[] = [
  {
    project: "open-logistics-lastmile",
    proc: "dispatchLeg",
    bpmnProcessId: "open_logistics_lastmile_dispatch_leg",
    nsid: "com.etzhayyim.apps.openLogisticsLastmile.dispatchLeg",
    ownerDid: "did:web:open-logistics-lastmile.etzhayyim.com",
    timeoutMs: 30000,
  },
  {
    project: "open-logistics-lastmile",
    proc: "confirmDelivery",
    bpmnProcessId: "open_logistics_lastmile_confirm_delivery",
    nsid: "com.etzhayyim.apps.openLogisticsLastmile.confirmDelivery",
    ownerDid: "did:web:open-logistics-lastmile.etzhayyim.com",
    timeoutMs: 30000,
  },
  {
    project: "open-machinery-maintenance",
    proc: "recordMaintenancePlan",
    bpmnProcessId: "open_machinery_maintenance_record_plan",
    nsid: "com.etzhayyim.apps.openMachineryMaintenance.recordMaintenancePlan",
    ownerDid: "did:web:open-machinery-maintenance.etzhayyim.com",
    timeoutMs: 30000,
  },
  {
    project: "open-machinery-maintenance",
    proc: "flagDowntime",
    bpmnProcessId: "open_machinery_maintenance_flag_downtime",
    nsid: "com.etzhayyim.apps.openMachineryMaintenance.flagDowntime",
    ownerDid: "did:web:open-machinery-maintenance.etzhayyim.com",
    timeoutMs: 30000,
  },
  {
    project: "open-industrial-safety",
    proc: "recordSafetyAssessment",
    bpmnProcessId: "open_industrial_safety_record_safety_assessment",
    nsid: "com.etzhayyim.apps.industrialSafety.recordSafetyAssessment",
    ownerDid: "did:web:open-industrial-safety.etzhayyim.com",
    timeoutMs: 30000,
  },
  {
    project: "open-industrial-safety",
    proc: "flagMajorAccident",
    bpmnProcessId: "open_industrial_safety_flag_major_accident",
    nsid: "com.etzhayyim.apps.industrialSafety.flagMajorAccident",
    ownerDid: "did:web:open-industrial-safety.etzhayyim.com",
    timeoutMs: 30000,
  },
];

const readContract = (relPath: string): string =>
  readFileSync(path.resolve(repoRoot, relPath), "utf8");

const procSlug = (proc: string): string =>
  proc.replace(/([A-Z])/g, "-$1").toLowerCase();

const processSeeds: ProcessSeed[] = entries.map((entry) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${entry.project}-${procSlug(entry.proc)}-v1`,
  bpmnProcessId: entry.bpmnProcessId,
  sourcePath: `00-contracts/bpmn/com/etzhayyim/${entry.project}/${entry.proc}.bpmn`,
  ownerDid: entry.ownerDid,
}));

const bindingSeeds: BindingSeed[] = entries.map((entry) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${entry.project}-${entry.proc}-v1`,
  nsid: entry.nsid,
  bpmnProcessId: entry.bpmnProcessId,
  ownerDid: entry.ownerDid,
  resultTimeoutMs: entry.timeoutMs,
}));

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${seed.vertexId}, ${seed.ownerDid}, ${seed.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${seed.sourcePath}, 'active', ${createdAt}, 1, ${seed.ownerDid}, ${seed.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId})
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: BindingSeed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${seed.vertexId}, ${seed.ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1, CAST(${seed.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${seed.ownerDid}, ${seed.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const seed of processSeeds) await insertProcessDef(db, seed);
  for (const seed of bindingSeeds) await insertBinding(db, seed);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of bindingSeeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
  for (const seed of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
}
