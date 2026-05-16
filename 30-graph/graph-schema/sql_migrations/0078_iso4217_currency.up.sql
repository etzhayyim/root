CREATE VIEW IF NOT EXISTS view_iso4217_currency AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'       AS name,
      value_json::jsonb->>'numeric'    AS numeric_code,
      value_json::jsonb->>'minor_unit' AS minor_unit,
      value_json::jsonb->>'entity'     AS entity,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.iso4217.currency';

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('iso4217', 'iso4217.gftd.ai', 178, 'currencies', 'finance');
