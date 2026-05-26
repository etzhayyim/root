/**
 * ADR-2605080600 Phase 4 — Seed webmk + newsletter BPMN process defs + bindings.
 *
 * webmk.createProposal → routing_target='langgraph' (assistant_id: webmk_create_proposal)
 * webmk.deliverProposal → routing_target='zeebe'  (Resend delivery, stays in Zeebe)
 * newsletter.sendCampaign → routing_target='zeebe'
 * newsletter.weeklySend  → timer-start, no binding needed
 */
import { type Kysely, sql } from "kysely";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const ownerDid = "did:web:bpmn.etzhayyim.com";
const actorTag = "did:web:bpmn.etzhayyim.com";
const createdAt = "2026-05-08T00:00:00Z";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readBpmn(sourcePath: string): string {
  return fs.readFileSync(path.resolve(repoRoot, sourcePath), "utf-8");
}

interface ProcessSeed {
  vertexId: string;
  ownerDid: string;
  bpmnProcessId: string;
  sourcePath: string;
  xml?: string;
}

interface BindingSeed {
  vertexId: string;
  ownerDid: string;
  nsid: string;
  bpmnProcessId: string;
  resultTimeoutMs: number;
  routingTarget: "langgraph" | "zeebe";
}

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/webmk-createProposal-v1",
    ownerDid,
    bpmnProcessId: "webmk_create_proposal",
    sourcePath: "00-contracts/bpmn/ai/gftd/webmk/createProposal.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/webmk-deliverProposal-v1",
    ownerDid,
    bpmnProcessId: "webmk_deliver_proposal",
    sourcePath: "00-contracts/bpmn/ai/gftd/webmk/deliverProposal.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/newsletter-sendCampaign-v1",
    ownerDid,
    bpmnProcessId: "newsletter_send_campaign",
    sourcePath: "00-contracts/bpmn/ai/gftd/newsletter/sendCampaign.bpmn",
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/webmk-createProposal-v1",
    ownerDid,
    nsid: "app.etzhayyim.apps.webmk.createProposal",
    bpmnProcessId: "webmk_create_proposal",
    resultTimeoutMs: 180_000,
    routingTarget: "langgraph",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/webmk-deliverProposal-v1",
    ownerDid,
    nsid: "app.etzhayyim.apps.webmk.deliverProposal",
    bpmnProcessId: "webmk_deliver_proposal",
    resultTimeoutMs: 60_000,
    routingTarget: "zeebe",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/newsletter-sendCampaign-v1",
    ownerDid,
    nsid: "app.etzhayyim.apps.newsletter.sendCampaign",
    bpmnProcessId: "newsletter_send_campaign",
    resultTimeoutMs: 60_000,
    routingTarget: "zeebe",
  },
];

async function insertProcessDef(db: Kysely<unknown>, s: ProcessSeed): Promise<void> {
  const xml = s.xml ?? readBpmn(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: BindingSeed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id, routing_target)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}, ${s.routingTarget}
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
