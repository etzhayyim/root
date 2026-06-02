import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0049 D4 — register judge / bengoshi / adr / legal-aid as BPMN-as-actor
// (ADR-0056). Each was previously "logical actor (MCP-only, no Worker)" per
// ADR-0016. Now each gets vertex_bpmn_process_def + vertex_bpmn_lexicon_binding
// rows so /xrpc/{nsid} dispatches via Zeebe instead of returning 404.

type Seed = {
  project: string;
  ownerDid: string;
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T23:04:00Z";
const actorTag = "sys.bpmn.seed.legal-logical-actors";
// bpmn-coverage gate marker: project: "judge,bengoshi,adr,legal-aid"

const seeds: Seed[] = [
  // judge.etzhayyim.com (200K judges, path-based DID)
  { project: "judge", ownerDid: "did:web:judge.etzhayyim.com",
    proc: "registerJudge", bpmnProcessId: "judge_register_judge",
    nsid: "com.etzhayyim.apps.judge.registerJudge", resultTimeoutMs: 15000 },
  { project: "judge", ownerDid: "did:web:judge.etzhayyim.com",
    proc: "listJudges", bpmnProcessId: "judge_list_judges",
    nsid: "com.etzhayyim.apps.judge.listJudges", resultTimeoutMs: 15000 },

  // bengoshi.etzhayyim.com (2.5M lawyers, path-based DID)
  { project: "bengoshi", ownerDid: "did:web:bengoshi.etzhayyim.com",
    proc: "registerLawyer", bpmnProcessId: "bengoshi_register_lawyer",
    nsid: "com.etzhayyim.apps.bengoshi.registerLawyer", resultTimeoutMs: 15000 },
  { project: "bengoshi", ownerDid: "did:web:bengoshi.etzhayyim.com",
    proc: "searchLawyers", bpmnProcessId: "bengoshi_search_lawyers",
    nsid: "com.etzhayyim.apps.bengoshi.searchLawyers", resultTimeoutMs: 15000 },

  // adr.etzhayyim.com (1M cases/yr, ICC/JCAA/AAA)
  { project: "adr", ownerDid: "did:web:adr.etzhayyim.com",
    proc: "registerArbitrator", bpmnProcessId: "adr_register_arbitrator",
    nsid: "com.etzhayyim.apps.adr.registerArbitrator", resultTimeoutMs: 15000 },
  { project: "adr", ownerDid: "did:web:adr.etzhayyim.com",
    proc: "createCase", bpmnProcessId: "adr_create_case",
    nsid: "com.etzhayyim.apps.adr.createCase", resultTimeoutMs: 15000 },

  // legal-aid.etzhayyim.com (10M cases/yr, public defender)
  { project: "legal-aid", ownerDid: "did:web:legal-aid.etzhayyim.com",
    proc: "registerOffice", bpmnProcessId: "legal_aid_register_office",
    nsid: "com.etzhayyim.apps.legal-aid.registerOffice", resultTimeoutMs: 15000 },
  { project: "legal-aid", ownerDid: "did:web:legal-aid.etzhayyim.com",
    proc: "openCase", bpmnProcessId: "legal_aid_open_case",
    nsid: "com.etzhayyim.apps.legal-aid.openCase", resultTimeoutMs: 15000 },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/${s.project}/${s.proc}.bpmn`;
const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${s.project}-${slug(s.proc)}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${s.project}-${s.proc}-v1`;

async function insertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const rel = sourcePath(s);
  const xml = readContract(rel);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${processVertexId(s)}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${rel}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)})
  `.execute(db);
}
async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${bindingVertexId(s)}, ${s.ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await insertProcessDef(db, s);
  for (const s of seeds) await insertBinding(db, s);
}
export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
  for (const s of seeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
}
