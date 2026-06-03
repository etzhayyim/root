import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed 10 more Wikivoyage languages — runWikivoyage already routes by
 * source_did suffix, so adding frontier rows is enough. Estimated
 * articles per language (en dominates at ~30K, others 5K-10K).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    ["did:web:maps.etzhayyim.com:wikivoyage:es", "Spot",  8_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:it", "Spot",  7_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:pt", "Spot",  5_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:nl", "Spot",  6_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:ru", "Spot", 10_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:zh", "Spot",  5_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:ja", "Spot",  5_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:pl", "Spot",  6_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:sv", "Spot",  4_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:uk", "Spot",  3_000, 0.3, 168.0],
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
  // Rolled back with phase-1 table drop.
}
