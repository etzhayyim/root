import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 71 — 10 more maritime/academic/urban Wikidata profiles.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number]> = [
    ["maritimeStrait", "Spot", 2_000,  0.7],
    ["archipelago",    "Spot", 5_000,  0.6],
    ["peninsulaWd",    "Spot", 10_000, 0.6],
    ["capeWd",         "Spot", 20_000, 0.6],
    ["lagoon",         "Lake", 5_000,  0.6],
    ["estuary",        "Spot", 10_000, 0.6],
    ["researchInst",   "Spot", 30_000, 0.7],
    ["scientificLab",  "Spot", 10_000, 0.6],
    ["artistStudio",   "Spot", 5_000,  0.6],
    ["observatory2",   "Spot", 5_000,  0.6],
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
