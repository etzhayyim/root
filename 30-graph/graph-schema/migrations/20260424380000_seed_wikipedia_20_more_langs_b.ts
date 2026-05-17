import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 63 — 20 more Wikipedia languages. Continuation of Phase 54's
 * migration-only pattern (runWikipedia handles any `:{lang}` suffix).
 *
 * Picks: tt (Tatar 300K), min (Minangkabau 250K), tg (Tajik 250K), ast
 * (Asturian 100K), mg (Malagasy 95K), ky (Kyrgyz 80K), lmo (Lombard 70K),
 * pms (Piedmontese 65K), ba (Bashkir 60K), fy (Frisian 50K), an (Aragonese
 * 40K), ckb (Central Kurdish 40K), bar (Bavarian 35K), scn (Sicilian 25K),
 * gd (Scottish Gaelic 15K), yi (Yiddish 15K), wa (Walloon 15K), ha (Hausa
 * 10K), mi (Maori 10K), mt (Maltese 5K).
 *
 * With existing 77 langs (Phase 28 + 47 + 54) → 97 total, ~97% of
 * geotagged Wikipedia article population.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, number]> = [
    ["tt",  300_000],
    ["min", 250_000],
    ["tg",  250_000],
    ["ast", 100_000],
    ["mg",   95_000],
    ["ky",   80_000],
    ["lmo",  70_000],
    ["pms",  65_000],
    ["ba",   60_000],
    ["fy",   50_000],
    ["an",   40_000],
    ["ckb",  40_000],
    ["bar",  35_000],
    ["scn",  25_000],
    ["gd",   15_000],
    ["yi",   15_000],
    ["wa",   15_000],
    ["ha",   10_000],
    ["mi",   10_000],
    ["mt",    5_000],
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
