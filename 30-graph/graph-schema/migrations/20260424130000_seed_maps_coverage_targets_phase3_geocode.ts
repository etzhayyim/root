import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 3 coverage target seed — adds path-variant sub-DIDs observed in
 * live vertex_spatial but absent from the phase 1/2 seed.
 *
 * Root cause: the Worker's geocoder and heartbeat scheduler write to
 * `did:web:maps.etzhayyim.com:geocode` (for Airport / Port resolved via geocode)
 * and `:weather` (for WeatherPoint), but the phase 1/2 frontier only had
 * `:infrastructure:Airport` — so 120+ existing rows never counted toward
 * the Airport frontier.
 *
 * This migration adds the observed variants so refreshCoverageStats
 * captures them immediately. Adding a row here is cheap (1 INSERT); the
 * canonical MV `mv_maps_collected_per_source_label_canonical` already
 * aggregates them.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    // source_did, label, world_total, priority_weight, ttl_hours
    ["did:web:maps.etzhayyim.com:geocode",        "Airport",      3_000,   1.0, 168.0],  // merges with infrastructure/Airport logically
    ["did:web:maps.etzhayyim.com:geocode",        "Port",         5_000,   1.0, 168.0],
    ["did:web:maps.etzhayyim.com:geocode",        "Station",     10_000,   0.6, 168.0],
    ["did:web:maps.etzhayyim.com:weather",        "WeatherPoint", 50_000,  0.3, 1.0],     // fast TTL (1h) — heartbeat refreshes
    ["did:web:maps.etzhayyim.com:infrastructure", "InfraSegment", 1_000_000, 0.3, 720.0],
    ["did:web:maps.etzhayyim.com:infrastructure", "CollectionJob", 100_000, 0.1, 720.0],  // own jobs; low priority
  ];

  for (const [sourceDid, label, worldTotal, priority, ttl] of seed) {
    const sourceSlug = sourceDid.replace(/^did:web:maps\.etzhayyim\.ai:?/, "") || "primary";
    const vid = `at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/${sourceSlug.replace(/[.:]/g, "-")}:${label}`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${sourceDid}, ${label}, ${worldTotal}, ${priority},
        ${ttl}, 'anon', 'anon', ${sourceDid}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Rolled back via phase-1 table drop.
}
