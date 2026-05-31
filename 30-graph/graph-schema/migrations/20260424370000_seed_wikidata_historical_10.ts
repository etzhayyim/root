import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 59 — 10 historical/military/civic Wikidata profiles:
 * battlefield / conventionCtr / musicSchool / airForceBase / busStationWd /
 * microbrewery / cityGate / bunker / arsenal / farmersMarket.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  // [profileKey, label, worldTotal, priority]
  const seed: Array<[string, string, number, number]> = [
    ["battlefield",   "Spot",    20_000, 0.6],
    ["conventionCtr", "Spot",     5_000, 0.7],
    ["musicSchool",   "Spot",    10_000, 0.6],
    ["airForceBase",  "Spot",     2_000, 0.7],
    ["busStationWd",  "Station", 50_000, 0.6],
    ["microbrewery",  "Spot",    30_000, 0.6],
    ["cityGate",      "Spot",     5_000, 0.7],
    ["bunker",        "Spot",    30_000, 0.6],
    ["arsenal",       "Spot",     3_000, 0.7],
    ["farmersMarket", "Spot",    20_000, 0.6],
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
