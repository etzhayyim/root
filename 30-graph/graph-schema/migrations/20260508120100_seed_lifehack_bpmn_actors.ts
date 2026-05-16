import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * lifehack.gftd.ai BPMN-as-actor seeding (ADR-0056 + ADR-2604282300).
 *
 * 8 BPMN process defs + 6 XRPC bindings.  No CF Worker (T2 tier:
 * pymagatama + Zeebe only).  3 timer-start BPMNs are autonomous;
 * 6 XRPC bindings are reachable via bpmn-dispatcher
 * `http://dispatcher.gftd.ai:8080/xrpc/ai.gftd.apps.lifehack.*`.
 *
 *  Process / NSID                                Trigger
 *  ---------------------------------------------------------------------
 *  lifehack_research_topic   (none, autonomous)  R/PT24H
 *  lifehack_daily_dust_post  ai.gftd.apps.lifehack.dailyDustPost +
 *                            cron 0 0 0 * * ?  (00:00 UTC = 09:00 JST)
 *  lifehack_static_alert     (none, autonomous)  R/PT6H
 *  lifehack_submit_tip       ai.gftd.apps.lifehack.submitTip
 *  lifehack_recommend        ai.gftd.apps.lifehack.recommend
 *  lifehack_agent_loop       ai.gftd.apps.lifehack.agentLoop
 *  lifehack_submit_environment_reading
 *                            ai.gftd.apps.lifehack.submitEnvironmentReading
 *  lifehack_coverage         ai.gftd.apps.lifehack.coverage
 *
 * The listTips / listProducts queries are intentionally schema-only in
 * Phase 1 — wire later via `generic.db.select` BPMNs.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T12:00:00Z";
const ownerDid = "did:web:lifehack.gftd.ai";
const actorTag = "sys.bpmn.seed.lifehack";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lifehack-research-topic-v1",
    bpmnProcessId: "lifehack_research_topic",
    sourcePath: "00-contracts/bpmn/ai/gftd/lifehack/researchTopic.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lifehack-daily-dust-post-v1",
    bpmnProcessId: "lifehack_daily_dust_post",
    sourcePath: "00-contracts/bpmn/ai/gftd/lifehack/dailyDustPost.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lifehack-static-alert-v1",
    bpmnProcessId: "lifehack_static_alert",
    sourcePath: "00-contracts/bpmn/ai/gftd/lifehack/staticAlert.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lifehack-submit-tip-v1",
    bpmnProcessId: "lifehack_submit_tip",
    sourcePath: "00-contracts/bpmn/ai/gftd/lifehack/submitTip.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lifehack-recommend-v1",
    bpmnProcessId: "lifehack_recommend",
    sourcePath: "00-contracts/bpmn/ai/gftd/lifehack/recommend.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lifehack-agent-loop-v1",
    bpmnProcessId: "lifehack_agent_loop",
    sourcePath: "00-contracts/bpmn/ai/gftd/lifehack/agentLoop.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lifehack-submit-environment-reading-v1",
    bpmnProcessId: "lifehack_submit_environment_reading",
    sourcePath: "00-contracts/bpmn/ai/gftd/lifehack/submitEnvironmentReading.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lifehack-coverage-v1",
    bpmnProcessId: "lifehack_coverage",
    sourcePath: "00-contracts/bpmn/ai/gftd/lifehack/coverage.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lifehack-dailyDustPost-v1",
    nsid: "ai.gftd.apps.lifehack.dailyDustPost",
    bpmnProcessId: "lifehack_daily_dust_post", ownerDid, resultTimeoutMs: 60_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lifehack-submitTip-v1",
    nsid: "ai.gftd.apps.lifehack.submitTip",
    bpmnProcessId: "lifehack_submit_tip", ownerDid, resultTimeoutMs: 60_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lifehack-recommend-v1",
    nsid: "ai.gftd.apps.lifehack.recommend",
    bpmnProcessId: "lifehack_recommend", ownerDid, resultTimeoutMs: 30_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lifehack-agentLoop-v1",
    nsid: "ai.gftd.apps.lifehack.agentLoop",
    bpmnProcessId: "lifehack_agent_loop", ownerDid, resultTimeoutMs: 60_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lifehack-submitEnvironmentReading-v1",
    nsid: "ai.gftd.apps.lifehack.submitEnvironmentReading",
    bpmnProcessId: "lifehack_submit_environment_reading", ownerDid, resultTimeoutMs: 15_000 },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lifehack-coverage-v1",
    nsid: "ai.gftd.apps.lifehack.coverage",
    bpmnProcessId: "lifehack_coverage", ownerDid, resultTimeoutMs: 15_000 },
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
