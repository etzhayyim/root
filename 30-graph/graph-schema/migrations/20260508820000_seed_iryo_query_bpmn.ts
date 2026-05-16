import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * iryo.gftd.ai Phase 1.1 — query BPMN seeding (ADR-2605080800).
 *
 * 4 read-only XRPC bindings backed by 4 minimal one-task BPMNs that
 * delegate to the iryo.coverage.snapshot / iryo.bed.occupancySnapshot /
 * iryo.encounter.list / iryo.claim.get pyzeebe primitives.
 *
 *   ai.gftd.apps.iryo.coverage          → iryo_coverage
 *   ai.gftd.apps.iryo.getBedOccupancy   → iryo_get_bed_occupancy
 *   ai.gftd.apps.iryo.listEncounters    → iryo_list_encounters
 *   ai.gftd.apps.iryo.getDrgClaim       → iryo_get_drg_claim
 *
 * Pure read path — no domain mutation. resultTimeoutMs=15000 (queries
 * are < 1 RTT against RW).
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T12:00:00Z";
const ownerDid = "did:web:iryo.gftd.ai:hospital";
const actorTag = "sys.bpmn.seed.iryo.query";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-coverage-v1",
    bpmnProcessId: "iryo_coverage",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/coverage.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-get-bed-occupancy-v1",
    bpmnProcessId: "iryo_get_bed_occupancy",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/getBedOccupancy.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-list-encounters-v1",
    bpmnProcessId: "iryo_list_encounters",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/listEncounters.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-get-drg-claim-v1",
    bpmnProcessId: "iryo_get_drg_claim",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/getDrgClaim.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/iryo-coverage-v1",
    nsid: "ai.gftd.apps.iryo.coverage",
    bpmnProcessId: "iryo_coverage", ownerDid, resultTimeoutMs: 15_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/iryo-getBedOccupancy-v1",
    nsid: "ai.gftd.apps.iryo.getBedOccupancy",
    bpmnProcessId: "iryo_get_bed_occupancy", ownerDid, resultTimeoutMs: 15_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/iryo-listEncounters-v1",
    nsid: "ai.gftd.apps.iryo.listEncounters",
    bpmnProcessId: "iryo_list_encounters", ownerDid, resultTimeoutMs: 15_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/iryo-getDrgClaim-v1",
    nsid: "ai.gftd.apps.iryo.getDrgClaim",
    bpmnProcessId: "iryo_get_drg_claim", ownerDid, resultTimeoutMs: 15_000 },
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
