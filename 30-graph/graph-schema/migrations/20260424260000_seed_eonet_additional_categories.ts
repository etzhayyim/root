import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed 5 more EONET category variants (seaLakeIce / snow / dustHaze /
 * tempExtremes / earthquakes). runEonet already routes via source_did
 * suffix, so just adding frontier rows is sufficient.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    ["did:web:maps.etzhayyim.com:eonet:seaLakeIce",    "SpatialEvent", 50, 0.3, 6.0],
    ["did:web:maps.etzhayyim.com:eonet:snow",          "SpatialEvent", 20, 0.3, 6.0],
    ["did:web:maps.etzhayyim.com:eonet:dustHaze",      "SpatialEvent", 30, 0.3, 6.0],
    ["did:web:maps.etzhayyim.com:eonet:tempExtremes",  "SpatialEvent", 20, 0.3, 6.0],
    ["did:web:maps.etzhayyim.com:eonet:earthquakes",   "SpatialEvent", 100, 0.3, 6.0],
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
