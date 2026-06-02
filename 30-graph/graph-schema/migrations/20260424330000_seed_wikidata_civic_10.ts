import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 51 — 10 new Wikidata civic/education/religion profiles. Pairs with
 * Phase 48 Overpass filters. Wikidata coverage catches entities registered
 * in Wikidata with P625 coords but missing from OSM (historical /
 * off-region / brand-authoritative).
 *
 * Worker-side WIKIDATA_PROFILES entries added in the same deploy; source_did
 * suffix ≡ profile key.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  // [profileKey, worldTotal, priority]
  const seed: Array<[string, number, number]> = [
    ["parliamentBldg",  2_000, 0.7],
    ["primarySchool", 500_000, 0.6],
    ["middleSchool",  200_000, 0.6],
    ["highSchoolWd",  300_000, 0.6],
    ["boardingSchool",  8_000, 0.6],
    ["prisonWd",       25_000, 0.6],
    ["gurdwara",       10_000, 0.6],
    ["aquariumWd",      1_000, 0.7],
    ["botanicalGarden", 3_000, 0.7],
    ["basilica",        3_000, 0.6],
  ];
  for (const [key, worldTotal, priority] of seed) {
    const sourceDid = `did:web:maps.etzhayyim.com:registry:wikidata:${key}`;
    const vid = `at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata-${key}:Spot`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${sourceDid}, 'Spot', ${worldTotal}, ${priority},
        168.0, 'anon', 'anon', ${sourceDid}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Rolled back via phase-1 table drop.
}
