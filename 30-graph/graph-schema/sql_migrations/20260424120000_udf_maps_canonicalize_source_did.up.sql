DROP FUNCTION IF EXISTS maps_canonicalize_source_did(varchar);

CREATE FUNCTION maps_canonicalize_source_did(source_did varchar)
      RETURNS varchar
      LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN source_did LIKE 'did:web:uqpel6i6.gftd.ai:%'
          THEN 'did:web:maps.gftd.ai' || SUBSTRING(source_did FROM 25)
        WHEN source_did LIKE 'did:web:uqpel6i6:%'
          THEN 'did:web:maps.gftd.ai' || SUBSTRING(source_did FROM 17)
        WHEN source_did = 'did:web:uqpel6i6.gftd.ai'
          THEN 'did:web:maps.gftd.ai'
        WHEN source_did = 'did:web:uqpel6i6'
          THEN 'did:web:maps.gftd.ai'
        ELSE source_did
      END
    $$;

DROP MATERIALIZED VIEW IF EXISTS mv_maps_collected_per_source_label_canonical;

CREATE MATERIALIZED VIEW mv_maps_collected_per_source_label_canonical AS
    SELECT
      maps_canonicalize_source_did(source_did) AS source_did,
      label,
      COUNT(*)::bigint AS collected_count
    FROM vertex_spatial
    WHERE source_did IS NOT NULL AND label IS NOT NULL
    GROUP BY maps_canonicalize_source_did(source_did), label;
