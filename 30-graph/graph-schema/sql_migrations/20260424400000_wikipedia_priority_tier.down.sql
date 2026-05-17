UPDATE vertex_maps_coverage_target
       SET priority_weight = 0.6
     WHERE source_did LIKE 'did:web:maps.etzhayyim.com:wikipedia:%'
       AND priority_weight = 0.35;

FLUSH;
