CREATE VIEW IF NOT EXISTS view_hs2012_commodity AS
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
    WHERE collection = 'ai.gftd.apps.hs.commodity2012';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs2012', 'hs2012.etzhayyim.com', 6529, 'products', 'trade');

DELETE FROM edge_classified_as WHERE system = 'sitc4' AND code IN ('I','II');

DELETE FROM edge_classified_as
    WHERE system = 'cpc' AND dst_vid LIKE '%/n/a';
