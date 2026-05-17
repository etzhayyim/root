import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 75 — 5 sports/education WD profiles.
 * baseballStadium / velodromeWd / publicLibrary / kindergartenWd /
 * cricketGround. High-confidence QIDs.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, number, number]> = [
    ["baseballStadium", 10_000, 0.7],
    ["velodromeWd",      1_000, 0.7],
    ["publicLibrary",   60_000, 0.6],
    ["kindergartenWd", 200_000, 0.6],
    ["cricketGround",   15_000, 0.7],
  ];
  for (const [key, worldTotal, priority] of seed) {
    const sourceDid = `did:web:maps.etzhayyim.com:registry:wikidata:${key}`;
    const vid = `at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/registry-wikidata-${key}:Spot`;
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
