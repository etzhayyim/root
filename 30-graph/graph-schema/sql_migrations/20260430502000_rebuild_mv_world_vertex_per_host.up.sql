DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host;

CREATE MATERIALIZED VIEW mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      -- legal-entity: bulk-loaded, not in AT records (190M rows)
      SELECT 'legal-entity'  AS app_host, COUNT(*) AS cnt FROM vertex_legal_entity
      -- maps: spatial features (5M rows)
      UNION ALL SELECT 'maps',          COUNT(*) FROM vertex_spatial
      -- maps: transit (small)
      UNION ALL SELECT 'maps',          COUNT(*) FROM vertex_transport
      -- gov: org and municipality
      UNION ALL SELECT 'gov',           COUNT(*) FROM vertex_gov_org
      UNION ALL SELECT 'gov',           COUNT(*) FROM vertex_gov_municipality
      -- dns: passive DNS observations
      UNION ALL SELECT 'dns',           COUNT(*) FROM vertex_dns_observation
      -- blockchain: addresses
      UNION ALL SELECT 'blockchain',    COUNT(*) FROM vertex_blockchain_actor
      -- gtin: barcoded products
      UNION ALL SELECT 'gtin',          COUNT(*) FROM vertex_gtin_product
      -- media-gamers: game actors and items
      UNION ALL SELECT 'media-gamers',  COUNT(*) FROM vertex_game_actor
      UNION ALL SELECT 'media-gamers',  COUNT(*) FROM vertex_game_item
      -- finance
      UNION ALL SELECT 'bank',          COUNT(*) FROM vertex_finance
      -- ip / chizai
      UNION ALL SELECT 'patent',        COUNT(*) FROM vertex_patent
      UNION ALL SELECT 'chizai',        COUNT(*) FROM vertex_trademark
      UNION ALL SELECT 'chizai',        COUNT(*) FROM vertex_work
      -- hospitality
      UNION ALL SELECT 'hospitality',   COUNT(*) FROM vertex_accommodation
      -- talent / employment
      UNION ALL SELECT 'talent',        COUNT(*) FROM vertex_talent_cohort
      UNION ALL SELECT 'talent',        COUNT(*) FROM vertex_skill
      UNION ALL SELECT 'talent',        COUNT(*) FROM vertex_occupation
      UNION ALL SELECT 'talent',        COUNT(*) FROM vertex_job_posting
      -- sanctions (new: 27-domain additions)
      UNION ALL SELECT 'sanctions',     COUNT(*) FROM vertex_open_ofac_sanctions_sdn
      -- adr (new: intake table)
      UNION ALL SELECT 'bengoshi',      COUNT(*) FROM vertex_adr_case
      UNION ALL SELECT 'bengoshi',      COUNT(*) FROM vertex_adr_arbitrator
      -- legal-aid (new: intake table)
      UNION ALL SELECT 'npo',           COUNT(*) FROM vertex_legal_aid_case
      UNION ALL SELECT 'npo',           COUNT(*) FROM vertex_legal_aid_office
    ) sub
    GROUP BY app_host;
