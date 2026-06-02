import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-05-01T10:00:00Z";
const ownerDid = "did:web:site.etzhayyim.com";
const actorId = "sys.bpmn.seed.site";

interface BpmnSeed {
  processVertexId: string;
  bindingVertexId: string;
  processId: string;
  nsid: string;
  sourcePath: string;
  resultTimeoutMs: number;
}

const seeds: BpmnSeed[] = [
  {
    processVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/site-ivfPqReindex-v1",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/site-ivfPqReindex-v1",
    processId: "site_ivf_pq_reindex",
    nsid: "com.etzhayyim.apps.site.ivfPqReindex",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/site/ivfPqReindex.bpmn",
    resultTimeoutMs: 14_400_000,
  },
  {
    processVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/site-corpus2skillDistill-v1",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/site-corpus2skillDistill-v1",
    processId: "site_corpus2skill_distill",
    nsid: "com.etzhayyim.apps.site.corpus2skillDistill",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/site/corpus2skillDistill.bpmn",
    resultTimeoutMs: 28_800_000,
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readContract(s.sourcePath);
    const size = Buffer.byteLength(xml, "utf8");

    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${s.processVertexId}, ${ownerDid}, ${s.processId}, 1, ${xml},
             CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt},
             1, ${ownerDid}, ${ownerDid}, ${actorId}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.processVertexId}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
         write_table_allowlist, status, created_at, sensitivity_ord,
         org_id, user_id, actor_id, actor_did, org_did)
      SELECT ${s.bindingVertexId}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
             CAST(${s.resultTimeoutMs} AS integer), '',
             'active', ${createdAt}, 1,
             ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.bindingVertexId}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.bindingVertexId}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = ${s.processVertexId}`.execute(db);
  }
}
