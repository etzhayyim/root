CREATE VIEW IF NOT EXISTS view_cpc3_product AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'group'    AS group_code,
      value_json::jsonb->>'class'    AS class_code,
      value_json::jsonb->>'parent'   AS parent_code,
      value_json::jsonb->>'change'   AS change_type,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.cpc.commodity_item_v3';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('cpc3', 'cpc3.etzhayyim.com', 4594, 'products', 'commerce');

DELETE FROM edge_classified_as WHERE system = 'cpc3';

DELETE FROM edge_classified_as WHERE system = 'naics_isic4';
