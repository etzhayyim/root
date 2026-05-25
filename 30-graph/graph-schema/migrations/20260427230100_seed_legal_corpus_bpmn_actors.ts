import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T23:01:00Z";
const ownerDid = "did:web:legal-corpus.etzhayyim.com";
const actorTag = "sys.bpmn.seed.legal-corpus";
// bpmn-coverage gate marker: project: "legal-corpus"
const project = "legal-corpus";

const seeds: Seed[] = [
  { proc: "ingestDocument",          bpmnProcessId: "legal_corpus_ingest_document",
    nsid: "app.etzhayyim.apps.legal-corpus.ingestDocument", resultTimeoutMs: 30000 },
  { proc: "embedDocument",           bpmnProcessId: "legal_corpus_embed_document",
    nsid: "app.etzhayyim.apps.legal-corpus.embedDocument", resultTimeoutMs: 60000 },
  { proc: "registerSource",          bpmnProcessId: "legal_corpus_register_source",
    nsid: "app.etzhayyim.apps.legal-corpus.registerSource", resultTimeoutMs: 15000 },
  { proc: "fetchCourtListenerDelta", bpmnProcessId: "legal_corpus_fetch_courtlistener_delta",
    nsid: "app.etzhayyim.apps.legal-corpus.fetchCourtListenerDelta", resultTimeoutMs: 600000 },
  { proc: "fetchEurLexDelta",        bpmnProcessId: "legal_corpus_fetch_eur_lex_delta",
    nsid: "app.etzhayyim.apps.legal-corpus.fetchEurLexDelta", resultTimeoutMs: 600000 },
  { proc: "fetchBailiiDelta",        bpmnProcessId: "legal_corpus_fetch_bailii_delta",
    nsid: "app.etzhayyim.apps.legal-corpus.fetchBailiiDelta", resultTimeoutMs: 600000 },
  { proc: "fetchWorldLiiDelta",      bpmnProcessId: "legal_corpus_fetch_worldlii_delta",
    nsid: "app.etzhayyim.apps.legal-corpus.fetchWorldLiiDelta", resultTimeoutMs: 600000 },
  { proc: "fetchCanLiiDelta",        bpmnProcessId: "legal_corpus_fetch_canlii_delta",
    nsid: "app.etzhayyim.apps.legal-corpus.fetchCanLiiDelta", resultTimeoutMs: 600000 },
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
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${rel}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
      CAST(${s.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await insertProcessDef(db, s);
  for (const s of seeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
  }
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
