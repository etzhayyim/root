CREATE VIEW IF NOT EXISTS view_iso639_language AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'        AS name,
      value_json::jsonb->>'native_name' AS native_name,
      value_json::jsonb->>'family'      AS language_family,
      value_json::jsonb->>'iso639_2'    AS iso639_2_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.iso639.language';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('iso639', 'iso639.etzhayyim.com', 184, 'languages', 'culture');

DELETE FROM edge_classified_as WHERE system = 'iso3166_m49';
