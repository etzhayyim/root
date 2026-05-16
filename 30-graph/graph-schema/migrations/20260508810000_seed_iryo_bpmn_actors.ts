import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * iryo.gftd.ai BPMN-as-actor seeding (ADR-2605080800 + ADR-0056 + ADR-2604282300).
 *
 * 5 BPMN process defs + 4 XRPC bindings.  No CF Worker (T2 tier:
 * pymagatama + Zeebe only).  3 timer-start BPMNs are autonomous;
 * the 4 XRPC bindings are reachable via bpmn-dispatcher
 * `http://dispatcher.gftd.ai:8080/xrpc/ai.gftd.apps.iryo.*`.
 *
 *  Process / NSID                                     Trigger
 *  ---------------------------------------------------------------------
 *  iryo_bed_occupancy_and_shift   (none, autonomous)  R/PT1H
 *  iryo_synthetic_event_tick      (none, autonomous)  R/PT15M (Phase 1 only)
 *  iryo_admission_discharge_cycle ai.gftd.apps.iryo.submitEncounter
 *                                 ai.gftd.apps.iryo.dischargeEncounter
 *                                                     (action-routed)
 *  iryo_drg_claim_cycle           ai.gftd.apps.iryo.submitDrgClaim
 *  iryo_agent_loop                ai.gftd.apps.iryo.agentLoop
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T11:00:00Z";
const ownerDid = "did:web:iryo.gftd.ai:hospital";
const actorTag = "sys.bpmn.seed.iryo";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-admission-discharge-cycle-v1",
    bpmnProcessId: "iryo_admission_discharge_cycle",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/admissionDischargeCycle.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-drg-claim-cycle-v1",
    bpmnProcessId: "iryo_drg_claim_cycle",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/drgClaimCycle.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-bed-occupancy-and-shift-v1",
    bpmnProcessId: "iryo_bed_occupancy_and_shift",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/bedOccupancyAndShift.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-agent-loop-v1",
    bpmnProcessId: "iryo_agent_loop",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/agentLoop.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/iryo-synthetic-event-tick-v1",
    bpmnProcessId: "iryo_synthetic_event_tick",
    sourcePath: "00-contracts/bpmn/ai/gftd/iryo/syntheticEventTick.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/iryo-submitEncounter-v1",
    nsid: "ai.gftd.apps.iryo.submitEncounter",
    bpmnProcessId: "iryo_admission_discharge_cycle", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/iryo-dischargeEncounter-v1",
    nsid: "ai.gftd.apps.iryo.dischargeEncounter",
    bpmnProcessId: "iryo_admission_discharge_cycle", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/iryo-submitDrgClaim-v1",
    nsid: "ai.gftd.apps.iryo.submitDrgClaim",
    bpmnProcessId: "iryo_drg_claim_cycle", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/iryo-agentLoop-v1",
    nsid: "ai.gftd.apps.iryo.agentLoop",
    bpmnProcessId: "iryo_agent_loop", ownerDid, resultTimeoutMs: 60_000 },
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
