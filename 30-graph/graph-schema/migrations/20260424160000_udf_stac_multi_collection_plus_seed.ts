import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Extend maps_source_dispatch_kind so `did:web:maps.etzhayyim.com:satellite:*`
 * (per-STAC-collection sub-DIDs) also route to 'stac', and seed 9 new
 * frontier rows (4 STAC collections + 5 dense POI labels).
 *
 * STAC collections (via source_did suffix):
 *   satellite:sentinel2 → sentinel-2-l2a   (optical 10m)
 *   satellite:landsat   → landsat-c2l2-sr  (optical 30m)
 *   satellite:sentinel1 → sentinel-1-grd   (SAR)
 *   satellite:naip      → naip             (US aerial)
 *
 * (hls merged into sentinel2/landsat above.)
 *
 * Dense POI labels under infrastructure:
 *   Hospital / School / Museum / Cafe / Restaurant
 * (Overpass filters added in collection-commands.ts.)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)`.execute(db);
  await sql`
    CREATE FUNCTION maps_source_dispatch_kind(
      source_did varchar,
      label      varchar
    ) RETURNS varchar
    LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:gleif'    THEN 'gleif'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata' THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:%'        THEN 'registry_other'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite'         THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite:%'       THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic'           THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:street_view'       THEN 'mapillary'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:infrastructure'    THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:geocode'           THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:weather'           THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gtfs'              THEN 'gtfs'
        WHEN source_did LIKE 'did:web:site.etzhayyim.com'                   THEN 'web_crawl'
        ELSE 'unsupported'
      END
    $$
  `.execute(db);

  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    // STAC per-collection frontier rows
    ["did:web:maps.etzhayyim.com:satellite:sentinel2", "SatelliteScene",  5_000_000, 0.6, 720.0],
    ["did:web:maps.etzhayyim.com:satellite:landsat",   "SatelliteScene",  2_000_000, 0.6, 720.0],
    ["did:web:maps.etzhayyim.com:satellite:sentinel1", "SatelliteScene",  1_500_000, 0.6, 720.0],
    ["did:web:maps.etzhayyim.com:satellite:naip",      "SatelliteScene",    500_000, 0.3, 720.0],
    // Dense POI labels — named-label path, high-yield on city bboxes
    ["did:web:maps.etzhayyim.com:infrastructure",      "Hospital",          150_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:infrastructure",      "School",          1_000_000, 0.3, 168.0],
    ["did:web:maps.etzhayyim.com:infrastructure",      "Museum",             50_000, 0.3, 720.0],
    ["did:web:maps.etzhayyim.com:infrastructure",      "Cafe",            3_000_000, 0.1, 168.0],
    ["did:web:maps.etzhayyim.com:infrastructure",      "Restaurant",      5_000_000, 0.1, 168.0],
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

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)`.execute(db);
}
