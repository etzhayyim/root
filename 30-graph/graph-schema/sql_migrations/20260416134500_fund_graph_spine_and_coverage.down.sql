DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host;

CREATE MATERIALIZED VIEW mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      SELECT 'legal-entity' AS app_host, COUNT(*) AS cnt FROM vertex_legal_entity
      UNION ALL SELECT 'maps',         COUNT(*) FROM vertex_spatial
      UNION ALL SELECT 'gov',          COUNT(*) FROM vertex_gov_org
      UNION ALL SELECT 'dns',          COUNT(*) FROM vertex_dns_observation
      UNION ALL SELECT 'railway',      COUNT(*) FROM vertex_transport
      UNION ALL SELECT 'blockchain',   COUNT(*) FROM vertex_blockchain_actor
      UNION ALL SELECT 'gtin',         COUNT(*) FROM vertex_gtin_product
      UNION ALL SELECT 'media-gamers', COUNT(*) FROM vertex_game_actor
      UNION ALL SELECT 'media-gamers', COUNT(*) FROM vertex_game_item
      UNION ALL SELECT 'bank',         COUNT(*) FROM vertex_finance
    ) sub
    GROUP BY app_host;

DELETE FROM dim_world_domain_collection
    WHERE domain IN (
      'government_fund',
      'investor_fund',
      'mutual_fund',
      'pension_fund',
      'private_fund',
      'sovereign_fund'
    );

DELETE FROM dim_app_host_alias
    WHERE alias_host IN (
      'asset-manager',
      'fm',
      'fund',
      'government-fund',
      'investor-fund',
      'ma',
      'mutual-fund',
      'pension-fund',
      'private-fund',
      'sovereign-fund'
    ) AND canonical_host = 'fund';

DELETE FROM dim_world_domain
    WHERE domain IN (
      'government_fund',
      'investor_fund',
      'mutual_fund',
      'pension_fund',
      'private_fund',
      'sovereign_fund'
    );

DROP TABLE IF EXISTS edge_fund_sponsored_by;

DROP TABLE IF EXISTS edge_fund_invests_in;

DROP TABLE IF EXISTS edge_fund_backed_by;

DROP TABLE IF EXISTS edge_fund_managed_by;

DROP TABLE IF EXISTS vertex_fund_investee;

DROP TABLE IF EXISTS vertex_fund_manager;

DROP TABLE IF EXISTS vertex_fund_investor;

DROP TABLE IF EXISTS vertex_fund;
