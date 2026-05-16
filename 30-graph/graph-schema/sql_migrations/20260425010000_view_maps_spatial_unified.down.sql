DROP VIEW IF EXISTS view_maps_spatial_unified;

UPDATE vertex_maps_coverage_target
       SET priority_weight = 0.6
     WHERE source_did = 'did:web:maps.gftd.ai:registry:gleif';
