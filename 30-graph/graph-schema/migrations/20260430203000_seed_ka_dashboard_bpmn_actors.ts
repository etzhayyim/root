import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:ka.etzhayyim.com";
const createdAt = "2026-04-30T20:30:00+09:00";
const actorId = "sys.bpmn.seed.ka-dashboard";

const seeds: Seed[] = [
  { slug: "get-dashboard", op: "getDashboard", processId: "ka_get_dashboard" },
  { slug: "get-goals", op: "getGoals", processId: "ka_get_goals" },
  { slug: "get-actions", op: "getActions", processId: "ka_get_actions" },
  { slug: "get-revenue", op: "getRevenue", processId: "ka_get_revenue" },
  { slug: "get-burn", op: "getBurn", processId: "ka_get_burn" },
  { slug: "get-risks", op: "getRisks", processId: "ka_get_risks" },
  { slug: "get-cases", op: "getCases", processId: "ka_get_cases" },
  { slug: "get-kpi", op: "getKpi", processId: "ka_get_kpi" },
  { slug: "get-projects", op: "getProjects", processId: "ka_get_projects" },
  { slug: "get-infra", op: "getInfra", processId: "ka_get_infra" },
  { slug: "get-milestones", op: "getMilestones", processId: "ka_get_milestones" },
  { slug: "get-snapshots", op: "getSnapshots", processId: "ka_get_snapshots" },
  { slug: "get-topo", op: "getTopo", processId: "ka_get_topo" },
  { slug: "get-inbox", op: "getInbox", processId: "ka_get_inbox" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/ka/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/ka-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/ka-${s.op}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${`app.etzhayyim.apps.ka.${s.op}`}, ${s.processId}, 1,
        30000, '', 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
