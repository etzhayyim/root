CREATE VIEW IF NOT EXISTS view_naics_industry AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'         AS name,
      value_json::jsonb->>'level'        AS level,
      value_json::jsonb->>'code'         AS original_code,
      value_json::jsonb->>'parent'       AS parent_code,
      value_json::jsonb->>'edition'      AS edition,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.naics.industry';

CREATE VIEW IF NOT EXISTS view_isic5_activity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'parent' AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.open_isic.economic_activity_rev5';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('naics', 'naics.etzhayyim.com', 2125, 'industries', 'industry');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('isic5', 'isic5.etzhayyim.com', 830, 'industries', 'governance');
