// Seed BPMN actor rows for the maps live tracker pipeline (Flightradar24 +
// N2YO equivalent). F5 watcher (30s) reads these rows and deploys to Zeebe.
//
// 4 process_def rows + 4 lexicon_binding rows.
// Mirror of 20260501150000_seed_market_internet_demand_poll_bpmn.ts.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-05-01T17:00:00Z";
const ownerDid = "did:web:maps.etzhayyim.com";
const actorId = "sys.bpmn.seed.maps-live-tracker";

interface BpmnSeed {
  processVertexId: string;
  bindingVertexId: string;
  processId: string;
  nsid: string;
  sourcePath: string;
  resultTimeoutMs: number;
  writeTableAllowlist: string;
}

const seeds: BpmnSeed[] = [
  {
    processVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-liveTrackAircraft-v1",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/maps-liveTrackAircraft-v1",
    processId: "maps_live_track_aircraft",
    nsid: "com.etzhayyim.apps.maps.liveTrackAircraft",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/maps/liveTrackAircraft.bpmn",
    resultTimeoutMs: 30_000,
    writeTableAllowlist: "vertex_aircraft_state",
  },
  {
    processVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-computeAircraftTrack-v1",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/maps-computeAircraftTrack-v1",
    processId: "maps_compute_aircraft_track",
    nsid: "com.etzhayyim.apps.maps.computeAircraftTrack",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/maps/computeAircraftTrack.bpmn",
    resultTimeoutMs: 120_000,
    writeTableAllowlist: "vertex_aircraft_track",
  },
  {
    processVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-refreshTleCatalog-v1",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/maps-refreshTleCatalog-v1",
    processId: "maps_refresh_tle_catalog",
    nsid: "com.etzhayyim.apps.maps.refreshTleCatalog",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/maps/refreshTleCatalog.bpmn",
    resultTimeoutMs: 300_000,
    writeTableAllowlist: "vertex_satellite_tle",
  },
  {
    processVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-precomputeSatellitePasses-v1",
    bindingVertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/maps-precomputeSatellitePasses-v1",
    processId: "maps_precompute_satellite_passes",
    nsid: "com.etzhayyim.apps.maps.precomputeSatellitePasses",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/maps/precomputeSatellitePasses.bpmn",
    resultTimeoutMs: 600_000,
    writeTableAllowlist: "vertex_satellite_pass",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readContract(s.sourcePath);
    const size = Buffer.byteLength(xml, "utf8");

    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${s.processVertexId}, ${ownerDid}, ${s.processId}, 1, ${xml},
             CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt},
             1, ${ownerDid}, ${ownerDid}, ${actorId}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.processVertexId}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
         write_table_allowlist, status, created_at, sensitivity_ord,
         org_id, user_id, actor_id, actor_did, org_did)
      SELECT ${s.bindingVertexId}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
             CAST(${s.resultTimeoutMs} AS integer), ${s.writeTableAllowlist},
             'active', ${createdAt}, 1,
             ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.bindingVertexId}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.bindingVertexId}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = ${s.processVertexId}`.execute(db);
  }
}
