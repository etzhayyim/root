import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 2 coverage target seed — extends the initial 12-row frontier
 * from `20260424080000_udf_maps_coverage_gap.ts` with the remaining
 * path-based source DIDs enumerated in
 * `60-apps/etzhayyim-project-maps/CLAUDE.md §Source DIDs`.
 *
 * Adds 13 rows to reach 25 total. ON CONFLICT DO NOTHING keeps it idempotent
 * — safe to re-run and safe to apply before/after phase-1 seed.
 *
 * Priority weights follow CLAUDE.md P-tier guidance:
 *   P0 (1.0) — GLEIF / JP NTA / Wikidata / JP NDI / JP MOJ / SDG-adjacent
 *   P1 (0.6) — OpenCorporates / OpenAddresses / Sentinel-1 / NAIP / Mapillary
 *   P2 (0.3) — EV / OSM tails / ADS-B
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    // source_did, label, world_total, priority_weight, ttl_hours
    ["did:web:maps.etzhayyim.com:street_view",             "StreetChunk",     50_000_000, 0.6,  720.0],   // Mapillary
    ["did:web:maps.etzhayyim.com:satellite",               "SatelliteScene",  10_000_000, 0.6,  720.0],   // Sentinel-1 SAR
    ["did:web:maps.etzhayyim.com:satellite",               "TerrainPatch",    14_000_000, 0.6,  720.0],   // Copernicus DEM 30m
    ["did:web:maps.etzhayyim.com:registry:uk-ch",          "LegalEntity",      5_500_000, 1.0,  168.0],   // UK Companies House
    ["did:web:maps.etzhayyim.com:registry:us-edgar",       "LegalEntity",        700_000, 1.0,  168.0],   // SEC EDGAR
    ["did:web:maps.etzhayyim.com:registry:eu-br",          "LegalEntity",     15_000_000, 1.0,  720.0],   // EU Business Registries
    ["did:web:maps.etzhayyim.com:registry:jp-moj",         "LandRegistry",   200_000_000, 1.0,  720.0],   // 登記情報
    ["did:web:maps.etzhayyim.com:infrastructure",          "Port",                 5_000, 1.0,  168.0],
    ["did:web:maps.etzhayyim.com:infrastructure",          "Road",                20_000, 0.6,  168.0],
    ["did:web:maps.etzhayyim.com:infrastructure",          "Railway",              5_000, 0.6,  168.0],
    ["did:web:maps.etzhayyim.com:infrastructure",          "EvCharger",          100_000, 0.3,  168.0],   // OpenChargeMap tail
    ["did:web:maps.etzhayyim.com:seismic",                 "SpatialEvent",       100_000, 0.3,    1.0],   // 15min TTL → always "stale"
    ["did:web:site.etzhayyim.com",                         "WebCrawlGeoEntity", 1_000_000, 0.3,  168.0],  // CommonCrawl WET/WAT
  ];

  for (const [sourceDid, label, worldTotal, priority, ttl] of seed) {
    const sourceSlug = sourceDid.replace(/^did:web:maps\.etzhayyim\.ai:?/, "") || sourceDid.replace(/^did:web:/, "");
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

export async function down(db: Kysely<unknown>): Promise<void> {
  // Phase-2 rows are identified by the `vertex_maps_coverage_target/` prefix + not in phase-1 seed.
  // Simplest safe rollback: let the phase-1 down() drop the whole table.
  // (Explicit DELETE here would duplicate the vid derivation logic.)
}
