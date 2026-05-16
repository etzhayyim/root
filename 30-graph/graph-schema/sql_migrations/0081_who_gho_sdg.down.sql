DROP VIEW IF EXISTS view_who_gho_indicator;

DROP VIEW IF EXISTS view_sdg_indicator;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.who.gho_indicator';

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.sdg.indicator';

DELETE FROM dim_world_domain WHERE domain IN ('who_gho','sdg');
