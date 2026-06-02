import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-04-28T23:50:00Z";
const actorTag = "sys.bpmn.seed.open-smartphone";

type ProcessSeed = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const entries: Array<{ project: string; bpmnProcessId: string; proc: string; ownerDid: string }> = [
  // BOM
  { project: "open-smartphone-bom", bpmnProcessId: "open_smartphone_bom_record_bom_line",         proc: "recordBomLine",          ownerDid: "did:web:open-smartphone-bom.etzhayyim.com" },
  { project: "open-smartphone-bom", bpmnProcessId: "open_smartphone_bom_assemble_bom",            proc: "assembleBom",            ownerDid: "did:web:open-smartphone-bom.etzhayyim.com" },
  { project: "open-smartphone-bom", bpmnProcessId: "open_smartphone_bom_record_alternative_source", proc: "recordAlternativeSource", ownerDid: "did:web:open-smartphone-bom.etzhayyim.com" },
  { project: "open-smartphone-bom", bpmnProcessId: "open_smartphone_bom_compute_open_score",      proc: "computeOpenScore",       ownerDid: "did:web:open-smartphone-bom.etzhayyim.com" },
  // EMS
  { project: "open-smartphone-ems", bpmnProcessId: "open_smartphone_ems_register_facility",       proc: "registerFacility",       ownerDid: "did:web:open-smartphone-ems.etzhayyim.com" },
  { project: "open-smartphone-ems", bpmnProcessId: "open_smartphone_ems_record_capacity_order",   proc: "recordCapacityOrder",    ownerDid: "did:web:open-smartphone-ems.etzhayyim.com" },
  { project: "open-smartphone-ems", bpmnProcessId: "open_smartphone_ems_fetch_compliance_delta",  proc: "fetchComplianceDelta",   ownerDid: "did:web:open-smartphone-ems.etzhayyim.com:ops" },
  { project: "open-smartphone-ems", bpmnProcessId: "open_smartphone_ems_daily_pulse",             proc: "dailyPulse",             ownerDid: "did:web:open-smartphone-ems.etzhayyim.com:ops" },
  // Modem
  { project: "open-smartphone-modem", bpmnProcessId: "open_smartphone_modem_record_modem_spec",   proc: "recordModemSpec",        ownerDid: "did:web:open-smartphone-modem.etzhayyim.com" },
  { project: "open-smartphone-modem", bpmnProcessId: "open_smartphone_modem_record_type_approval", proc: "recordTypeApproval",    ownerDid: "did:web:open-smartphone-modem.etzhayyim.com" },
  { project: "open-smartphone-modem", bpmnProcessId: "open_smartphone_modem_flag_patent_blocker", proc: "flagPatentBlocker",      ownerDid: "did:web:open-smartphone-modem.etzhayyim.com" },
  { project: "open-smartphone-modem", bpmnProcessId: "open_smartphone_modem_fetch_sep_delta",     proc: "fetchSepDelta",          ownerDid: "did:web:open-smartphone-modem.etzhayyim.com:ops" },
  // OS
  { project: "open-smartphone-os", bpmnProcessId: "open_smartphone_os_register_os_build",        proc: "registerOsBuild",        ownerDid: "did:web:open-smartphone-os.etzhayyim.com" },
  { project: "open-smartphone-os", bpmnProcessId: "open_smartphone_os_record_hal_driver",         proc: "recordHalDriver",        ownerDid: "did:web:open-smartphone-os.etzhayyim.com" },
  { project: "open-smartphone-os", bpmnProcessId: "open_smartphone_os_track_ota_release",         proc: "trackOtaRelease",        ownerDid: "did:web:open-smartphone-os.etzhayyim.com" },
  { project: "open-smartphone-os", bpmnProcessId: "open_smartphone_os_fetch_security_patch_delta", proc: "fetchSecurityPatchDelta", ownerDid: "did:web:open-smartphone-os.etzhayyim.com:ops" },
  // Patent
  { project: "open-smartphone-patent", bpmnProcessId: "open_smartphone_patent_record_license_pool",  proc: "recordLicensePool",    ownerDid: "did:web:open-smartphone-patent.etzhayyim.com" },
  { project: "open-smartphone-patent", bpmnProcessId: "open_smartphone_patent_map_patent_dependency", proc: "mapPatentDependency",  ownerDid: "did:web:open-smartphone-patent.etzhayyim.com" },
  { project: "open-smartphone-patent", bpmnProcessId: "open_smartphone_patent_flag_expiry_gate",      proc: "flagExpiryGate",       ownerDid: "did:web:open-smartphone-patent.etzhayyim.com:ops" },
  { project: "open-smartphone-patent", bpmnProcessId: "open_smartphone_patent_fetch_sep_landscape_delta", proc: "fetchSepLandscapeDelta", ownerDid: "did:web:open-smartphone-patent.etzhayyim.com:ops" },
  // Sensor
  { project: "open-smartphone-sensor", bpmnProcessId: "open_smartphone_sensor_register_sensor",        proc: "registerSensor",         ownerDid: "did:web:open-smartphone-sensor.etzhayyim.com" },
  { project: "open-smartphone-sensor", bpmnProcessId: "open_smartphone_sensor_record_calibration",     proc: "recordCalibration",      ownerDid: "did:web:open-smartphone-sensor.etzhayyim.com" },
  { project: "open-smartphone-sensor", bpmnProcessId: "open_smartphone_sensor_fetch_driver_availability", proc: "fetchDriverAvailability", ownerDid: "did:web:open-smartphone-sensor.etzhayyim.com:ops" },
  { project: "open-smartphone-sensor", bpmnProcessId: "open_smartphone_sensor_daily_pulse",            proc: "dailyPulse",             ownerDid: "did:web:open-smartphone-sensor.etzhayyim.com:ops" },
  // SoC
  { project: "open-smartphone-soc", bpmnProcessId: "open_smartphone_soc_register_chip_design",    proc: "registerChipDesign",     ownerDid: "did:web:open-smartphone-soc.etzhayyim.com" },
  { project: "open-smartphone-soc", bpmnProcessId: "open_smartphone_soc_track_fab_order",         proc: "trackFabOrder",          ownerDid: "did:web:open-smartphone-soc.etzhayyim.com" },
  { project: "open-smartphone-soc", bpmnProcessId: "open_smartphone_soc_flag_export_control",     proc: "flagExportControl",      ownerDid: "did:web:open-smartphone-soc.etzhayyim.com" },
  { project: "open-smartphone-soc", bpmnProcessId: "open_smartphone_soc_fetch_riscv_ecosystem_delta", proc: "fetchRiscvEcosystemDelta", ownerDid: "did:web:open-smartphone-soc.etzhayyim.com:ops" },
];

const processSeeds: ProcessSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${e.project}-${e.proc}-v1`,
  bpmnProcessId: e.bpmnProcessId,
  sourcePath: `00-contracts/bpmn/com/etzhayyim/${e.project}/${e.proc}.bpmn`,
  ownerDid: e.ownerDid,
}));

async function insertProcessDef(db: Kysely<unknown>, s: ProcessSeed): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds)
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
