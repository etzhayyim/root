DROP VIEW IF EXISTS view_hs2012_commodity;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.hs.commodity2012';

DELETE FROM dim_world_domain WHERE domain = 'hs2012';
