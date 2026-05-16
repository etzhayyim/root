DROP VIEW IF EXISTS view_iso639_language;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.iso639.language';

DELETE FROM dim_world_domain WHERE domain = 'iso639';

DELETE FROM edge_classified_as WHERE system = 'iso3166_m49';
