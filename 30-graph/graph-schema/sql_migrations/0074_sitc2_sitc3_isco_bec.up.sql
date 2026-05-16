CREATE VIEW IF NOT EXISTS view_sitc3_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.sitc.commodity_rev3';

CREATE VIEW IF NOT EXISTS view_sitc2_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.sitc.commodity_rev2';

CREATE VIEW IF NOT EXISTS view_isco_occupation AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'major'    AS major,
      value_json::jsonb->>'submajor' AS submajor,
      value_json::jsonb->>'minor'    AS minor,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.isco.occupation';

CREATE VIEW IF NOT EXISTS view_bec_category AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'parent' AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.bec.category';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sitc3', 'sitc3.gftd.ai', 5690, 'products', 'trade');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sitc2', 'sitc2.gftd.ai', 3723, 'products', 'trade');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('isco', 'isco.gftd.ai', 393, 'occupations', 'labour');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('bec', 'bec.gftd.ai', 31, 'categories', 'trade');

DELETE FROM edge_classified_as WHERE system = 'sitc3_sitc4';

DELETE FROM edge_classified_as WHERE system = 'sitc2_sitc3';

DELETE FROM edge_classified_as WHERE system = 'sitc2_sitc4';
