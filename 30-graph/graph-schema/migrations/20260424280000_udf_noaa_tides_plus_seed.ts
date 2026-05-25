import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * UDF: route `:noaa_tides*` → 'noaa_tides'. Seed 1 frontier row.
 * NOAA CO-OPS tide/current stations — ~3K globally, mostly US coasts.
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
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:noaa_tides'           THEN 'noaa_tides'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:noaa_tides:%'         THEN 'noaa_tides'
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
  await sql`
    INSERT INTO vertex_maps_coverage_target (
      vertex_id, source_did, label, world_total, priority_weight,
      ttl_hours, org_id, user_id, actor_id, created_at
    ) VALUES (
      'at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/noaa_tides:Station',
      'did:web:maps.etzhayyim.com:noaa_tides', 'Station', 3000, 0.6, 168.0,
      'anon', 'anon', 'did:web:maps.etzhayyim.com:noaa_tides', ${now}
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)`.execute(db);
}
