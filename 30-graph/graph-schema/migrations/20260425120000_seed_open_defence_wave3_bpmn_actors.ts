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
const createdAt = "2026-04-25T12:00:00Z";
const actorTag = "sys.bpmn.seed.open-defence-w3";

type Entry = { project: string; proc: string; bpmnProcessId: string; nsidNs: string; timeoutMs: number };

const entries: Entry[] = [
  { project: "open-critical-minerals",        proc: "flagRareEarthChokepoint",      bpmnProcessId: "open_critical_minerals_flag_rare_earth_chokepoint",      nsidNs: "criticalMinerals",      timeoutMs: 15000 },
  { project: "open-critical-minerals",        proc: "trackArmsGradeMetal",          bpmnProcessId: "open_critical_minerals_track_arms_grade_metal",          nsidNs: "criticalMinerals",      timeoutMs: 20000 },
  { project: "open-isic",                     proc: "classifyArmsManufacturing",    bpmnProcessId: "open_isic_classify_arms_manufacturing",                  nsidNs: "openIsic",              timeoutMs: 15000 },
  { project: "open-unispsc",                  proc: "flagArmsCommodity",            bpmnProcessId: "open_unispsc_flag_arms_commodity",                       nsidNs: "openUnispsc",           timeoutMs: 15000 },
  { project: "open-export-credit-agency",     proc: "trackArmsExportFinance",       bpmnProcessId: "open_export_credit_agency_track_arms_export_finance",    nsidNs: "exportCreditAgency",    timeoutMs: 20000 },
  { project: "open-ai-supply-chain",          proc: "flagAiWeaponizedComponent",    bpmnProcessId: "open_ai_supply_chain_flag_ai_weaponized_component",      nsidNs: "aiSupplyChain",         timeoutMs: 15000 },
  { project: "open-aviation-safety",          proc: "notifyMilitaryNotam",          bpmnProcessId: "open_aviation_safety_notify_military_notam",             nsidNs: "aviationSafety",        timeoutMs: 15000 },
  { project: "open-airport-narita-ops",       proc: "flagArmsCargoCustoms",         bpmnProcessId: "open_airport_narita_ops_flag_arms_cargo_customs",        nsidNs: "airportNaritaOps",      timeoutMs: 20000 },
  { project: "open-airline-jal-ops",          proc: "flagCargoArmsTransit",         bpmnProcessId: "open_airline_jal_ops_flag_cargo_arms_transit",           nsidNs: "airlineJalOps",         timeoutMs: 15000 },
  { project: "open-uas-traffic-management",   proc: "flagWeaponizedDrone",          bpmnProcessId: "open_uas_traffic_management_flag_weaponized_drone",      nsidNs: "uasTrafficManagement",  timeoutMs: 15000 },
  { project: "open-artemis-lunar",            proc: "flagOuterSpaceTreatyViolation", bpmnProcessId: "open_artemis_lunar_flag_outer_space_treaty_violation",  nsidNs: "artemisLunar",          timeoutMs: 15000 },
  { project: "open-iaea-safeguards",          proc: "flagNuclearWeaponDiversion",   bpmnProcessId: "open_iaea_safeguards_flag_nuclear_weapon_diversion",     nsidNs: "iaeaSafeguards",        timeoutMs: 20000 },
  { project: "open-disarmament-treaties",     proc: "flagTreatyBreach",             bpmnProcessId: "open_disarmament_treaties_flag_treaty_breach",           nsidNs: "disarmamentTreaties",   timeoutMs: 20000 },
  { project: "open-jpn-gov",                  proc: "registerFmsCase",              bpmnProcessId: "open_jpn_gov_register_fms_case",                         nsidNs: "openJpnGov",            timeoutMs: 20000 },
  { project: "open-jpn-gov",                  proc: "registerKokusanWeaponsExport", bpmnProcessId: "open_jpn_gov_register_kokusan_weapons_export",           nsidNs: "openJpnGov",            timeoutMs: 20000 },
  { project: "open-ocds-procurement",         proc: "flagDefenceProcurement",       bpmnProcessId: "open_ocds_procurement_flag_defence_procurement",         nsidNs: "ocdsProcurement",       timeoutMs: 15000 },
  { project: "open-debarment-list",           proc: "flagArmsDebarment",            bpmnProcessId: "open_debarment_list_flag_arms_debarment",                nsidNs: "debarmentList",         timeoutMs: 15000 },
  { project: "open-laws-autonomous-weapons",  proc: "flagLawsDeployment",           bpmnProcessId: "open_laws_autonomous_weapons_flag_laws_deployment",      nsidNs: "lawsAutonomousWeapons", timeoutMs: 15000 },
  { project: "open-genocide-convention",      proc: "flagAtrocityArms",             bpmnProcessId: "open_genocide_convention_flag_atrocity_arms",            nsidNs: "genocideConvention",    timeoutMs: 15000 },
  { project: "open-poc-ihl",                  proc: "flagIhlBreachArms",            bpmnProcessId: "open_poc_ihl_flag_ihl_breach_arms",                      nsidNs: "pocIhl",                timeoutMs: 15000 },
];

const kebabToSlug = (kebab: string, proc: string): string =>
  `${kebab}-${proc.replace(/([A-Z])/g, "-$1").toLowerCase()}-v1`;
const ownerDidOf = (project: string) => `did:web:${project}.etzhayyim.com:ops`;

const processSeeds: ProcessSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${kebabToSlug(e.project, e.proc)}`,
  bpmnProcessId: e.bpmnProcessId,
  sourcePath: `00-contracts/bpmn/com/etzhayyim/${e.project}/${e.proc}.bpmn`,
  ownerDid: ownerDidOf(e.project),
}));

const bindingSeeds: BindingSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${e.project}-${e.proc}-v1`,
  nsid: `com.etzhayyim.apps.${e.nsidNs}.${e.proc}`,
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
