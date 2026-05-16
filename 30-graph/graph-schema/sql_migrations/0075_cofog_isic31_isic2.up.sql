CREATE VIEW IF NOT EXISTS view_cofog_function AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.cofog.function';

CREATE VIEW IF NOT EXISTS view_isic31_activity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'group'    AS group_code,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.open_isic.economic_activity_rev31';

CREATE VIEW IF NOT EXISTS view_isic2_activity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'group'    AS group_code,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.open_isic.economic_activity_rev2';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('cofog', 'cofog.gftd.ai', 188, 'government functions', 'governance');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('isic31', 'isic31.gftd.ai', 538, 'industries', 'governance');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('isic2', 'isic2.gftd.ai', 277, 'industries', 'governance');

DELETE FROM edge_classified_as WHERE system = 'isic31_isic4';

DELETE FROM edge_classified_as WHERE system = 'isic31_isic5';

DELETE FROM edge_classified_as WHERE system = 'isic2_isic31';
