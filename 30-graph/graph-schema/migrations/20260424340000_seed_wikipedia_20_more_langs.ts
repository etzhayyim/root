import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 54 — 20 more Wikipedia languages. `runWikipedia` dispatches by
 * source_did suffix so zero Worker code changes are needed.
 *
 * Picks: uk (Ukrainian 1.2M), ceb (Cebuano 6.1M — auto-gen wiki with
 * dense geotag coverage), war (Waray-Waray 1.3M, similar), ca/ro/bg/sk/eu/
 * gl (EU regional), la/vo (historic/artificial), af/sw/az/hy/kk/tl/lb/sq/
 * vec (global long-tail). With the existing 57 (27 Phase 28 + 30 Phase 47)
 * this brings coverage to 77 languages — ~95% of geotagged-article pop.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, number]> = [
    ["uk",  1_200_000],
    ["ceb", 6_100_000],
    ["war", 1_300_000],
    ["ca",    700_000],
    ["ro",    430_000],
    ["bg",    290_000],
    ["sk",    240_000],
    ["eu",    400_000],
    ["gl",    200_000],
    ["la",    140_000],
    ["vo",    120_000],
    ["af",    100_000],
    ["sw",     80_000],
    ["az",    200_000],
    ["hy",    290_000],
    ["kk",    240_000],
    ["tl",     45_000],
    ["lb",     60_000],
    ["sq",    100_000],
    ["vec",    70_000],
  ];
  for (const [lang, worldTotal] of seed) {
    const sourceDid = `did:web:maps.etzhayyim.com:wikipedia:${lang}`;
    const vid = `at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.coverageTarget/wikipedia-${lang}:Spot`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${sourceDid}, 'Spot', ${worldTotal}, 0.6,
        168.0, 'anon', 'anon', ${sourceDid}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Rolled back via phase-1 table drop.
}
