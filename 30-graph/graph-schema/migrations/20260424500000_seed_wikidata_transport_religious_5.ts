import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 80 — 5 transport/religious niche WD profiles.
 * tramStop / monasteryWd / funeralHomeWd / crematoriumWd / ferryRouteWd.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number]> = [
    ["tramStop",      "Station", 50_000, 0.6],
    ["monasteryWd",   "Spot",    15_000, 0.7],
    ["funeralHomeWd", "Spot",    30_000, 0.5],
    ["crematoriumWd", "Spot",     5_000, 0.6],
    ["ferryRouteWd",  "Spot",     3_000, 0.6],
  ];
  for (const [key, label, worldTotal, priority] of seed) {
    const sourceDid = `did:web:maps.etzhayyim.com:registry:wikidata:${key}`;
    const vid = `at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-${key}:${label}`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${sourceDid}, ${label}, ${worldTotal}, ${priority},
        168.0, 'anon', 'anon', ${sourceDid}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Rolled back via phase-1 table drop.
}
