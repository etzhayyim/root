DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar);

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
        WHEN source_did LIKE 'did:web:maps.gftd.ai:gtfs'              THEN 'gtfs'
        WHEN source_did LIKE 'did:web:site.gftd.ai'                   THEN 'web_crawl'
        ELSE 'unsupported'
      END
    $$;
