// ADR-2604271600 — projector L7 BPMN seed.
//
// Registers the four projector BPMN process definitions and their
// lexicon bindings in vertex_bpmn_process_def + vertex_bpmn_lexicon_binding
// so the F5 watcher (`50-infra/.../bpmn-dispatcher`) deploys them to
// Zeebe and routes XRPC POSTs through dispatcher.etzhayyim.com:8080.
//
// Same shape as `20260427120100_seed_telecom_resource_bpmn_actors.ts`.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T16:00:00Z";
const ownerDid = "did:web:projector.etzhayyim.com";
const actorTag = "sys.bpmn.seed.projector";
const project = "projector";

const seeds: Seed[] = [
  {
    proc: "sendProjectMessage",
    bpmnProcessId: "projector_send_project_message",
    nsid: "app.etzhayyim.apps.projector.sendProjectMessage",
    resultTimeoutMs: 60_000,
  },
  {
    proc: "agentLoop",
    bpmnProcessId: "projector_agent_loop",
    nsid: "app.etzhayyim.apps.projector.agentLoop",
    resultTimeoutMs: 60_000,
  },
  {
    proc: "treeOfThoughts",
    bpmnProcessId: "projector_tree_of_thoughts",
    nsid: "app.etzhayyim.apps.projector.treeOfThoughts",
    resultTimeoutMs: 90_000,
  },
  {
    proc: "selfConsistency",
    bpmnProcessId: "projector_self_consistency",
    nsid: "app.etzhayyim.apps.projector.selfConsistency",
    resultTimeoutMs: 90_000,
  },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/${project}/${s.proc}.bpmn`;
const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${project}-${slug(s.proc)}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${project}-${s.proc}-v1`;

async function insertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const rel = sourcePath(s);
  const xml = readContract(rel);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${rel}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
      CAST(${s.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await insertProcessDef(db, s);
  for (const s of seeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
  }
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
