import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * UDF: route `:eonet*` → 'eonet', `:opensky*` → 'opensky'.
 * Seed: 1 EONET (plus 3 EONET category variants) + 1 OpenSky frontier.
 *
 * EONET covers ~500 open natural events globally (wildfires / storms /
 * volcanoes / seaLakeIce / etc). OpenSky live aircraft ADS-B, bbox
 * filtered — new "Aircraft" label (not Spot).
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
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikivoyage'           THEN 'wikivoyage'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:wikivoyage:%'         THEN 'wikivoyage'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:commons'              THEN 'commons'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:commons:%'            THEN 'commons'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:inaturalist'          THEN 'inaturalist'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:inaturalist:%'        THEN 'inaturalist'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gbif'                 THEN 'gbif'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gbif:%'               THEN 'gbif'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:eonet'                THEN 'eonet'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:eonet:%'              THEN 'eonet'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:opensky'              THEN 'opensky'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:opensky:%'            THEN 'opensky'
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
    // EONET — 1 general + 3 category variants
    ["did:web:maps.etzhayyim.com:eonet",            "SpatialEvent",    500, 0.6, 6.0],   // fast TTL, real-time events
    ["did:web:maps.etzhayyim.com:eonet:wildfires",  "SpatialEvent",    300, 0.6, 6.0],
    ["did:web:maps.etzhayyim.com:eonet:severeStorms","SpatialEvent",    50, 0.6, 6.0],
    ["did:web:maps.etzhayyim.com:eonet:volcanoes",  "SpatialEvent",     50, 0.6, 6.0],
    // OpenSky aircraft — new Aircraft label, volatile TTL
    ["did:web:maps.etzhayyim.com:opensky",          "Aircraft",     15_000, 0.6, 1.0],   // ~15K aircraft in air globally
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
