import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; nsid: string; processId: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:k3t5g0r1.etzhayyim.com";
const createdAt = "2026-04-30T21:11:00+09:00";
const actorId = "sys.bpmn.seed.kami-ketsu-gorilla";

const seeds: Seed[] = [
  { slug: "submit-score", op: "submitScore", nsid: "app.etzhayyim.apps.kami.ketsuGorilla.submitScore", processId: "kami_ketsu_gorilla_submit_score", timeoutMs: 30000, writeTableAllowlist: "vertex_atrecord_kami_ketsu_gorilla_score" },
  { slug: "get-leaderboard", op: "getLeaderboard", nsid: "app.etzhayyim.apps.kami.ketsuGorilla.getLeaderboard", processId: "kami_ketsu_gorilla_get_leaderboard", timeoutMs: 30000, writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/kamiKetsuGorilla/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-ketsu-gorilla-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-ketsu-gorilla-${s.op}-v1`;

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
        ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
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
