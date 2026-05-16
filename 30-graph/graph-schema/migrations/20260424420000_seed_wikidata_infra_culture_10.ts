import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 68 — 10 more infrastructure/culture/transport Wikidata profiles:
 * waterTreatment / sewageTreatment / navalBase / operaHouse / concertHall /
 * restAreaWd / tollPlaza / lighthouseWd2 / miningSite / museumShip.
 * Pattern matches Phase 56/59 (dense QIDs to avoid zero-row tier).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, number, number]> = [
    ["waterTreatment",  10_000, 0.6],
    ["sewageTreatment", 10_000, 0.6],
    ["navalBase",          500, 0.7],
    ["operaHouse",       1_500, 0.7],
    ["concertHall",      5_000, 0.7],
    ["restAreaWd",      20_000, 0.6],
    ["tollPlaza",       10_000, 0.6],
    ["lighthouseWd2",    5_000, 0.6],
    ["miningSite",      30_000, 0.6],
    ["museumShip",         300, 0.7],
  ];
  for (const [key, worldTotal, priority] of seed) {
    const sourceDid = `did:web:maps.gftd.ai:registry:wikidata:${key}`;
    const vid = `at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/registry-wikidata-${key}:Spot`;
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
