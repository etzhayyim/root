UPDATE vertex_maps_coverage_target
       SET priority_weight = 0.35
     WHERE source_did LIKE 'did:web:maps.etzhayyim.com:wikipedia:%'
       AND collected_count < 100;

FLUSH;
