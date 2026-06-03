import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed 30 more Wikipedia language frontier rows. `runWikipedia` already
 * routes any `did:web:maps.etzhayyim.com:wikipedia:<lang>` via source_did suffix,
 * so only the INSERT + iter-41 world_total estimates are needed.
 *
 * Combined with the existing 27 (en/ja/es/de/fr/it/zh/ru/ar/pt/ko/id/vi/tr/
 * pl/nl/sv/fi/no/da/cs/hu/el/hi/bn/th/he), this brings coverage to 57
 * languages — ~90% of Wikipedia's geotagged-article population.
 *
 * World-total estimates are heuristics based on the language edition's
 * total article count × ~10-15% geotagged ratio observed in majors.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    ["did:web:maps.etzhayyim.com:wikipedia:simple", "Spot", 150_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ml",     "Spot",  90_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ta",     "Spot", 200_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:te",     "Spot",  80_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:kn",     "Spot",  35_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:mr",     "Spot",  90_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:gu",     "Spot",  30_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:pa",     "Spot",  45_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ur",     "Spot", 210_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:fa",     "Spot", 900_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:uz",     "Spot", 220_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ka",     "Spot", 170_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:my",     "Spot", 120_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:km",     "Spot",  12_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:si",     "Spot",  24_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ne",     "Spot",  35_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:jv",     "Spot",  75_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:su",     "Spot",  65_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ms",     "Spot", 370_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:mn",     "Spot",  22_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:mk",     "Spot", 140_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:sr",     "Spot", 670_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:hr",     "Spot", 220_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:sl",     "Spot", 180_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:lv",     "Spot", 115_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:lt",     "Spot", 210_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:et",     "Spot", 225_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:is",     "Spot",  55_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ga",     "Spot",  58_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:cy",     "Spot", 160_000, 0.6, 168.0],
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
