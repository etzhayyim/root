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
const createdAt = "2026-04-28T16:01:00Z";
const ownerDid = "did:web:telecom.etzhayyim.com";
const actorTag = "sys.bpmn.seed.telecom-ntn";
// bpmn-coverage gate marker: project: "telecom"
const project = "telecom";

const seeds: Seed[] = [
  { proc: "registerSatellite", bpmnProcessId: "telecom_register_satellite",
    nsid: "com.etzhayyim.apps.telecom.registerSatellite", resultTimeoutMs: 30000 },
  { proc: "registerEarthStation", bpmnProcessId: "telecom_register_earth_station",
    nsid: "com.etzhayyim.apps.telecom.registerEarthStation", resultTimeoutMs: 30000 },
  { proc: "provisionNtnCell", bpmnProcessId: "telecom_provision_ntn_cell",
    nsid: "com.etzhayyim.apps.telecom.provisionNtnCell", resultTimeoutMs: 30000 },
  { proc: "recordEphemeris", bpmnProcessId: "telecom_record_ephemeris",
    nsid: "com.etzhayyim.apps.telecom.recordEphemeris", resultTimeoutMs: 15000 },
  { proc: "recordNtnHandover", bpmnProcessId: "telecom_record_ntn_handover",
    nsid: "com.etzhayyim.apps.telecom.recordNtnHandover", resultTimeoutMs: 15000 },
  { proc: "provisionInterSatelliteLink", bpmnProcessId: "telecom_provision_inter_satellite_link",
    nsid: "com.etzhayyim.apps.telecom.provisionInterSatelliteLink", resultTimeoutMs: 30000 },
  { proc: "recordEarthStationContact", bpmnProcessId: "telecom_record_earth_station_contact",
    nsid: "com.etzhayyim.apps.telecom.recordEarthStationContact", resultTimeoutMs: 15000 },
  { proc: "registerNtnRoamingPartner", bpmnProcessId: "telecom_register_ntn_roaming_partner",
    nsid: "com.etzhayyim.apps.telecom.registerNtnRoamingPartner", resultTimeoutMs: 30000 },
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
