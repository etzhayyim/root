CREATE TABLE IF NOT EXISTS vertex_shohin (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      gtin               VARCHAR,
      name               VARCHAR,
      brand              VARCHAR,
      category           VARCHAR,
      cpc_code           VARCHAR,
      country_of_origin  VARCHAR,
      manufacturer       VARCHAR,
      currency           VARCHAR,
      price_amount       DOUBLE PRECISION,
      created_at         VARCHAR
    );

CREATE VIEW IF NOT EXISTS view_cpc_product AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'"group"'  AS group_code,
      value_json::jsonb->>'class'    AS class_code,
      value_json::jsonb->>'parent'   AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.cpc.commodity_item';

CREATE VIEW IF NOT EXISTS view_isic_activity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'parent' AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.open_isic.economic_activity';

UPDATE dim_world_domain SET world_total = 4596 WHERE domain = 'cpc';

UPDATE dim_world_domain SET world_total = 766  WHERE domain = 'isic';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs', 'hs.etzhayyim.com', 5300, 'products', 'trade')
    ON CONFLICT DO NOTHING;
