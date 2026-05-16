DROP VIEW IF EXISTS view_isic_activity;

DROP VIEW IF EXISTS view_cpc_product;

DROP TABLE IF EXISTS vertex_shohin;

UPDATE dim_world_domain SET world_total = 2738 WHERE domain = 'cpc';

UPDATE dim_world_domain SET world_total = 419  WHERE domain = 'isic';

DELETE FROM dim_world_domain WHERE domain = 'hs';
