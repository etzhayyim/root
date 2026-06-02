import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed BPMN process_def + lexicon binding for personnelAssignmentDecide.
 * Picked up by bpmn-dispatcher F5 watcher within ~30s of apply.
 *
 * ADR-0056 BPMN-as-actor.
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T00:00:00Z";
const ownerDid = "did:web:etzhayyim.etzhayyim.com";
const actorTag = "sys.bpmn.seed.etzhayyim";

const PROCESS = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/etzhayyim-personnel-assignment-decide-v1",
  bpmnProcessId: "etzhayyim_personnel_assignment_decide",
  sourcePath: "00-contracts/bpmn/com/etzhayyim/etzhayyim/personnelAssignmentDecide.bpmn",
};
const BINDING = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-personnel-assignment-decide-xrpc-v1",
  nsid: "com.etzhayyim.apps.etzhayyim.personnelAssignmentDecide",
  bpmnProcessId: "etzhayyim_personnel_assignment_decide",
  resultTimeoutMs: 600_000,
};

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(PROCESS.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${PROCESS.vertexId}, ${ownerDid}, ${PROCESS.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${PROCESS.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId})
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${BINDING.vertexId}, ${ownerDid}, ${BINDING.nsid}, ${BINDING.bpmnProcessId}, 1, CAST(${BINDING.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId}`.execute(db);
}
