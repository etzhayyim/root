DELETE FROM dim_world_domain
    WHERE domain IN (
      'accommodation', 'hotel', 'minpaku', 'ryokan',
      'occupation_code', 'skill_taxonomy', 'job_posting', 'talent_cohort_stat'
    );

INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector) VALUES
    -- Hospitality: all lodging (hotels + hostels + B&B + camping etc.)
    ('accommodation',       'hospitality', 1500000, 'accommodation properties', 'hospitality'),
    -- Hotels only subset (world_total < accommodation since hotels are a subset)
    ('hotel',               'hospitality',  700000, 'hotels (star-rated)',      'hospitality'),
    -- Japan-specific: minpaku (民泊) + ryokan
    ('minpaku',             'hospitality',   60000, 'minpaku / home-stay JP',   'hospitality'),
    ('ryokan',              'hospitality',    3000, 'ryokan JP',                'hospitality'),
    -- Talent / Employment
    ('occupation_code',     'talent',         5172, 'ISCO/O*NET occupation codes', 'employment'),
    ('skill_taxonomy',      'talent',        50000, 'ESCO + O*NET skill nodes',    'employment'),
    ('job_posting',         'talent',    300000000, 'active job postings globally','employment'),
    ('talent_cohort_stat',  'talent',    600000000, 'ILOSTAT workforce cohorts',   'employment');

DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live;

DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      -- existing entries (from 0025 + 0038)
      SELECT 'legal-entity'  AS app_host, COUNT(*) AS cnt FROM vertex_legal_entity
      UNION ALL SELECT 'maps',         COUNT(*) FROM vertex_spatial
      UNION ALL SELECT 'gov',          COUNT(*) FROM vertex_gov_org
      UNION ALL SELECT 'dns',          COUNT(*) FROM vertex_dns_observation
      UNION ALL SELECT 'railway',      COUNT(*) FROM vertex_transport
      UNION ALL SELECT 'blockchain',   COUNT(*) FROM vertex_blockchain_actor
      UNION ALL SELECT 'gtin',         COUNT(*) FROM vertex_gtin_product
      UNION ALL SELECT 'media-gamers', COUNT(*) FROM vertex_game_actor
      UNION ALL SELECT 'media-gamers', COUNT(*) FROM vertex_game_item
      UNION ALL SELECT 'bank',         COUNT(*) FROM vertex_finance
      UNION ALL SELECT 'patent',       COUNT(*) FROM vertex_patent
      UNION ALL SELECT 'chizai',       COUNT(*) FROM vertex_trademark
      UNION ALL SELECT 'chizai',       COUNT(*) FROM vertex_work
      -- new: hospitality
      UNION ALL SELECT 'hospitality',  COUNT(*) FROM vertex_accommodation
      -- new: talent / employment
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_talent_cohort
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_skill
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_occupation
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_job_posting
    ) sub
    GROUP BY app_host;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_coverage_live AS
    SELECT
      d.domain,
      d.app_host,
      d.world_total,
      d.unit,
      d.sector,
      COALESCE(p.did_count, 0)    AS did_count,
      COALESCE(r.record_count, 0) AS record_count,
      COALESCE(v.vertex_count, 0) AS vertex_count,
      GREATEST(
        COALESCE(p.did_count, 0),
        COALESCE(r.record_count, 0),
        COALESCE(v.vertex_count, 0)
      ) AS collected,
      GREATEST(
        COALESCE(p.did_count, 0),
        COALESCE(r.record_count, 0),
        COALESCE(v.vertex_count, 0)
      )::double precision / NULLIF(d.world_total, 0) AS coverage_rate
    FROM dim_world_domain d
    LEFT JOIN mv_world_did_per_host    p ON p.app_host = d.app_host
    LEFT JOIN mv_world_record_per_host r ON r.app_host = d.app_host
    LEFT JOIN mv_world_vertex_per_host v ON v.app_host = d.app_host;
