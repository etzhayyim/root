import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed 10 more Wikivoyage language frontier rows (ro/he/ar/tr/uk/cs/sk/
 * fi/no/da). Trivial addition — runWikivoyage routes by source_did suffix,
 * so new langs go live as soon as the row exists in the table.
 *
 * Note for next iter: USGS NWIS water sites (https://waterservices.usgs.
 * gov/nwis/site/?format=rdb&bBox=...&seriesCatalogOutput=false) returns
 * ~1.7M US water monitoring sites. RDB format (pipe-delimited), zero auth.
 * Left as a TODO dispatcher for when coverage needs deeper US-only fill.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    ["did:web:maps.etzhayyim.com:wikivoyage:ro", "Spot", 2_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:he", "Spot", 2_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:ar", "Spot", 1_500, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:tr", "Spot", 2_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:uk", "Spot", 2_500, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:cs", "Spot", 2_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:sk", "Spot",   800, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:fi", "Spot", 1_500, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:no", "Spot", 1_500, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:wikivoyage:da", "Spot", 1_200, 0.3, 168.0],
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
