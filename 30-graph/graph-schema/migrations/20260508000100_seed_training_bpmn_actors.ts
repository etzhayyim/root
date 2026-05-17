import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * training.etzhayyim.com BPMN-as-actor seeding (ADR-0056 + ADR-2604282300 + ADR-2605070700).
 *
 * 5 BPMN process defs + 5 XRPC bindings.  No CF Worker (T2 tier:
 * pymagatama + Zeebe only).  Reachable via bpmn-dispatcher
 * `http://dispatcher.etzhayyim.com:8080/xrpc/ai.gftd.apps.training.*`.
 *
 *  Process / NSID                        Result timeout
 *  -----------------------------------------------------
 *  training_run_sft                      30 min  (1_800_000 ms)
 *  training_run_lora                     30 min
 *  training_run_distill                  60 min  (3_600_000 ms)
 *  training_run_eval                     10 min  (600_000 ms)
 *  training_promote                      30 s    (30_000 ms)
 *
 * Long timeouts reflect that the actual GPU work runs to completion
 * inside the pyzeebe handler before returning. If a run is expected
 * to exceed the cap (multi-hour SFT), invoke runSft asynchronously
 * (fire-and-forget) and poll vertex_training_run.status, instead of
 * waiting for the synchronous XRPC reply.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T00:01:00Z";
const ownerDid = "did:web:training.etzhayyim.com";
const actorTag = "sys.bpmn.seed.training";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-sft-v1",
    bpmnProcessId: "training_run_sft",
    sourcePath: "00-contracts/bpmn/ai/gftd/training/runSft.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-lora-v1",
    bpmnProcessId: "training_run_lora",
    sourcePath: "00-contracts/bpmn/ai/gftd/training/runLora.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-distill-v1",
    bpmnProcessId: "training_run_distill",
    sourcePath: "00-contracts/bpmn/ai/gftd/training/runDistill.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-run-eval-v1",
    bpmnProcessId: "training_run_eval",
    sourcePath: "00-contracts/bpmn/ai/gftd/training/runEval.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/training-promote-v1",
    bpmnProcessId: "training_promote",
    sourcePath: "00-contracts/bpmn/ai/gftd/training/promote.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runSft-v1",
    nsid: "ai.gftd.apps.training.runSft",
    bpmnProcessId: "training_run_sft", ownerDid, resultTimeoutMs: 1_800_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runLora-v1",
    nsid: "ai.gftd.apps.training.runLora",
    bpmnProcessId: "training_run_lora", ownerDid, resultTimeoutMs: 1_800_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runDistill-v1",
    nsid: "ai.gftd.apps.training.runDistill",
    bpmnProcessId: "training_run_distill", ownerDid, resultTimeoutMs: 3_600_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-runEval-v1",
    nsid: "ai.gftd.apps.training.runEval",
    bpmnProcessId: "training_run_eval", ownerDid, resultTimeoutMs: 600_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/training-promote-v1",
    nsid: "ai.gftd.apps.training.promote",
    bpmnProcessId: "training_promote", ownerDid, resultTimeoutMs: 30_000 },
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
