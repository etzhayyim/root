import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed 30 more Wikipedia language frontier rows. `runWikipedia` already
 * routes any `did:web:maps.gftd.ai:wikipedia:<lang>` via source_did suffix,
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
    ["did:web:maps.gftd.ai:wikipedia:simple", "Spot", 150_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:ml",     "Spot",  90_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:ta",     "Spot", 200_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:te",     "Spot",  80_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:kn",     "Spot",  35_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:mr",     "Spot",  90_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:gu",     "Spot",  30_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:pa",     "Spot",  45_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:ur",     "Spot", 210_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:fa",     "Spot", 900_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:uz",     "Spot", 220_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:ka",     "Spot", 170_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:my",     "Spot", 120_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:km",     "Spot",  12_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:si",     "Spot",  24_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:ne",     "Spot",  35_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:jv",     "Spot",  75_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:su",     "Spot",  65_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:ms",     "Spot", 370_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:mn",     "Spot",  22_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:mk",     "Spot", 140_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:sr",     "Spot", 670_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:hr",     "Spot", 220_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:sl",     "Spot", 180_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:lv",     "Spot", 115_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:lt",     "Spot", 210_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:et",     "Spot", 225_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:is",     "Spot",  55_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:ga",     "Spot",  58_000, 0.6, 168.0],
    ["did:web:maps.gftd.ai:wikipedia:cy",     "Spot", 160_000, 0.6, 168.0],
  ];
  for (const [sourceDid, label, worldTotal, priority, ttl] of seed) {
    const sourceSlug = sourceDid.replace(/^did:web:maps\.gftd\.ai:?/, "") || "primary";
    const vid = `at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/${sourceSlug.replace(/[.:]/g, "-")}:${label}`;
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
