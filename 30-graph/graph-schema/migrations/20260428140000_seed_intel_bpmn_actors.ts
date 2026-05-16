// ADR-0056 — intel BPMN actor seed.
//
// Registers 6 intel processes in vertex_bpmn_process_def +
// vertex_bpmn_lexicon_binding so the F5 watcher deploys them
// to Zeebe and dispatcher.gftd.ai routes XRPC POSTs.
//
// Workers: intel-pyzeebe-worker (50-infra/k8s/intel-dependency-worker)
// handles all intel.* task types. Pod is already Running in the
// intel namespace and polling — RESOURCE_EXHAUSTED errors resolve
// once these processes are deployed to Zeebe.
//
// 6 processes:
//   resolveEntity           — intel.run.create → intel.entity.resolve → intel.langgraph.resolve
//   listDependencyCandidates — intel.run.create → intel.dependency.list → intel.candidate.scan
//   inferDependencies       — intel.run.create → intel.dependency.list → intel.edge.materialize
//   explainDependency       — intel.run.create → intel.dependency.explain → intel.owl.validate
//   getCounterpartyGraph    — intel.run.create → intel.graph.counterparty → intel.edge.materialize
//   getBuildingOwnershipGraph — intel.run.create → intel.graph.buildingOwnership → intel.edge.materialize

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
const createdAt = "2026-04-28T14:00:00Z";
const ownerDid = "did:web:intel.gftd.ai";
const actorTag = "sys.bpmn.seed.intel";
const project = "intel";

const seeds: Seed[] = [
  {
    proc: "resolveEntity",
    bpmnProcessId: "intel_resolve_entity",
    nsid: "ai.gftd.apps.intel.resolveEntity",
    resultTimeoutMs: 60_000,
  },
  {
    proc: "listDependencyCandidates",
    bpmnProcessId: "intel_list_dependency_candidates",
    nsid: "ai.gftd.apps.intel.listDependencyCandidates",
    resultTimeoutMs: 30_000,
  },
  {
    proc: "inferDependencies",
    bpmnProcessId: "intel_infer_dependencies",
    nsid: "ai.gftd.apps.intel.inferDependencies",
    resultTimeoutMs: 60_000,
  },
  {
    proc: "explainDependency",
    bpmnProcessId: "intel_explain_dependency",
    nsid: "ai.gftd.apps.intel.explainDependency",
    resultTimeoutMs: 60_000,
  },
  {
    proc: "getCounterpartyGraph",
    bpmnProcessId: "intel_get_counterparty_graph",
    nsid: "ai.gftd.apps.intel.getCounterpartyGraph",
    resultTimeoutMs: 60_000,
  },
  {
    proc: "getBuildingOwnershipGraph",
    bpmnProcessId: "intel_get_building_ownership_graph",
    nsid: "ai.gftd.apps.intel.getBuildingOwnershipGraph",
    resultTimeoutMs: 60_000,
  },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/${project}/${s.proc}.bpmn`;
const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${project}-${slug(s.proc)}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${project}-${s.proc}-v1`;

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
