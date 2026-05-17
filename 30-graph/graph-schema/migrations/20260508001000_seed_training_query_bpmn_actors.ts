import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * training.etzhayyim.com query-side BPMN-as-actor seeding (ADR-2605070700).
 *
 * 3 read-only XRPC queries that wrap the lineage tables added by
 * 20260508000000_vertex_training_lineage. No audit step (high-frequency
 * dashboard probes shouldn't pile up vertex_repo_commit rows — same
 * convention as shosha.coverage).
 *
 *  Process / NSID                              Trigger
 *  ---------------------------------------------------------------
 *  training_list_runs        ai.gftd.apps.training.listRuns
 *  training_list_checkpoints ai.gftd.apps.training.listCheckpoints
 *  training_serving          ai.gftd.apps.training.serving
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T00:10:00Z";
const ownerDid = "did:web:training.etzhayyim.com";
const actorTag = "sys.bpmn.seed.training.query";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-list-runs-v1",
    bpmnProcessId: "training_list_runs",
    sourcePath: "00-contracts/bpmn/ai/gftd/training/listRuns.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-list-checkpoints-v1",
    bpmnProcessId: "training_list_checkpoints",
    sourcePath: "00-contracts/bpmn/ai/gftd/training/listCheckpoints.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-serving-v1",
    bpmnProcessId: "training_serving",
    sourcePath: "00-contracts/bpmn/ai/gftd/training/serving.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-listRuns-v1",
    nsid: "ai.gftd.apps.training.listRuns",
    bpmnProcessId: "training_list_runs", ownerDid, resultTimeoutMs: 15_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-listCheckpoints-v1",
    nsid: "ai.gftd.apps.training.listCheckpoints",
    bpmnProcessId: "training_list_checkpoints", ownerDid, resultTimeoutMs: 15_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-serving-v1",
    nsid: "ai.gftd.apps.training.serving",
    bpmnProcessId: "training_serving", ownerDid, resultTimeoutMs: 15_000 },
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

async function insertBinding(db: Kysely<unknown>, s: B): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of bindingSeeds) await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  for (const s of processSeeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
