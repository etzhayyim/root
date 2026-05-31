import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 74 — 10 sports/nature/tourism Wikidata profiles.
 * footballStadium / canyon / orchard / wetland / atoll / themePark /
 * hotSpringWd / waterpark / fortress / iceberg.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number]> = [
    ["footballStadium","Spot",     20_000, 0.7],
    ["canyon",         "Spot",      5_000, 0.6],
    ["orchard",        "Farmland", 20_000, 0.6],
    ["wetland",        "Spot",     20_000, 0.6],
    ["atoll",          "Spot",      2_000, 0.7],
    ["themePark",      "Spot",      1_000, 0.7],
    ["hotSpringWd",    "Spot",      5_000, 0.6],
    ["waterpark",      "Spot",      2_000, 0.7],
    ["fortress",       "Spot",     10_000, 0.6],
    ["iceberg",        "Spot",      1_500, 0.5],
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
