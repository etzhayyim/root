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
const createdAt = "2026-04-25T11:00:00Z";
const actorTag = "sys.bpmn.seed.open-defence-w2";

type Entry = { project: string; proc: string; bpmnProcessId: string; nsidNs: string; timeoutMs: number };

const entries: Entry[] = [
  { project: "open-cyber-threat",            proc: "assessThreatActor",          bpmnProcessId: "open_cyber_threat_assess_threat_actor",          nsidNs: "cyberThreat",            timeoutMs: 20000 },
  { project: "open-cyber-vuln",              proc: "linkExploitToActor",         bpmnProcessId: "open_cyber_vuln_link_exploit_to_actor",          nsidNs: "cyberVuln",              timeoutMs: 20000 },
  { project: "open-zero-day-broker",         proc: "flagZeroDayTrade",           bpmnProcessId: "open_zero_day_broker_flag_zero_day_trade",       nsidNs: "zeroDayBroker",          timeoutMs: 15000 },
  { project: "open-cve-cna",                 proc: "flagWeaponizedCve",          bpmnProcessId: "open_cve_cna_flag_weaponized_cve",               nsidNs: "cveCna",                 timeoutMs: 15000 },
  { project: "open-ransomware-pay",          proc: "screenRansomSanctions",      bpmnProcessId: "open_ransomware_pay_screen_ransom_sanctions",    nsidNs: "ransomwarePay",          timeoutMs: 20000 },
  { project: "open-ofac-sanctions-sdn",      proc: "matchSdnEntity",             bpmnProcessId: "open_ofac_sanctions_sdn_match_sdn_entity",       nsidNs: "ofacSanctionsSdn",       timeoutMs: 20000 },
  { project: "open-bis-triennial",           proc: "classifyEccnControl",        bpmnProcessId: "open_bis_triennial_classify_eccn_control",       nsidNs: "bisTriennial",           timeoutMs: 15000 },
  { project: "open-mofcom-export-control",   proc: "flagPrcExport",              bpmnProcessId: "open_mofcom_export_control_flag_prc_export",     nsidNs: "mofcomExportControl",    timeoutMs: 15000 },
  { project: "open-uflpa-enforcement",       proc: "flagUflpaSupplier",          bpmnProcessId: "open_uflpa_enforcement_flag_uflpa_supplier",     nsidNs: "uflpaEnforcement",       timeoutMs: 15000 },
  { project: "open-spyware-export",          proc: "flagSpywareTrade",           bpmnProcessId: "open_spyware_export_flag_spyware_trade",         nsidNs: "spywareExport",          timeoutMs: 15000 },
  { project: "open-ais-dark-vessel",         proc: "flagAisManipulation",        bpmnProcessId: "open_ais_dark_vessel_flag_ais_manipulation",     nsidNs: "aisDarkVessel",          timeoutMs: 15000 },
  { project: "open-shadow-fleet-insurance",  proc: "flagPiClubBypass",           bpmnProcessId: "open_shadow_fleet_insurance_flag_pi_club_bypass", nsidNs: "shadowFleetInsurance",  timeoutMs: 15000 },
  { project: "open-cable-repair-fleet",      proc: "flagSubseaCableTamper",      bpmnProcessId: "open_cable_repair_fleet_flag_subsea_cable_tamper", nsidNs: "cableRepairFleet",     timeoutMs: 15000 },
  { project: "open-critical-minerals",       proc: "flagSupplyConcentration",    bpmnProcessId: "open_critical_minerals_flag_supply_concentration", nsidNs: "criticalMinerals",     timeoutMs: 15000 },
  { project: "open-semiconductor-fab",       proc: "flagFabExportControl",       bpmnProcessId: "open_semiconductor_fab_flag_fab_export_control", nsidNs: "semiconductorFab",       timeoutMs: 15000 },
  { project: "open-semi-ip-licensing",       proc: "flagDualUseLicensing",       bpmnProcessId: "open_semi_ip_licensing_flag_dual_use_licensing", nsidNs: "semiIpLicensing",        timeoutMs: 15000 },
  { project: "open-space-traffic",           proc: "flagAdversarialManeuver",    bpmnProcessId: "open_space_traffic_flag_adversarial_maneuver",   nsidNs: "spaceTraffic",           timeoutMs: 15000 },
  { project: "open-orbital-debris",          proc: "flagAsatDebris",             bpmnProcessId: "open_orbital_debris_flag_asat_debris",           nsidNs: "orbitalDebris",          timeoutMs: 15000 },
  { project: "open-social-media-influence-op", proc: "flagStateInfluenceOp",     bpmnProcessId: "open_social_media_influence_op_flag_state_influence_op", nsidNs: "socialMediaInfluenceOp", timeoutMs: 15000 },
  { project: "open-deepfake-takedown",       proc: "flagStateSponsoredDeepfake", bpmnProcessId: "open_deepfake_takedown_flag_state_sponsored_deepfake", nsidNs: "deepfakeTakedown",  timeoutMs: 15000 },
  { project: "open-jpn-gov",                 proc: "registerAtlaContract",       bpmnProcessId: "open_jpn_gov_register_atla_contract",            nsidNs: "openJpnGov",             timeoutMs: 20000 },
  { project: "open-jpn-gov",                 proc: "notifyJsdfJcgAlert",         bpmnProcessId: "open_jpn_gov_notify_jsdf_jcg_alert",             nsidNs: "openJpnGov",             timeoutMs: 15000 },
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
