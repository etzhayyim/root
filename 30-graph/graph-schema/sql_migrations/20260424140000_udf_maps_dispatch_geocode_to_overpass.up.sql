DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar);

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
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:seismic'           THEN 'seismic'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:street_view'       THEN 'mapillary'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:infrastructure'    THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:geocode'           THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:weather'           THEN 'overpass'
        WHEN source_did LIKE 'did:web:maps.etzhayyim.com:gtfs'              THEN 'gtfs'
        WHEN source_did LIKE 'did:web:site.etzhayyim.com'                   THEN 'web_crawl'
        ELSE 'unsupported'
      END
    $$;
