// Seed BPMN actor row for the aircraft registry backfill (Phase 3).
// F5 watcher (30s) reads + deploys to Zeebe.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-05-05T18:31:00Z";
const ownerDid = "did:web:maps.etzhayyim.com";
const actorId = "sys.bpmn.seed.maps-aircraft-phase3";

const seed = {
  processVertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/maps-backfillAircraftRegistry-v1",
  bindingVertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/maps-backfillAircraftRegistry-v1",
  processId: "maps_backfill_aircraft_registry",
  nsid: "app.etzhayyim.apps.maps.backfillAircraftRegistry",
  sourcePath: "00-contracts/bpmn/ai/gftd/maps/backfillAircraftRegistry.bpmn",
  resultTimeoutMs: 1_800_000,
  writeTableAllowlist: "vertex_aircraft,edge_aircraft_state_for_aircraft",
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
