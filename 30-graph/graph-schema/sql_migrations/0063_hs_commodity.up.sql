CREATE VIEW IF NOT EXISTS view_hs_commodity AS
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
    WHERE collection = 'com.etzhayyim.apps.hs.commodity';

UPDATE dim_world_domain SET world_total = 6705 WHERE domain = 'hs';
