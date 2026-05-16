import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0056 — move resource-flow write procedures behind BPMN/pyzeebe.
// projectFlow / reviewAnomaly remain ADR-0036-compliant Hyperdrive writes,
// but the edge Worker is now only a dispatcher facade for those commands.

type Seed = { proc: string; bpmnProcessId: string; nsid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-05-06T03:00:00Z";
const ownerDid = "did:web:resource-flow.gftd.ai";
const actorTag = "sys.bpmn.seed.resource-flow-project-review";
// bpmn-coverage gate marker: project: "resource-flow"
const project = "resource-flow";

const seeds: Seed[] = [
  {
    proc: "projectFlow",
    bpmnProcessId: "resource_flow_project_flow",
    nsid: "ai.gftd.apps.resourceFlow.projectFlow",
    resultTimeoutMs: 60000,
  },
  {
    proc: "reviewAnomaly",
    bpmnProcessId: "resource_flow_review_anomaly",
    nsid: "ai.gftd.apps.resourceFlow.reviewAnomaly",
    resultTimeoutMs: 60000,
  },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/${project}/${s.proc}.bpmn`;
const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${project}-${slug(s.proc)}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${project}-${s.proc}-v1`;

async function upsertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const rel = sourcePath(s);
  const xml = readContract(rel);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    ) VALUES (
      ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${rel}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    )
  `.execute(db);
}

async function upsertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    ) VALUES (
      ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
      CAST(${s.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await upsertProcessDef(db, s);
  for (const s of seeds) await upsertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
  }
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
