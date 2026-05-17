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
const createdAt = "2026-04-25T15:00:00Z";
const actorTag = "sys.bpmn.seed.open-defence-w5";

type Entry = { project: string; proc: string; bpmnProcessId: string; nsidNs: string; timeoutMs: number };

const entries: Entry[] = [
  { project: "open-biosecurity",                proc: "flagBwcBreach",                  bpmnProcessId: "open_biosecurity_flag_bwc_breach",                            nsidNs: "biosecurity",              timeoutMs: 20000 },
  { project: "open-biosecurity",                proc: "flagDualUseGof",                 bpmnProcessId: "open_biosecurity_flag_dual_use_gof",                          nsidNs: "biosecurity",              timeoutMs: 20000 },
  { project: "open-biosecurity-certification",  proc: "trackBslExportControl",          bpmnProcessId: "open_biosecurity_certification_track_bsl_export_control",     nsidNs: "biosecurityCertification", timeoutMs: 15000 },
  { project: "open-amr-surveillance",           proc: "flagBioweaponSignal",            bpmnProcessId: "open_amr_surveillance_flag_bioweapon_signal",                 nsidNs: "amrSurveillance",          timeoutMs: 20000 },
  { project: "open-pharma-supply",              proc: "flagCountermeasureGap",          bpmnProcessId: "open_pharma_supply_flag_countermeasure_gap",                  nsidNs: "pharmaSupply",             timeoutMs: 15000 },
  { project: "open-mrna-vaccine-hub",           proc: "flagStrategicReserveBreach",     bpmnProcessId: "open_mrna_vaccine_hub_flag_strategic_reserve_breach",         nsidNs: "mrnaVaccineHub",           timeoutMs: 15000 },
  { project: "open-agri-food-security",         proc: "flagFoodWeaponization",          bpmnProcessId: "open_agri_food_security_flag_food_weaponization",             nsidNs: "agriFoodSecurity",         timeoutMs: 15000 },
  { project: "open-feed-provenance",            proc: "flagAgroterrorism",              bpmnProcessId: "open_feed_provenance_flag_agroterrorism",                     nsidNs: "feedProvenance",           timeoutMs: 15000 },
  { project: "open-pandemic-prep",              proc: "flagBioMilitaryStockpile",       bpmnProcessId: "open_pandemic_prep_flag_bio_military_stockpile",              nsidNs: "pandemicPrep",             timeoutMs: 15000 },
  { project: "open-trusted-flagger",            proc: "flagStateMandatedTakedown",      bpmnProcessId: "open_trusted_flagger_flag_state_mandated_takedown",           nsidNs: "trustedFlagger",           timeoutMs: 15000 },
  { project: "open-content-moderation-appeal",  proc: "flagPoliticalCensorship",        bpmnProcessId: "open_content_moderation_appeal_flag_political_censorship",    nsidNs: "contentModerationAppeal",  timeoutMs: 15000 },
  { project: "open-press-finance-coercion",     proc: "flagStateMediaCoercion",         bpmnProcessId: "open_press_finance_coercion_flag_state_media_coercion",       nsidNs: "pressFinanceCoercion",     timeoutMs: 15000 },
  { project: "open-misinformation-observatory", proc: "flagCoordinatedCampaign",        bpmnProcessId: "open_misinformation_observatory_flag_coordinated_campaign",   nsidNs: "misinformationObservatory", timeoutMs: 15000 },
  { project: "open-itu-spectrum",               proc: "flagJamming",                    bpmnProcessId: "open_itu_spectrum_flag_jamming",                              nsidNs: "ituSpectrum",              timeoutMs: 15000 },
  { project: "open-itu-spectrum",               proc: "flagGnssSpoofing",               bpmnProcessId: "open_itu_spectrum_flag_gnss_spoofing",                        nsidNs: "ituSpectrum",              timeoutMs: 15000 },
  { project: "open-itu-spectrum",               proc: "flagSatelliteUplinkInterference", bpmnProcessId: "open_itu_spectrum_flag_satellite_uplink_interference",       nsidNs: "ituSpectrum",              timeoutMs: 15000 },
  { project: "open-quantum-safe-crypto",        proc: "flagPqcMigrationLag",            bpmnProcessId: "open_quantum_safe_crypto_flag_pqc_migration_lag",             nsidNs: "quantumSafeCrypto",        timeoutMs: 15000 },
  { project: "open-qkd-quantum",                proc: "registerMilitaryQkdLink",        bpmnProcessId: "open_qkd_quantum_register_military_qkd_link",                 nsidNs: "qkdQuantum",               timeoutMs: 15000 },
  { project: "open-c2pa-content-cred",          proc: "flagAdversarialDeepfake",        bpmnProcessId: "open_c2pa_content_cred_flag_adversarial_deepfake",            nsidNs: "c2paContentCred",          timeoutMs: 15000 },
  { project: "open-spr",                        proc: "flagStrategicDrawdown",          bpmnProcessId: "open_spr_flag_strategic_drawdown",                            nsidNs: "spr",                      timeoutMs: 15000 },
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
