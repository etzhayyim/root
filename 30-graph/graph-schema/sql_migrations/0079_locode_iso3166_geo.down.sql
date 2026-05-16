DROP VIEW IF EXISTS view_locode_location;

DROP VIEW IF EXISTS view_iso3166_country;

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.locode.location';

DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.iso3166.country';

DELETE FROM dim_world_domain WHERE domain IN ('locode','iso3166');

DELETE FROM edge_classified_as WHERE system IN ('sovereign_m49','iso3166_sovereign');
