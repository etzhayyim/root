// Phase B of the live.etzhayyim.com L4 actor migration.
//
// Registers three single-task BPMN flows + their lexicon bindings so
// `dispatcher.etzhayyim.com/xrpc/ai.gftd.apps.live.{postChat,scheduleSet,
// sendCheer}` calls can land directly without going through the
// `magatama-l1ve9pq4` Worker. Each binding maps the NSID to the
// matching BPMN process_id; pyzeebe / Zeebe gateway picks up the
// instance, runs `generic.db.insert` into the corresponding
// vertex_live_* table from the migration in 20260429000000, then
// emits a `generic.audit.emit` for postChat / scheduleSet.
//
// The companion `apps/live/showFlow.bpmn` is **not** registered here
// because it has no XRPC entry — it's driven by a cron / heartbeat
// trigger to fan out actorJoin + actorComment over a roster.
//
// Driving NSIDs that stay on the L3 worker (no binding):
//   ai.gftd.apps.live.joinRoom        — query, reads the DO state
//   ai.gftd.apps.live.getCurrentSet   — query, reads the DO state
//   ai.gftd.apps.live.actorJoin       — handled inside showFlow.bpmn
//   ai.gftd.apps.live.postChat        — registered here ✓
//   ai.gftd.apps.live.scheduleSet     — registered here ✓
//   ai.gftd.apps.live.sendCheer       — registered here ✓
//
// After this migration applies + dispatcher.etzhayyim.com picks up the
// `vertex_bpmn_lexicon_binding` rows (typically a few seconds), the
// dispatcher returns 200 for the three NSIDs above without the live
// Worker being in the path.

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
const createdAt = "2026-04-29T01:00:00Z";
const ownerDid = "did:web:live.etzhayyim.com";
const actorTag = "sys.bpmn.seed.live";
// bpmn-coverage gate marker: project: "apps/live"
const project = "apps/live";

const seeds: Seed[] = [
  {
    proc: "postChat",
    bpmnProcessId: "live_post_chat",
    nsid: "ai.gftd.apps.live.postChat",
    resultTimeoutMs: 5_000,
  },
  {
    proc: "scheduleSet",
    bpmnProcessId: "live_schedule_set",
    nsid: "ai.gftd.apps.live.scheduleSet",
    resultTimeoutMs: 10_000,
  },
  {
    proc: "sendCheer",
    bpmnProcessId: "live_send_cheer",
    nsid: "ai.gftd.apps.live.sendCheer",
    resultTimeoutMs: 5_000,
  },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/${project}/${s.proc}.bpmn`;
const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const projectKey = project.replace(/\//g, "-");
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/${projectKey}-${slug(s.proc)}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${projectKey}-${s.proc}-v1`;

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
