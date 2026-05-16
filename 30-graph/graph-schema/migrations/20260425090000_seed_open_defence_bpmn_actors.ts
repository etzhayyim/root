import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type ProcessSeed = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type BindingSeed = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-04-25T09:00:00Z";
const actorTag = "sys.bpmn.seed.open-defence";

type Entry = {
  project: string;
  bpmnProcessId: string;
  proc: string;
  nsidNs: string;
  timeoutMs: number;
};

const entries: Entry[] = [
  { project: "open-airplane", bpmnProcessId: "open_airplane_flag_airspace_violation", proc: "flagAirspaceViolation", nsidNs: "openAirplane", timeoutMs: 15000 },
  { project: "open-airplane", bpmnProcessId: "open_airplane_notify_no_fly_zone",     proc: "notifyNoFlyZone",     nsidNs: "openAirplane", timeoutMs: 15000 },
  { project: "open-ports",    bpmnProcessId: "open_ports_screen_vessel_sanctions",   proc: "screenVesselSanctions", nsidNs: "openPorts",   timeoutMs: 20000 },
  { project: "open-ports",    bpmnProcessId: "open_ports_flag_dark_fleet",           proc: "flagDarkFleet",       nsidNs: "openPorts",   timeoutMs: 15000 },
  { project: "open-rail",     bpmnProcessId: "open_rail_flag_critical_asset_incident", proc: "flagCriticalAssetIncident", nsidNs: "openRail", timeoutMs: 15000 },
  { project: "open-network",  bpmnProcessId: "open_network_report_cyber_incident",   proc: "reportCyberIncident", nsidNs: "openNetwork", timeoutMs: 30000 },
  { project: "open-network",  bpmnProcessId: "open_network_escalate_ddos",           proc: "escalateDdos",        nsidNs: "openNetwork", timeoutMs: 15000 },
  { project: "open-power",    bpmnProcessId: "open_power_report_grid_attack",        proc: "reportGridAttack",    nsidNs: "openPower",   timeoutMs: 30000 },
  { project: "open-gas",      bpmnProcessId: "open_gas_report_pipeline_sabotage",    proc: "reportPipelineSabotage", nsidNs: "openGas",  timeoutMs: 30000 },
  { project: "open-water",    bpmnProcessId: "open_water_report_infra_sabotage",     proc: "reportInfraSabotage", nsidNs: "openWater",   timeoutMs: 30000 },
  { project: "open-swift",    bpmnProcessId: "open_swift_screen_sanctions",          proc: "screenSanctions",     nsidNs: "openSwift",   timeoutMs: 20000 },
  { project: "open-banking",  bpmnProcessId: "open_banking_flag_suspicious_transaction", proc: "flagSuspiciousTransaction", nsidNs: "openBanking", timeoutMs: 20000 },
  { project: "open-jpn-gov",  bpmnProcessId: "open_jpn_gov_resolve_boei_sho_procurement", proc: "resolveBoeiShoProcurement", nsidNs: "openJpnGov", timeoutMs: 20000 },
  { project: "open-jpn-gov",  bpmnProcessId: "open_jpn_gov_check_tokutei_himitsu",   proc: "checkTokuteiHimitsu", nsidNs: "openJpnGov",  timeoutMs: 15000 },
  { project: "open-cofog",    bpmnProcessId: "open_cofog_classify_defence_function", proc: "classifyDefenceFunction", nsidNs: "openCofog", timeoutMs: 15000 },
  { project: "open-isic",     bpmnProcessId: "open_isic_flag_dual_use_industry",     proc: "flagDualUseIndustry", nsidNs: "openIsic",    timeoutMs: 15000 },
  { project: "open-seiyaku",  bpmnProcessId: "open_seiyaku_screen_export_control",   proc: "screenExportControl", nsidNs: "openSeiyaku", timeoutMs: 20000 },
  { project: "open-unispsc",  bpmnProcessId: "open_unispsc_flag_dual_use_commodity", proc: "flagDualUseCommodity", nsidNs: "openUnispsc", timeoutMs: 15000 },
];

const kebabToSlug = (kebab: string, proc: string): string => `${kebab}-${proc.replace(/([A-Z])/g, "-$1").toLowerCase()}-v1`;
const ownerDidOf = (project: string) => `did:web:${project}.gftd.ai:ops`;

const processSeeds: ProcessSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${kebabToSlug(e.project, e.proc)}`,
  bpmnProcessId: e.bpmnProcessId,
  sourcePath: `00-contracts/bpmn/ai/gftd/${e.project}/${e.proc}.bpmn`,
  ownerDid: ownerDidOf(e.project),
}));

const bindingSeeds: BindingSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${e.project}-${e.proc}-v1`,
  nsid: `ai.gftd.apps.${e.nsidNs}.${e.proc}`,
  bpmnProcessId: e.bpmnProcessId,
  ownerDid: ownerDidOf(e.project),
  resultTimeoutMs: e.timeoutMs,
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
async function insertBinding(db: Kysely<unknown>, s: BindingSeed): Promise<void> {
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
