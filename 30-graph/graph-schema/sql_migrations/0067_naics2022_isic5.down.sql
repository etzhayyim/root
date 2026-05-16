DROP VIEW IF EXISTS view_isic5_activity;

DROP VIEW IF EXISTS view_naics_industry;

DELETE FROM dim_world_domain WHERE domain = 'naics';

DELETE FROM dim_world_domain WHERE domain = 'isic5';
