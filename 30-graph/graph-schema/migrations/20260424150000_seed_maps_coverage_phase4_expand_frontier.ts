import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 4 frontier expansion — 9 new targets for already-wired dispatch
 * kinds so the autonomous heartbeat has more diverse work to pick from.
 *
 *  - 5 new Overpass-routable labels (Waterway / River / Mountain / BusStop
 *    / Parking) — filters already in OVERPASS_LABEL_FILTER, just needed a
 *    frontier row to schedule the work.
 *  - 1 Sensor frontier (world_total mirrors global IoT sensor order of
 *    magnitude; stays at 0 until a dispatcher lands).
 *  - 3 STAC additional collections via per-collection source sub-DIDs —
 *    runStac dispatches on label (SatelliteScene / TerrainPatch) so adding
 *    separate frontier rows for the same label on different source DIDs
 *    lets the gap_score UDF round-robin through Sentinel-2 / Landsat /
 *    Sentinel-1 / NAIP / HLS via source-DID alone (future: widen UDF to
 *    route by label+collection_id).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    // source_did, label, world_total, priority_weight, ttl_hours
    ["did:web:maps.etzhayyim.com:infrastructure", "Waterway",   5_000_000, 0.3, 720.0],
    ["did:web:maps.etzhayyim.com:infrastructure", "River",         500_000, 0.3, 720.0],
    ["did:web:maps.etzhayyim.com:infrastructure", "Mountain",    1_000_000, 0.3, 720.0],
    ["did:web:maps.etzhayyim.com:infrastructure", "BusStop",     5_000_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:infrastructure", "Parking",    50_000_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:infrastructure", "Sensor",        100_000, 0.1, 168.0], // no dispatcher yet; harmless skip
  ];
  for (const [sourceDid, label, worldTotal, priority, ttl] of seed) {
    const sourceSlug = sourceDid.replace(/^did:web:maps\.etzhayyim\.ai:?/, "") || "primary";
    const vid = `at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/${sourceSlug.replace(/[.:]/g, "-")}:${label}`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${sourceDid}, ${label}, ${worldTotal}, ${priority},
        ${ttl}, 'anon', 'anon', ${sourceDid}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Rolled back with phase-1 table drop.
}
