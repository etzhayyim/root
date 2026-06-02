DROP VIEW IF EXISTS view_hs2007_commodity;

DROP VIEW IF EXISTS view_hs2002_commodity;

DROP VIEW IF EXISTS view_hs1996_commodity;

DROP VIEW IF EXISTS view_sitc1_commodity;

DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.hs.commodity2007';

DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.hs.commodity2002';

DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.hs.commodity1996';

DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.sitc.commodity_rev1';

DELETE FROM dim_world_domain WHERE domain IN ('hs2007','hs2002','hs1996','sitc1');

DELETE FROM edge_classified_as WHERE system IN ('hs07_hs12','hs02_hs07','hs96_hs02','sitc1_sitc2');
