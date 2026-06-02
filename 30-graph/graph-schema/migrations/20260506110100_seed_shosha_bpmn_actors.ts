import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * shosha.etzhayyim.com BPMN-as-actor seeding (ADR-0056 + ADR-2604282300).
 *
 * 8 BPMN process defs + 4 XRPC bindings.  No CF Worker (T2 tier:
 * pymagatama + Zeebe only).  4 timer-start BPMNs are autonomous;
 * 4 XRPC bindings are reachable via bpmn-dispatcher
 * `http://dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.apps.shosha.*`.
 *
 *  Process / NSID                                   Trigger
 *  ---------------------------------------------------------------------
 *  shosha_market_intelligence_ingest  (none, autonomous)   R/PT1H
 *  shosha_trade_book_recompute        (none, autonomous)   R/PT4H
 *  shosha_trade_idea_synthesize       (none, autonomous)   R/PT4H
 *  shosha_daily_report                (none, autonomous)   cron 0 0 22 * * ?  (07:00 JST)
 *  shosha_submit_trade                com.etzhayyim.apps.shosha.submitTrade
 *  shosha_propose_hedge               com.etzhayyim.apps.shosha.proposeHedge
 *  shosha_comply_check                com.etzhayyim.apps.shosha.complyCheck
 *  shosha_agent_loop                  com.etzhayyim.apps.shosha.agentLoop
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-06T10:00:00Z";
const ownerDid = "did:web:shosha.etzhayyim.com";
const actorTag = "sys.bpmn.seed.shosha";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-market-intelligence-ingest-v1",
    bpmnProcessId: "shosha_market_intelligence_ingest",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shosha/marketIntelligenceIngest.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-trade-book-recompute-v1",
    bpmnProcessId: "shosha_trade_book_recompute",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shosha/tradeBookRecompute.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-trade-idea-synthesize-v1",
    bpmnProcessId: "shosha_trade_idea_synthesize",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shosha/tradeIdeaSynthesize.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-daily-report-v1",
    bpmnProcessId: "shosha_daily_report",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shosha/dailyShoshaReport.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-submit-trade-v1",
    bpmnProcessId: "shosha_submit_trade",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shosha/submitTrade.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-propose-hedge-v1",
    bpmnProcessId: "shosha_propose_hedge",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shosha/proposeHedge.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-comply-check-v1",
    bpmnProcessId: "shosha_comply_check",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shosha/complyCheck.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-agent-loop-v1",
    bpmnProcessId: "shosha_agent_loop",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shosha/agentLoop.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shosha-submitTrade-v1",
    nsid: "com.etzhayyim.apps.shosha.submitTrade",
    bpmnProcessId: "shosha_submit_trade", ownerDid, resultTimeoutMs: 60_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shosha-proposeHedge-v1",
    nsid: "com.etzhayyim.apps.shosha.proposeHedge",
    bpmnProcessId: "shosha_propose_hedge", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shosha-complyCheck-v1",
    nsid: "com.etzhayyim.apps.shosha.complyCheck",
    bpmnProcessId: "shosha_comply_check", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shosha-agentLoop-v1",
    nsid: "com.etzhayyim.apps.shosha.agentLoop",
    bpmnProcessId: "shosha_agent_loop", ownerDid, resultTimeoutMs: 60_000 },
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
