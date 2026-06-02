import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * shinshi.etzhayyim.com gap-fill autonomous backfill BPMN.
 *
 * Adds 1 timer-start (R/PT4H) BPMN that scans for shinshi models with
 * fewer than 5 image scenes and triggers `shinshi.scene.bulkSeed` to
 * fill the gap. No XRPC binding (timer-only). The bulk seed primitive
 * caps internally at 3 slugs/run, so this loop drains ~1,000 partial
 * models in ~2 months without operator touch.
 *
 * Coverage gap motivating this BPMN (2026-05-07):
 *   1,650 models = 57 zero-scene + 1,036 partial (1-4) + 557 complete (5+).
 *   Bulk seed peak (4,181 posts/day) ran 2026-04-24..04-26 then stopped.
 *
 * F5 watcher (dispatcher_main.py) auto-deploys this row to Zeebe within
 * the next ~30s tick after migration apply.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-07T15:00:00Z";
const ownerDid = "did:web:shinshi.etzhayyim.com";
const actorTag = "sys.bpmn.seed.shinshi.gap-fill";

const processSeeds: P[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shinshi-seed-gap-fill-v1",
    bpmnProcessId: "shinshi_seed_gap_fill",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/shinshi/seedGapFill.bpmn",
    ownerDid,
  },
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

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
