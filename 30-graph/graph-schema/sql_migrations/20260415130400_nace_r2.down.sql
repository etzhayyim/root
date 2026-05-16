DELETE FROM edge_classified_as WHERE system = 'nace_r2';

DROP VIEW IF EXISTS view_nace_activity;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.nace.activity';

DELETE FROM dim_world_domain WHERE domain = 'nace';
