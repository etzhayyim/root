CREATE VIEW IF NOT EXISTS view_icd10_disease AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'       AS name,
      value_json::jsonb->>'level'      AS level,
      value_json::jsonb->>'parent'     AS parent_code,
      value_json::jsonb->>'short_name' AS short_name,
      value_json::jsonb->>'chapter'    AS chapter,
      value_json::jsonb->>'code_range' AS code_range,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.icd10.disease';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('icd10', 'icd10.etzhayyim.com', 90168, 'ICD-10-CM disease codes', 'healthcare');

DELETE FROM edge_classified_as WHERE system = 'iso4217_iso3166';
