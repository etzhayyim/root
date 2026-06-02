CREATE VIEW IF NOT EXISTS view_nace_activity AS
    SELECT
      rkey AS nace_code,
      value_json::jsonb->>'name'       AS name,
      value_json::jsonb->>'level'      AS level,
      value_json::jsonb->>'isic4_code' AS isic4_code,
      value_json::jsonb->>'parent'     AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.nace.activity';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('nace', 'nace.etzhayyim.com', 997, 'industries', 'governance');

DELETE FROM edge_classified_as WHERE system = 'nace_r2';
