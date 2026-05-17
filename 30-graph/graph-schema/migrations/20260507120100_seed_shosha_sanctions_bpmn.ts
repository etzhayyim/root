import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * shosha.etzhayyim.com Phase 2b — register `shosha_refresh_sanctions_list` BPMN.
 *
 * Timer-start only (no XRPC binding), so just one row in
 * vertex_bpmn_process_def. F5 watcher in bpmn-dispatcher will deploy
 * to Zeebe on its next tick.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-07T12:00:00Z";
const ownerDid = "did:web:shosha.etzhayyim.com";
const actorTag = "sys.bpmn.seed.shosha.phase2b";

const seeds: P[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/shosha-refresh-sanctions-list-v1",
    bpmnProcessId: "shosha_refresh_sanctions_list",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/refreshSanctionsList.bpmn",
    ownerDid,
  },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await insertProcessDef(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
