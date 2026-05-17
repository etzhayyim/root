CREATE VIEW IF NOT EXISTS view_locode_location AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'        AS name,
      value_json::jsonb->>'country'     AS country,
      value_json::jsonb->>'subdivision' AS subdivision,
      value_json::jsonb->>'function'    AS function_codes,
      value_json::jsonb->>'iata'        AS iata_code,
      value_json::jsonb->>'coords'      AS coordinates,
      value_json::jsonb->>'status'      AS status,
      (value_json::jsonb->>'has_port')::boolean    AS has_port,
      (value_json::jsonb->>'has_airport')::boolean AS has_airport,
      (value_json::jsonb->>'has_rail')::boolean    AS has_rail,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.locode.location';

CREATE VIEW IF NOT EXISTS view_iso3166_country AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'iso2'    AS iso2_code,
      value_json::jsonb->>'region'  AS region,
      value_json::jsonb->>'income'  AS income_level,
      value_json::jsonb->>'capital' AS capital,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.iso3166.country';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('locode', 'locode.etzhayyim.com', 116067, 'locations', 'transport');

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('iso3166', 'iso3166.etzhayyim.com', 296, 'countries', 'governance');

DELETE FROM edge_classified_as WHERE system = 'sovereign_m49';

DELETE FROM edge_classified_as WHERE system = 'iso3166_sovereign';
