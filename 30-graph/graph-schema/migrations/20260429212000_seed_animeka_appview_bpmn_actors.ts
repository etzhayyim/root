import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; processId: string; nsid: string; file: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:animeka.gftd.ai";
const createdAt = "2026-04-29T21:20:00+09:00";
const actorId = "sys.bpmn.seed.animeka-appview";
const project = "animeka";

const seeds: Seed[] = [
  { slug: "create-work", processId: "animeka_create_work", nsid: "ai.gftd.apps.animeka.createWork", file: "createWork.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_animeka" },
  { slug: "list-works", processId: "animeka_list_works", nsid: "ai.gftd.apps.animeka.listWorks", file: "listWorks.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "add-episode", processId: "animeka_add_episode", nsid: "ai.gftd.apps.animeka.addEpisode", file: "addEpisode.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_animeka" },
  { slug: "list-episodes", processId: "animeka_list_episodes", nsid: "ai.gftd.apps.animeka.listEpisodes", file: "listEpisodes.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "add-cut", processId: "animeka_add_cut", nsid: "ai.gftd.apps.animeka.addCut", file: "addCut.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_animeka" },
  { slug: "list-cuts", processId: "animeka_list_cuts", nsid: "ai.gftd.apps.animeka.listCuts", file: "listCuts.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "get-cut", processId: "animeka_get_cut", nsid: "ai.gftd.apps.animeka.getCut", file: "getCut.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "update-cut-stage", processId: "animeka_update_cut_stage", nsid: "ai.gftd.apps.animeka.updateCutStage", file: "updateCutStage.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_animeka" },
  { slug: "submit-retake", processId: "animeka_submit_retake", nsid: "ai.gftd.apps.animeka.submitRetake", file: "submitRetake.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_animeka" },
  { slug: "resolve-retake", processId: "animeka_resolve_retake", nsid: "ai.gftd.apps.animeka.resolveRetake", file: "resolveRetake.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_animeka" },
  { slug: "list-retakes", processId: "animeka_list_retakes", nsid: "ai.gftd.apps.animeka.listRetakes", file: "listRetakes.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "health", processId: "animeka_health", nsid: "ai.gftd.apps.animeka.health", file: "health.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
];

const processVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${project}-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${project}-${s.slug}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const sourcePath = `00-contracts/bpmn/ai/gftd/animeka/${s.file}`;
    const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${sourcePath}, 'active',
        ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorId},
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
        ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
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
