import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * UDF: route `:seismic:*` suffix to 'seismic' (mirrors the :satellite:* and
 * :wikidata:* pattern). Seeds 7 more Wikipedia languages + 4 seismic variants.
 *
 * Wikipedia total geotagged articles by language (rough):
 *   de 1.5M / fr 1.2M / it 700K / zh 800K / ru 900K / ar 300K / pt 600K
 *
 * Seismic variants share USGS GeoJSON schema but different window/filter:
 *   week / month — bigger recent windows
 *   sig_month    — significant quakes last 30 days
 *   m6           — M≥6 from 4.5_month (high-impact filter)
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
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:gleif'       THEN 'gleif'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata'    THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:wikidata:%'  THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:registry:%'           THEN 'registry_other'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikipedia'            THEN 'wikipedia'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikipedia:%'          THEN 'wikipedia'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite'            THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:satellite:%'          THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic'              THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic:%'            THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:street_view'          THEN 'mapillary'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:infrastructure'       THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:geocode'              THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:weather'              THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gtfs'                 THEN 'gtfs'
        WHEN source_did LIKE 'did:web:site.etzhayyim.com'                      THEN 'web_crawl'
        ELSE 'unsupported'
      END
    $$
  `.execute(db);

  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number, number]> = [
    // 7 Wikipedia languages
    ["did:web:maps.etzhayyim.com:wikipedia:de", "Spot",    1_500_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:fr", "Spot",    1_200_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:it", "Spot",      700_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:zh", "Spot",      800_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ru", "Spot",      900_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:ar", "Spot",      300_000, 0.6, 168.0],
    ["did:web:maps.etzhayyim.com:wikipedia:pt", "Spot",      600_000, 0.6, 168.0],
    // 4 seismic variants
    ["did:web:maps.etzhayyim.com:seismic:week",      "SpatialEvent", 20_000, 0.3, 1.0],
    ["did:web:maps.etzhayyim.com:seismic:month",     "SpatialEvent", 100_000, 0.3, 24.0],
    ["did:web:maps.etzhayyim.com:seismic:sig_month", "SpatialEvent",    100, 0.6, 24.0],
    ["did:web:maps.etzhayyim.com:seismic:m6",        "SpatialEvent",    500, 0.6, 24.0],
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
