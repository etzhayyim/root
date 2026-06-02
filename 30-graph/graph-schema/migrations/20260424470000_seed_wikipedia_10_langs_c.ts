import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 76 — 10 more Wikipedia langs. Continuation of Phase 28/47/54/63.
 * Picks: eo Esperanto (400K — largest miss so far), am Amharic (15K),
 * io Ido (40K), xh Xhosa, zu Zulu, so Somali, ig Igbo, yo Yoruba, haw
 * Hawaiian, sah Sakha. With existing 97 → 107 total.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, number]> = [
    ["eo",  400_000],
    ["am",   15_000],
    ["io",   40_000],
    ["xh",    5_000],
    ["zu",    5_000],
    ["so",    5_000],
    ["ig",    8_000],
    ["yo",   15_000],
    ["haw",   2_000],
    ["sah",  15_000],
  ];
  for (const [lang, worldTotal] of seed) {
    const sourceDid = `did:web:maps.etzhayyim.com:wikipedia:${lang}`;
    const vid = `at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/wikipedia-${lang}:Spot`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${sourceDid}, 'Spot', ${worldTotal}, 0.4,
        168.0, 'anon', 'anon', ${sourceDid}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Rolled back via phase-1 table drop.
}
