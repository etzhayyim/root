import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for wellbecoming.processMining (ADR-2604291800).
// F5 watcher picks this up and deploys to Zeebe within 30s.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..", "..");

export async function up(db: Kysely<unknown>): Promise<void> {
  const bpmnXml = readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/wellbecoming/processMining.bpmn"),
    "utf-8",
  );
  const now = "2026-04-29T22:10:00Z";
  const vertexId = "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/wellbecoming-process-mining-v1";
  const ownerDid = "did:web:bpmn.gftd.ai";
  const size = Buffer.byteLength(bpmnXml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${vertexId}, ${ownerDid}, ${"wellbecoming_process_mining"}, 1, ${bpmnXml},
           CAST(${size} AS integer),
           ${"00-contracts/bpmn/ai/gftd/wellbecoming/processMining.bpmn"},
           ${"active"}, ${now}, 1, ${ownerDid}, ${ownerDid}, ${"sys.bpmn.seed.wellbecoming"}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${vertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_process_def
    WHERE bpmn_process_id = 'wellbecoming_process_mining'
  `.execute(db);
}
