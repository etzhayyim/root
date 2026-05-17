import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 56 — 10 more Wikidata profiles: subwayStation / seaport / borough /
 * hamletWd / neighborhood / publicSquare / skiResort / cityPark /
 * shoppingCenter / policeStationWd. All selected for known dense P625
 * coord coverage (avoided the 0-row outcome from Phase 51's narrow QIDs).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  // [profileKey, label, worldTotal, priority]
  const seed: Array<[string, string, number, number]> = [
    ["subwayStation",  "Station",     20_000, 0.7],
    ["seaport",        "Port",         2_000, 0.7],
    ["borough",        "AdminArea",   15_000, 0.6],
    ["hamletWd",       "Spot",       200_000, 0.5],
    ["neighborhood",   "AdminArea",  100_000, 0.6],
    ["publicSquare",   "Spot",        30_000, 0.6],
    ["skiResort",      "Spot",         5_000, 0.7],
    ["cityPark",       "Spot",        50_000, 0.6],
    ["shoppingCenter", "Spot",        30_000, 0.6],
    ["policeStationWd","Spot",        20_000, 0.6],
  ];
  for (const [key, label, worldTotal, priority] of seed) {
    const sourceDid = `did:web:maps.etzhayyim.com:registry:wikidata:${key}`;
    const vid = `at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-${key}:${label}`;
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
