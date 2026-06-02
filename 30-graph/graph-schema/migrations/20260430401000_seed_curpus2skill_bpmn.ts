import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-04-30T12:35:00Z";
const ownerDid = "did:web:recruit.etzhayyim.com";
const actorTag = "sys.bpmn.seed.curpus2skill";
const processVertexId = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/curpus2skill-extractEvidence-v1";
const bpmnProcessId = "curpus2skill_extract_evidence";
const sourcePath = "00-contracts/bpmn/com/etzhayyim/curpus2skill/extractEvidence.bpmn";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT ${processVertexId}, ${ownerDid}, ${bpmnProcessId}, 1, ${xml},
           CAST(${size} AS integer), ${sourcePath}, 'active', ${createdAt},
           1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
}
