DELETE FROM edge_classified_as WHERE system = 'cpc3';

DELETE FROM edge_classified_as WHERE system = 'naics_isic4';

DROP VIEW IF EXISTS view_cpc3_product;

DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.cpc.commodity_item_v3';

DELETE FROM dim_world_domain WHERE domain = 'cpc3';
