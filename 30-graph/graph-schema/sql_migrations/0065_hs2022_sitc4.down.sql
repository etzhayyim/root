DROP VIEW IF EXISTS view_sitc_commodity;

DROP VIEW IF EXISTS view_hs2022_commodity;

DELETE FROM dim_world_domain WHERE domain = 'hs2022';

DELETE FROM dim_world_domain WHERE domain = 'sitc';
