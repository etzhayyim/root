DROP VIEW IF EXISTS view_cofog_function;

DROP VIEW IF EXISTS view_isic31_activity;

DROP VIEW IF EXISTS view_isic2_activity;

DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.cofog.function';

DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.open_isic.economic_activity_rev31';

DELETE FROM vertex_repo_record WHERE collection = 'com.etzhayyim.apps.open_isic.economic_activity_rev2';

DELETE FROM dim_world_domain WHERE domain IN ('cofog','isic31','isic2');

DELETE FROM edge_classified_as WHERE system IN ('isic31_isic4','isic31_isic5','isic2_isic31');
