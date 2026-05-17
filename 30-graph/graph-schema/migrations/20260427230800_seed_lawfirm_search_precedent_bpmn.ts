import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase C — lawfirm.searchPrecedent BPMN-as-actor (ADR-0049 Future Phase 3).
// Thin wrapper over legal_corpus_search_document with firm authz +
// auto-jurisdiction default. Also re-deploys runConflictCheck v2 which now
// includes a Task_Precedent call activity to legal_corpus_search_document.

type Seed = { proc: string; bpmnProcessId: string; nsid: string; resultTimeoutMs: number; version: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T23:08:00Z";
const ownerDid = "did:web:lawfirm.etzhayyim.com";
const actorTag = "sys.bpmn.seed.lawfirm-search-precedent";
// bpmn-coverage gate marker: project: "lawfirm"
const project = "lawfirm";

const seeds: Seed[] = [
  { proc: "searchPrecedent",  bpmnProcessId: "lawfirm_search_precedent",
    nsid: "ai.gftd.apps.lawfirm.searchPrecedent", resultTimeoutMs: 30000, version: 1 },
  // runConflictCheck v2 — adds Task_Precedent call activity. v1 row is
  // superseded by content-addressed PK collision on (project, slug, version),
  // so we bump version explicitly.
  { proc: "runConflictCheck", bpmnProcessId: "lawfirm_run_conflict_check",
    nsid: "ai.gftd.apps.lawfirm.runConflictCheck", resultTimeoutMs: 60000, version: 2 },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/${project}/${s.proc}.bpmn`;
const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/${project}-${slug(s.proc)}-v${s.version}`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${project}-${s.proc}-v${s.version}`;

async function insertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const rel = sourcePath(s);
  const xml = readContract(rel);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, CAST(${s.version} AS integer), ${xml}, CAST(${size} AS integer), ${rel}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)})
  `.execute(db);
}
async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  // For runConflictCheck v2, also retire v1 binding so the dispatcher routes
  // to the new version. searchPrecedent is brand new — no prior binding.
  if (s.proc === "runConflictCheck") {
    const v1Vid = `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${project}-${s.proc}-v1`;
    await sql`UPDATE vertex_bpmn_lexicon_binding SET status = 'superseded' WHERE vertex_id = ${v1Vid}`.execute(db);
  }
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, CAST(${s.version} AS integer), CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
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
  // Restore v1 runConflictCheck binding
  const v1Vid = `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${project}-runConflictCheck-v1`;
  await sql`UPDATE vertex_bpmn_lexicon_binding SET status = 'active' WHERE vertex_id = ${v1Vid}`.execute(db);
}
