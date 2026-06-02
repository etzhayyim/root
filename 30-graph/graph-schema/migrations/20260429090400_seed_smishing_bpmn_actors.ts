import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-29T09:04:00Z";
const ownerDid = "did:web:smishing.etzhayyim.com";
const actorTag = "sys.bpmn.seed.smishing";
// bpmn-coverage gate marker: project: "smishing"
const project = "smishing";
const proc = "analyzeMessage";
const bpmnProcessId = "smishing_analyze_message";
const nsid = "com.etzhayyim.apps.smishing.analyzeMessageProcess";
const sourcePath = "00-contracts/bpmn/com/etzhayyim/smishing/analyzeMessage.bpmn";
const processVertexId = `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${project}-${proc}-v1`;
const bindingVertexId = `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${project}-${proc}-v1`;

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId}, ${ownerDid}, ${bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId}, ${ownerDid}, ${nsid}, ${bpmnProcessId}, 1,
      CAST(120000 AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
}
