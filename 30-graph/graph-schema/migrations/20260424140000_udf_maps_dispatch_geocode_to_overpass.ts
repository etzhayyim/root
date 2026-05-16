import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Extend maps_source_dispatch_kind to route `did:web:maps.gftd.ai:geocode`
 * (Airport / Port / Station from the geocoder sub-DID) through the
 * 'overpass' path — the same handler covers both OSM infra and geocoded
 * POIs. Observed failure: phase-3 seed rows (geocode:Airport, geocode:Port)
 * hit 'unsupported' and got 0 rows ingested.
 *
 * This replaces the UDF defined in 20260424110000. SQL functions in RW
 * don't support CREATE OR REPLACE, so DROP + re-CREATE.
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
        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:gleif'    THEN 'gleif'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:wikidata' THEN 'wikidata'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:%'        THEN 'registry_other'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:satellite'         THEN 'stac'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:seismic'           THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:street_view'       THEN 'mapillary'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:infrastructure'    THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:geocode'           THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:weather'           THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.gftd.ai:gtfs'              THEN 'gtfs'
        WHEN source_did LIKE 'did:web:site.gftd.ai'                   THEN 'web_crawl'
        ELSE 'unsupported'
      END
    $$
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)`.execute(db);
  // Reapply previous version from 20260424110000 if needed.
}
