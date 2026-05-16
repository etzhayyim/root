import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * shosha.gftd.ai Phase 2d (simplified) — register approveTrade /
 * rejectTrade BPMN + 2 XRPC bindings.
 *
 * 2 process_def + 2 lexicon binding rows (XRPC-only, no autonomous timer).
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-07T18:00:00Z";
const ownerDid = "did:web:shosha.gftd.ai";
const actorTag = "sys.bpmn.seed.shosha.phase2d";

const processSeeds: P[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-approve-trade-v1",
    bpmnProcessId: "shosha_approve_trade",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/approveTrade.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-reject-trade-v1",
    bpmnProcessId: "shosha_reject_trade",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/rejectTrade.bpmn",
    ownerDid,
  },
];

const bindingSeeds: B[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/shosha-approveTrade-v1",
    nsid: "ai.gftd.apps.shosha.approveTrade",
    bpmnProcessId: "shosha_approve_trade",
    ownerDid,
    resultTimeoutMs: 30_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/shosha-rejectTrade-v1",
    nsid: "ai.gftd.apps.shosha.rejectTrade",
    bpmnProcessId: "shosha_reject_trade",
    ownerDid,
    resultTimeoutMs: 30_000,
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
