// ADR-2604301200 P2 — register the autonomous-agent runtime lease lifecycle BPMN.
//
// This is the dispatcher-facing entrypoint for:
//   ai.gftd.apps.agent.runtimeLeaseLifecycle
//
// The BPMN quotes CPU/memory/GPU/storage/egress cost, records a runtime lease,
// and optionally submits the GCC bond to AgentRuntimeLeaseEscrow when explicitly
// enabled. Runtime namespace defaults to yoro-actors and never to k8s default.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const createdAt = "2026-04-30T12:30:00Z";
const ownerDid = "did:web:agent.gftd.ai";
const actorTag = "sys.bpmn.seed.agent.runtimeLeaseLifecycle";

const procVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-runtime-lease-lifecycle-v1";
const bindingVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/agent-runtimeLeaseLifecycle-v1";
const sourcePath = "00-contracts/bpmn/ai/gftd/agent/runtimeLeaseLifecycle.bpmn";
const bpmnProcessId = "agent_runtime_lease_lifecycle";
const nsid = "ai.gftd.apps.agent.runtimeLeaseLifecycle";
const resultTimeoutMs = 90_000;

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${procVertexId}, ${ownerDid}, ${bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${procVertexId}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId}, ${ownerDid}, ${nsid}, ${bpmnProcessId}, 1,
      CAST(${resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${procVertexId}`.execute(db);
}
