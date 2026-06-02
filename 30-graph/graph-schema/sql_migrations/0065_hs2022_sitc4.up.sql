CREATE VIEW IF NOT EXISTS view_hs2022_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.hs.commodity2022';

CREATE VIEW IF NOT EXISTS view_sitc_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'parent'   AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.sitc.commodity';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs2022', 'hs2022.etzhayyim.com', 6939, 'products', 'trade');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sitc', 'sitc.etzhayyim.com', 5484, 'products', 'trade');
