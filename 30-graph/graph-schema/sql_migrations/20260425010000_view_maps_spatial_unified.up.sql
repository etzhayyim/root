DROP VIEW IF EXISTS view_maps_spatial_unified;

CREATE VIEW view_maps_spatial_unified AS
    SELECT
      vertex_id,
      name,
      label,
      lat,
      lng AS lon,
      source_did,
      'vertex_spatial' AS origin
    FROM vertex_spatial
    UNION ALL
    SELECT
      vertex_id,
      name,
      'LegalEntity'::varchar AS label,
      NULL::real AS lat,
      NULL::real AS lon,
      'did:web:legal-entity.etzhayyim.com'::varchar AS source_did,
      'vertex_legal_entity'::varchar AS origin
    FROM vertex_legal_entity
    UNION ALL
    SELECT
      vertex_id,
      name,
      'Hotel'::varchar AS label,
      lat,
      lon,
      'did:web:hospitality.etzhayyim.com'::varchar AS source_did,
      'vertex_accommodation'::varchar AS origin
    FROM vertex_accommodation;

UPDATE vertex_maps_coverage_target
       SET priority_weight = 0.0
     WHERE source_did = 'did:web:maps.etzhayyim.com:registry:gleif';

FLUSH;
