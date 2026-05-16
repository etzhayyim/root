DROP VIEW IF EXISTS view_atc_substance;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.atc.substance';

DELETE FROM dim_world_domain WHERE domain = 'atc';
