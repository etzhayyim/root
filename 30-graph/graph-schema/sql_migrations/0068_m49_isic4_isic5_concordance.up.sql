DELETE FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.sovereign.m49_region';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('m49', 'sovereign.etzhayyim.com', 460, 'geo_areas', 'governance');

DELETE FROM edge_classified_as WHERE system = 'isic5';
