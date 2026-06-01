import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase B — read paths for legal-corpus.etzhayyim.com (ADR-0049).
// searchDocument: bge-m3 query embed + IVF cosine SELECT
// getDocument:    direct SELECT by vertex_id or canonical_uri
// listJurisdictions: read from mv_legal_corpus_jurisdiction_coverage
//
// All three are BPMN-as-actor (ADR-0056) for consistency. Latency budget
// 500ms is acceptable for legal research read paths.

type Seed = { proc: string; bpmnProcessId: string; nsid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T23:05:00Z";
const ownerDid = "did:web:legal-corpus.etzhayyim.com";
const actorTag = "sys.bpmn.seed.legal-corpus-read";
// bpmn-coverage gate marker: project: "legal-corpus"
const project = "legal-corpus";

const seeds: Seed[] = [
  { proc: "searchDocument",     bpmnProcessId: "legal_corpus_search_document",
    nsid: "app.etzhayyim.apps.legal-corpus.searchDocument",     resultTimeoutMs: 30000 },
  { proc: "getDocument",        bpmnProcessId: "legal_corpus_get_document",
    nsid: "app.etzhayyim.apps.legal-corpus.getDocument",        resultTimeoutMs: 10000 },
  { proc: "listJurisdictions",  bpmnProcessId: "legal_corpus_list_jurisdictions",
    nsid: "app.etzhayyim.apps.legal-corpus.listJurisdictions",  resultTimeoutMs: 10000 },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/${project}/${s.proc}.bpmn`;
const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${project}-${slug(s.proc)}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${project}-${s.proc}-v1`;

async function insertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const rel = sourcePath(s);
  const xml = readContract(rel);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${rel}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)})
  `.execute(db);
}
async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
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
