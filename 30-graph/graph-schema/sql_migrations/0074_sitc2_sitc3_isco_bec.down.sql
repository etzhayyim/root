DROP VIEW IF EXISTS view_sitc3_commodity;

DROP VIEW IF EXISTS view_sitc2_commodity;

DROP VIEW IF EXISTS view_isco_occupation;

DROP VIEW IF EXISTS view_bec_category;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.sitc.commodity_rev3';

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.sitc.commodity_rev2';

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.isco.occupation';

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.bec.category';

DELETE FROM dim_world_domain WHERE domain IN ('sitc3','sitc2','isco','bec');

DELETE FROM edge_classified_as WHERE system IN ('sitc3_sitc4','sitc2_sitc3','sitc2_sitc4');
