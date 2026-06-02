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
const actorTag = "sys.bpmn.seed.open-cyber-fetch";

type ProcessSeed = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const entries: Array<{ project: string; bpmnProcessId: string; proc: string; ownerDid: string }> = [
  { project: "open-cyber-vuln",  bpmnProcessId: "open_cyber_vuln_fetch_nvd_delta",          proc: "fetchNvdDelta",         ownerDid: "did:web:open-cyber-vuln.etzhayyim.com:ops" },
  { project: "open-kev-catalog", bpmnProcessId: "open_kev_catalog_fetch_kev_delta",          proc: "fetchKevDelta",         ownerDid: "did:web:open-kev-catalog.etzhayyim.com:ops" },
  { project: "open-oss-vuln",    bpmnProcessId: "open_oss_vuln_fetch_ghsa_delta",            proc: "fetchGhsaDelta",        ownerDid: "did:web:open-oss-vuln.etzhayyim.com:ops" },
  { project: "open-cyber-threat",bpmnProcessId: "open_cyber_threat_fetch_mitre_attack_delta",proc: "fetchMitreAttackDelta", ownerDid: "did:web:open-cyber-threat.etzhayyim.com:ops" },
  { project: "open-cyber-soc",   bpmnProcessId: "open_cyber_soc_fetch_cisa_alert_delta",    proc: "fetchCisaAlertDelta",   ownerDid: "did:web:open-cyber-soc.etzhayyim.com:ops" },
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
