CREATE VIEW IF NOT EXISTS view_who_gho_indicator AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'  AS name,
      value_json::jsonb->>'group' AS indicator_group,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.who.gho_indicator';

CREATE VIEW IF NOT EXISTS view_sdg_indicator AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'goal'   AS goal,
      value_json::jsonb->>'target' AS target,
      value_json::jsonb->>'tier'   AS tier,
      value_json::jsonb->>'parent' AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.sdg.indicator';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('who_gho', 'gho.gftd.ai', 3057, 'health indicators', 'healthcare');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sdg', 'sdg.gftd.ai', 251, 'SDG indicators', 'governance');
