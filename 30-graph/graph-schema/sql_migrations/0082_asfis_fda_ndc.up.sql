CREATE VIEW IF NOT EXISTS view_asfis_species AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'            AS name,
      value_json::jsonb->>'level'           AS level,
      value_json::jsonb->>'scientific_name' AS scientific_name,
      value_json::jsonb->>'family'          AS family,
      value_json::jsonb->>'order'           AS taxon_order,
      value_json::jsonb->>'isscaap'         AS isscaap_group,
      value_json::jsonb->>'parent'          AS parent_code,
      (value_json::jsonb->>'in_fishstat')::boolean AS in_fishstat,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.asfis.species';

CREATE VIEW IF NOT EXISTS view_fda_ndc AS
    SELECT
      rkey AS ndc,
      value_json::jsonb->>'name'          AS name,
      value_json::jsonb->>'generic_name'  AS generic_name,
      value_json::jsonb->>'brand_name'    AS brand_name,
      value_json::jsonb->>'labeler'       AS labeler,
      value_json::jsonb->>'dosage_form'   AS dosage_form,
      value_json::jsonb->>'product_type'  AS product_type,
      value_json::jsonb->>'route'         AS route,
      value_json::jsonb->>'marketing_cat' AS marketing_category,
      value_json::jsonb->>'app_num'       AS application_number,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.fda.ndc';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('asfis', 'asfis.etzhayyim.com', 13708, 'aquatic species', 'food');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('fda_ndc', 'ndc.etzhayyim.com', 131664, 'FDA drug products', 'pharma');

DELETE FROM edge_classified_as WHERE system = 'atc_ndc';
