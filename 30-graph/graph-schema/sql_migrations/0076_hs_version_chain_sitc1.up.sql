CREATE VIEW IF NOT EXISTS view_hs2007_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.hs.commodity2007';

CREATE VIEW IF NOT EXISTS view_hs2002_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.hs.commodity2002';

CREATE VIEW IF NOT EXISTS view_hs1996_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.hs.commodity1996';

CREATE VIEW IF NOT EXISTS view_sitc1_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.sitc.commodity_rev1';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs2007', 'hs2007.etzhayyim.com', 6373, 'HS products', 'trade');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs2002', 'hs2002.etzhayyim.com', 6569, 'HS products', 'trade');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs1996', 'hs1996.etzhayyim.com', 6474, 'HS products', 'trade');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sitc1', 'sitc1.etzhayyim.com', 2784, 'products', 'trade');

DELETE FROM edge_classified_as WHERE system = 'hs07_hs12';

DELETE FROM edge_classified_as WHERE system = 'hs02_hs07';

DELETE FROM edge_classified_as WHERE system = 'hs96_hs02';

DELETE FROM edge_classified_as WHERE system = 'sitc1_sitc2';
