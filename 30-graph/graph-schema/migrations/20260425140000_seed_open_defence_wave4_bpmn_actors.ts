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
const createdAt = "2026-04-25T14:00:00Z";
const actorTag = "sys.bpmn.seed.open-defence-w4";

type Entry = { project: string; proc: string; bpmnProcessId: string; nsidNs: string; timeoutMs: number };

const entries: Entry[] = [
  { project: "open-cyber-soc",              proc: "escalateStateApt",            bpmnProcessId: "open_cyber_soc_escalate_state_apt",                  nsidNs: "cyberSoc",            timeoutMs: 20000 },
  { project: "open-cyber-incident",         proc: "linkIncidentToTreaty",        bpmnProcessId: "open_cyber_incident_link_incident_to_treaty",        nsidNs: "cyberIncident",       timeoutMs: 15000 },
  { project: "open-mass-autonomous-ship",   proc: "flagWeaponizedMass",          bpmnProcessId: "open_mass_autonomous_ship_flag_weaponized_mass",     nsidNs: "massAutonomousShip",  timeoutMs: 15000 },
  { project: "open-fusion-energy",          proc: "flagIcfWeaponsLink",          bpmnProcessId: "open_fusion_energy_flag_icf_weapons_link",           nsidNs: "fusionEnergy",        timeoutMs: 20000 },
  { project: "open-pandemic-treaty",        proc: "flagBwcDualUse",              bpmnProcessId: "open_pandemic_treaty_flag_bwc_dual_use",             nsidNs: "pandemicTreaty",      timeoutMs: 15000 },
  { project: "open-cyclone-prepo",          proc: "flagMilitaryHadr",            bpmnProcessId: "open_cyclone_prepo_flag_military_hadr",              nsidNs: "cyclonePrepo",        timeoutMs: 15000 },
  { project: "open-redsea-naval",           proc: "flagFreedomOfNavigation",     bpmnProcessId: "open_redsea_naval_flag_freedom_of_navigation",       nsidNs: "redseaNaval",         timeoutMs: 15000 },
  { project: "open-redsea-incident",        proc: "flagShipMissileStrike",       bpmnProcessId: "open_redsea_incident_flag_ship_missile_strike",      nsidNs: "redseaIncident",      timeoutMs: 20000 },
  { project: "open-redsea-rerouting",       proc: "flagSupplyChainImpact",       bpmnProcessId: "open_redsea_rerouting_flag_supply_chain_impact",     nsidNs: "redseaRerouting",     timeoutMs: 15000 },
  { project: "open-hormuz-darkfleet",       proc: "flagIranSpoofing",            bpmnProcessId: "open_hormuz_darkfleet_flag_iran_spoofing",           nsidNs: "hormuzDarkfleet",     timeoutMs: 15000 },
  { project: "open-hormuz-incident",        proc: "flagTankerHijack",            bpmnProcessId: "open_hormuz_incident_flag_tanker_hijack",            nsidNs: "hormuzIncident",      timeoutMs: 20000 },
  { project: "open-malacca-incident",       proc: "flagPiracyEscort",            bpmnProcessId: "open_malacca_incident_flag_piracy_escort",           nsidNs: "malaccaIncident",     timeoutMs: 15000 },
  { project: "open-cell-broadcast-alert",   proc: "notifyJalert",                bpmnProcessId: "open_cell_broadcast_alert_notify_jalert",            nsidNs: "cellBroadcastAlert",  timeoutMs: 10000 },
  { project: "open-internet-shutdown",      proc: "flagWartimeShutdown",         bpmnProcessId: "open_internet_shutdown_flag_wartime_shutdown",       nsidNs: "internetShutdown",    timeoutMs: 15000 },
  { project: "open-encryption-debate",      proc: "flagBackdoorMandate",         bpmnProcessId: "open_encryption_debate_flag_backdoor_mandate",       nsidNs: "encryptionDebate",    timeoutMs: 15000 },
  { project: "open-mining-operation",       proc: "flagConflictMineral",         bpmnProcessId: "open_mining_operation_flag_conflict_mineral",        nsidNs: "miningOperation",     timeoutMs: 15000 },
  { project: "open-deep-sea-mining",        proc: "flagStrategicSeabedClaim",    bpmnProcessId: "open_deep_sea_mining_flag_strategic_seabed_claim",   nsidNs: "deepSeaMining",       timeoutMs: 15000 },
  { project: "open-arctic-nsr",             proc: "flagArcticMilitarization",    bpmnProcessId: "open_arctic_nsr_flag_arctic_militarization",         nsidNs: "arcticNsr",           timeoutMs: 15000 },
  { project: "open-antarctic-treaty",       proc: "flagAntarcticMilitary",       bpmnProcessId: "open_antarctic_treaty_flag_antarctic_military",      nsidNs: "antarcticTreaty",     timeoutMs: 15000 },
  { project: "open-bbnj-highseas",          proc: "flagHighseasMilitary",        bpmnProcessId: "open_bbnj_highseas_flag_highseas_military",          nsidNs: "bbnjHighseas",        timeoutMs: 15000 },
  { project: "open-orbital-debris",         proc: "trackKesslerCascade",         bpmnProcessId: "open_orbital_debris_track_kessler_cascade",          nsidNs: "orbitalDebris",       timeoutMs: 15000 },
  { project: "open-space-traffic",          proc: "trackHostileRpo",             bpmnProcessId: "open_space_traffic_track_hostile_rpo",               nsidNs: "spaceTraffic",        timeoutMs: 15000 },
  { project: "open-fatf-greylist",          proc: "flagSanctionsEvasion",        bpmnProcessId: "open_fatf_greylist_flag_sanctions_evasion",          nsidNs: "fatfGreylist",        timeoutMs: 15000 },
  { project: "open-fatf-travel-rule",       proc: "flagCryptoSanctionsEvasion",  bpmnProcessId: "open_fatf_travel_rule_flag_crypto_sanctions_evasion", nsidNs: "fatfTravelRule",     timeoutMs: 15000 },
  { project: "open-crypto-mixer-sanction",  proc: "flagMixerUseByDprk",          bpmnProcessId: "open_crypto_mixer_sanction_flag_mixer_use_by_dprk",  nsidNs: "cryptoMixerSanction", timeoutMs: 15000 },
];

const kebabToSlug = (kebab: string, proc: string): string =>
  `${kebab}-${proc.replace(/([A-Z])/g, "-$1").toLowerCase()}-v1`;
const ownerDidOf = (project: string) => `did:web:${project}.etzhayyim.com:ops`;

const processSeeds: ProcessSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/${kebabToSlug(e.project, e.proc)}`,
  bpmnProcessId: e.bpmnProcessId,
  sourcePath: `00-contracts/bpmn/ai/gftd/${e.project}/${e.proc}.bpmn`,
  ownerDid: ownerDidOf(e.project),
}));

const bindingSeeds: BindingSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${e.project}-${e.proc}-v1`,
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
