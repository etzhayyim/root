import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * karma.gftd.ai — additive BPMN seed for WBT settlement + ecosystem
 * resident agents (Phase K1 follow-on).
 *
 * Why a separate migration: keeps the original
 * `20260508130100_seed_karma_bpmn_actors.ts` immutable as historical
 * baseline, and lets the F5 watcher pick up the new BPMNs without
 * reseeding existing rows.
 *
 *  Process / NSID                       Trigger
 *  ---------------------------------------------------------------------
 *  karma_wbt_transfer        ai.gftd.apps.karma.wbtTransfer       (XRPC)
 *  karma_wbt_balance         ai.gftd.apps.karma.wbtBalance        (XRPC, query)
 *  karma_cohort_genesis      (none, autonomous)                   R/PT24H
 *  karma_organism_resident   (none, autonomous)                   R/PT15M
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T17:00:00Z";
const ownerDid = "did:web:karma.gftd.ai";
const actorTag = "sys.bpmn.seed.karma.wbt";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-wbt-transfer-v1",
    bpmnProcessId: "karma_wbt_transfer",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/wbtTransfer.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-wbt-balance-v1",
    bpmnProcessId: "karma_wbt_balance",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/wbtBalance.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-cohort-genesis-v1",
    bpmnProcessId: "karma_cohort_genesis",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/cohortGenesis.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-organism-resident-v1",
    bpmnProcessId: "karma_organism_resident",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/organismResident.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-organism-resume-v1",
    bpmnProcessId: "karma_organism_resume",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/organismResume.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-cohort-fission-v1",
    bpmnProcessId: "karma_cohort_fission",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/cohortFission.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-cohort-fission-sweep-v1",
    bpmnProcessId: "karma_cohort_fission_sweep",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/cohortFissionSweep.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-submit-rebirth-proof-v1",
    bpmnProcessId: "karma_submit_rebirth_proof",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/submitRebirthProof.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-filecoin-propose-v1",
    bpmnProcessId: "karma_filecoin_propose",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/filecoinPropose.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/karma-filecoin-renew-v1",
    bpmnProcessId: "karma_filecoin_renew",
    sourcePath: "00-contracts/bpmn/ai/gftd/karma/filecoinRenew.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/karma-wbtTransfer-v1",
    nsid: "ai.gftd.apps.karma.wbtTransfer",
    bpmnProcessId: "karma_wbt_transfer", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/karma-wbtBalance-v1",
    nsid: "ai.gftd.apps.karma.wbtBalance",
    bpmnProcessId: "karma_wbt_balance", ownerDid, resultTimeoutMs: 15_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/karma-organismResume-v1",
    nsid: "ai.gftd.apps.karma.organismResume",
    bpmnProcessId: "karma_organism_resume", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/karma-fissionCohort-v1",
    nsid: "ai.gftd.apps.karma.fissionCohort",
    bpmnProcessId: "karma_cohort_fission", ownerDid, resultTimeoutMs: 60_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/karma-submitRebirthProof-v1",
    nsid: "ai.gftd.apps.karma.submitRebirthProof",
    bpmnProcessId: "karma_submit_rebirth_proof", ownerDid, resultTimeoutMs: 60_000 },
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
