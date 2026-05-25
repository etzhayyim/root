import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 86 — 5 more specialty WD profiles.
 * powerLineWd / radioAntenna / fishingHarbor / artificialIsland /
 * amusementRideWd.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number]> = [
    ["powerLineWd",      "PowerLine", 20_000, 0.6],
    ["radioAntenna",     "Spot",       5_000, 0.6],
    ["fishingHarbor",    "Port",       3_000, 0.7],
    ["artificialIsland", "Spot",       1_500, 0.7],
    ["amusementRideWd",  "Spot",       5_000, 0.6],
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
