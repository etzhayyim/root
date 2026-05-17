import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 81 — rebase world_total for near-saturation targets.
 *
 * Current state (iter 80 telemetry):
 *   eonet:volcanoes  45/50   = 90.0%  → real upper bound ~1500 active+dormant
 *   eonet:seaLakeIce 30/50   = 60.0%  → real upper bound ~200 active events
 *   eonet:wildfires  100/300 = 33.3%  → 1500 (FIRMS reports thousands/day)
 *   museumShip       98/300  = 32.7%  → 500 (maritime registries list more)
 *
 * Near-saturation coverage pushes gap_score → 0, drops targets from
 * frontier rotation. Rebasing keeps them in active pick cycle while
 * remaining honest about catalog size.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const bumps: Array<[string, number]> = [
    ["did:web:maps.etzhayyim.com:eonet:volcanoes",                     1500],
    ["did:web:maps.etzhayyim.com:eonet:seaLakeIce",                    200],
    ["did:web:maps.etzhayyim.com:eonet:wildfires",                     1500],
    ["did:web:maps.etzhayyim.com:registry:wikidata:museumShip",        500],
  ];
  for (const [sd, wt] of bumps) {
    await sql`UPDATE vertex_maps_coverage_target SET world_total = ${wt} WHERE source_did = ${sd}`.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op: rebasing is a monotonic correction.
}
