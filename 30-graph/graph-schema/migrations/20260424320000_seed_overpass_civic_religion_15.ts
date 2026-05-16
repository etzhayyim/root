import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed 15 new Overpass civic/education/religion/amenity coverage targets
 * (Phase 48). Every mid-size city has these → high yield per Overpass call.
 * All share source_did = `did:web:maps.gftd.ai:infrastructure` which the
 * dispatch UDF routes to Overpass; label determines the Overpass filter.
 *
 * Productivity factor defaults to NULL (= 1.0), so new rows compete on
 * equal footing until their first run sets last_rows_written.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const source = "did:web:maps.gftd.ai:infrastructure";
  // [label, world_total_estimate]
  const seed: Array<[string, number]> = [
    ["University",     30_000],
    ["College",        60_000],
    ["TownHall",      100_000],
    ["Courthouse",     15_000],
    ["Embassy",         3_500],
    ["FerryTerminal",   4_500],
    ["Toilets",     2_000_000],
    ["FastFood",    1_200_000],
    ["Bar",         1_500_000],
    ["Nightclub",      80_000],
    ["Church",        500_000],
    ["BuddhistTemple", 80_000],
    ["Shrine",         80_000],
    ["HinduTemple",    50_000],
    ["SikhTemple",     10_000],
  ];
  for (const [label, worldTotal] of seed) {
    const vid = `at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/infrastructure:${label}`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${source}, ${label}, ${worldTotal}, 0.6,
        168.0, 'anon', 'anon', ${source}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Rolled back via phase-1 table drop.
}
