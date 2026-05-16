CREATE VIEW IF NOT EXISTS view_atc_substance AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'parent' AS parent_code,
      value_json::jsonb->>'ddd'    AS ddd,
      value_json::jsonb->>'uom'    AS uom,
      value_json::jsonb->>'adm_r'  AS adm_r,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.atc.substance';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('atc', 'atc.gftd.ai', 6440, 'drug substances', 'pharma');
