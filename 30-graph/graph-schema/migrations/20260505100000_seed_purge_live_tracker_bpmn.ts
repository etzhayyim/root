// Seed BPMN actor row for the live tracker purge job.
// F5 watcher reads this row + deploys to Zeebe.
//
// 1 process_def + 1 lexicon_binding row. Mirror of the live tracker
// seed migration (20260501180200_seed_live_tracker_bpmn.ts).

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-05-05T10:00:00Z";
const ownerDid = "did:web:maps.gftd.ai";
const actorId = "sys.bpmn.seed.maps-purge-live-tracker";

const seed = {
  processVertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-purgeStaleLiveTracker-v1",
  bindingVertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-purgeStaleLiveTracker-v1",
  processId: "maps_purge_stale_live_tracker",
  nsid: "ai.gftd.apps.maps.purgeStaleLiveTracker",
  sourcePath: "00-contracts/bpmn/ai/gftd/maps/purgeStaleLiveTracker.bpmn",
  resultTimeoutMs: 300_000,
  // Allow generic.db.delete to touch all 3 live tracker tables.
  writeTableAllowlist: "vertex_aircraft_state,vertex_satellite_pass,vertex_satellite_tle",
};

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(seed.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT ${seed.processVertexId}, ${ownerDid}, ${seed.processId}, 1, ${xml},
           CAST(${size} AS integer), ${seed.sourcePath}, 'active', ${createdAt},
           1, ${ownerDid}, ${ownerDid}, ${actorId}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.processVertexId}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
       write_table_allowlist, status, created_at, sensitivity_ord,
       org_id, user_id, actor_id, actor_did, org_did)
    SELECT ${seed.bindingVertexId}, ${ownerDid}, ${seed.nsid}, ${seed.processId}, 1,
           CAST(${seed.resultTimeoutMs} AS integer), ${seed.writeTableAllowlist},
           'active', ${createdAt}, 1,
           ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = ${seed.processVertexId}`.execute(db);
}
