import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * shosha.gftd.ai BPMN v2 — audit actor input fix.
 *
 * Phase 1 (2026-05-06) deployed all 8 shosha BPMN with audit task
 * passing only `eventType` + `attributes` to `generic.audit.emit`. The
 * task's signature requires `actor` (or `actor_did`) too — without it
 * the function returns `{"error":"actor and action required"}` and the
 * OCEL audit row never lands in `vertex_repo_commit`.
 *
 * Fix: each Task_Audit now also passes
 *   <zeebe:input source="=&quot;did:web:shosha.gftd.ai&quot;" target="actor"/>
 *
 * UPDATE in place + version bump + reset deployed_zeebe_key so the
 * F5 watcher in bpmn-dispatcher re-deploys to Zeebe on its next tick
 * (≤30s).  vertex_id stays at the v1 slug (immutable PK convention,
 * matches isbn precedent).
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const seeds: P[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-market-intelligence-ingest-v1",
    bpmnProcessId: "shosha_market_intelligence_ingest",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/marketIntelligenceIngest.bpmn" },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-trade-book-recompute-v1",
    bpmnProcessId: "shosha_trade_book_recompute",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/tradeBookRecompute.bpmn" },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-trade-idea-synthesize-v1",
    bpmnProcessId: "shosha_trade_idea_synthesize",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/tradeIdeaSynthesize.bpmn" },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-daily-report-v1",
    bpmnProcessId: "shosha_daily_report",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/dailyShoshaReport.bpmn" },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-submit-trade-v1",
    bpmnProcessId: "shosha_submit_trade",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/submitTrade.bpmn" },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-propose-hedge-v1",
    bpmnProcessId: "shosha_propose_hedge",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/proposeHedge.bpmn" },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-comply-check-v1",
    bpmnProcessId: "shosha_comply_check",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/complyCheck.bpmn" },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-agent-loop-v1",
    bpmnProcessId: "shosha_agent_loop",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/agentLoop.bpmn" },
];

async function updateProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  // RW SQL parser treats `xml` and `version` as reserved keywords; quote
  // every column for safety.
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml" = ${xml},
        "xml_byte_size" = CAST(${size} AS integer),
        "version" = 2,
        "deployed_zeebe_key" = NULL,
        "deployed_at" = NULL
    WHERE "vertex_id" = ${s.vertexId}
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await updateProcessDef(db, s);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op — v1 XML cannot be reconstructed without the original tree.
  // Phase 1 history is captured in git; rollback by checking out the
  // previous BPMN files and re-running this migration.
}
