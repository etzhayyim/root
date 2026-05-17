import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 79 — 3 more OSM Notes coverage targets. Dispatcher uses the same
 * OpenStreetMap notes.json API but different source_did suffixes so the
 * advance UDF treats them as independent frontier entries. Each gets its
 * own bbox cycle via cyclicBboxIdx(job.job_id), multiplying effective
 * region coverage.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, number, number]> = [
    ["osm_notes:eu",     40_000, 0.7],
    ["osm_notes:us",     30_000, 0.7],
    ["osm_notes:global", 30_000, 0.6],
  ];
  for (const [suffix, worldTotal, priority] of seed) {
    const sourceDid = `did:web:maps.etzhayyim.com:${suffix}`;
    const vid = `at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/${suffix.replace(/:/g, "-")}:Spot`;
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
