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
const createdAt = "2026-04-28T23:01:00Z";
const actorTag = "sys.bpmn.seed.open-cyber";

type Entry = {
  project: string;
  bpmnProcessId: string;
  proc: string;
  nsidNs: string;
  timeoutMs: number;
};

const entries: Entry[] = [
  // open-cyber-vuln (3)
  { project: "open-cyber-vuln",              bpmnProcessId: "open_cyber_vuln_cve",                              proc: "recordCveDisclosure",      nsidNs: "cyberVuln",             timeoutMs: 20000 },
  { project: "open-cyber-vuln",              bpmnProcessId: "open_cyber_vuln_patch",                            proc: "recordPatchAdvisory",      nsidNs: "cyberVuln",             timeoutMs: 15000 },
  { project: "open-cyber-vuln",              bpmnProcessId: "open_cyber_vuln_link_exploit_to_actor",            proc: "linkExploitToActor",       nsidNs: "cyberVuln",             timeoutMs: 15000 },
  // open-cve-cna (3)
  { project: "open-cve-cna",                 bpmnProcessId: "open_cve_cna_record_assignment",                   proc: "recordAssignment",         nsidNs: "cveCna",                timeoutMs: 15000 },
  { project: "open-cve-cna",                 bpmnProcessId: "open_cve_cna_flag_disclosure_gap",                 proc: "flagDisclosureGap",        nsidNs: "cveCna",                timeoutMs: 15000 },
  { project: "open-cve-cna",                 bpmnProcessId: "open_cve_cna_flag_weaponized_cve",                 proc: "flagWeaponizedCve",        nsidNs: "cveCna",                timeoutMs: 15000 },
  // open-kev-catalog (2)
  { project: "open-kev-catalog",             bpmnProcessId: "open_kev_catalog_record_entry",                    proc: "recordEntry",              nsidNs: "kevCatalog",            timeoutMs: 15000 },
  { project: "open-kev-catalog",             bpmnProcessId: "open_kev_catalog_flag_remediation_lag",            proc: "flagRemediationLag",       nsidNs: "kevCatalog",            timeoutMs: 15000 },
  // open-oss-vuln (2)
  { project: "open-oss-vuln",                bpmnProcessId: "open_oss_vuln_register_advisory",                  proc: "registerAdvisory",         nsidNs: "ossVuln",               timeoutMs: 15000 },
  { project: "open-oss-vuln",                bpmnProcessId: "open_oss_vuln_record_sbom_match",                  proc: "recordSbomMatch",          nsidNs: "ossVuln",               timeoutMs: 20000 },
  // open-cyber-threat (3)
  { project: "open-cyber-threat",            bpmnProcessId: "open_cyber_threat_actor",                          proc: "recordThreatActor",        nsidNs: "cyberThreat",           timeoutMs: 20000 },
  { project: "open-cyber-threat",            bpmnProcessId: "open_cyber_threat_assess_threat_actor",            proc: "assessThreatActor",        nsidNs: "cyberThreat",           timeoutMs: 30000 },
  { project: "open-cyber-threat",            bpmnProcessId: "open_cyber_threat_campaign",                       proc: "recordCampaign",           nsidNs: "cyberThreat",           timeoutMs: 20000 },
  // open-cyber-incident (3)
  { project: "open-cyber-incident",          bpmnProcessId: "open_cyber_incident_report",                       proc: "reportIncident",           nsidNs: "cyberIncident",         timeoutMs: 20000 },
  { project: "open-cyber-incident",          bpmnProcessId: "open_cyber_incident_ioc",                          proc: "recordIOC",                nsidNs: "cyberIncident",         timeoutMs: 15000 },
  { project: "open-cyber-incident",          bpmnProcessId: "open_cyber_incident_link_incident_to_treaty",      proc: "linkIncidentToTreaty",     nsidNs: "cyberIncident",         timeoutMs: 15000 },
  // open-cyber-compliance (2)
  { project: "open-cyber-compliance",        bpmnProcessId: "open_cyber_compliance_isms",                       proc: "recordIsmsAudit",          nsidNs: "cyberCompliance",       timeoutMs: 20000 },
  { project: "open-cyber-compliance",        bpmnProcessId: "open_cyber_compliance_regulatory",                 proc: "recordRegulatoryReporting",nsidNs: "cyberCompliance",       timeoutMs: 20000 },
  // open-cyber-soc (3)
  { project: "open-cyber-soc",               bpmnProcessId: "open_cyber_soc_alert",                             proc: "recordSocAlert",           nsidNs: "cyberSoc",              timeoutMs: 15000 },
  { project: "open-cyber-soc",               bpmnProcessId: "open_cyber_soc_ir",                                proc: "recordIncidentResponse",   nsidNs: "cyberSoc",              timeoutMs: 20000 },
  { project: "open-cyber-soc",               bpmnProcessId: "open_cyber_soc_escalate_state_apt",                proc: "escalateStateApt",         nsidNs: "cyberSoc",              timeoutMs: 30000 },
  // open-cyber-resilience-stress (2)
  { project: "open-cyber-resilience-stress", bpmnProcessId: "open_cyber_resilience_stress_record_stress_test",  proc: "recordStressTest",         nsidNs: "cyberResilienceStress", timeoutMs: 20000 },
  { project: "open-cyber-resilience-stress", bpmnProcessId: "open_cyber_resilience_stress_report_resilience_gap", proc: "reportResilienceGap",   nsidNs: "cyberResilienceStress", timeoutMs: 20000 },
];

const kebabToSlug = (kebab: string, proc: string): string =>
  `${kebab}-${proc.replace(/([A-Z])/g, "-$1").toLowerCase()}-v1`;
const ownerDidOf = (project: string) => `did:web:${project}.etzhayyim.com:ops`;

const processSeeds: ProcessSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${kebabToSlug(e.project, e.proc)}`,
  bpmnProcessId: e.bpmnProcessId,
  sourcePath: `00-contracts/bpmn/ai/gftd/${e.project}/${e.proc}.bpmn`,
  ownerDid: ownerDidOf(e.project),
}));

const bindingSeeds: BindingSeed[] = entries.map((e) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${e.project}-${e.proc}-v1`,
  nsid: `app.etzhayyim.apps.${e.nsidNs}.${e.proc}`,
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
  for (const s of bindingSeeds)
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  for (const s of processSeeds)
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
