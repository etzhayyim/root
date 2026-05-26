import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * 2026-04-16
 * Add a fund graph spine plus world-coverage expansion for fund operations.
 *
 * Scope:
 * - graph tables for funds, LPs, fund managers, and investees
 * - explicit world domains for investor/private/government/sovereign/pension/mutual funds
 * - host aliases + collection mappings so fund repos can contribute to coverage
 * - mv_world_vertex_per_host recreation so fund vertices count toward coverage
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fund (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         TIMESTAMP,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      did                  VARCHAR,
      fund_id              VARCHAR,
      name                 VARCHAR,
      fund_kind            VARCHAR,
      strategy             VARCHAR,
      status               VARCHAR,
      jurisdiction         VARCHAR,
      domicile             VARCHAR,
      vintage_year         INTEGER,
      manager_name         VARCHAR,
      manager_did          VARCHAR,
      sponsor_name         VARCHAR,
      currency             VARCHAR,
      aum_amount           DOUBLE PRECISION,
      committed_capital    DOUBLE PRECISION,
      called_capital       DOUBLE PRECISION,
      distributed_capital  DOUBLE PRECISION,
      dry_powder           DOUBLE PRECISION,
      target_size          DOUBLE PRECISION,
      first_close_date     VARCHAR,
      final_close_date     VARCHAR,
      website              VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      confidence           DOUBLE PRECISION,
      notes                VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fund_investor (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         TIMESTAMP,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      did                  VARCHAR,
      investor_id          VARCHAR,
      investor_name        VARCHAR,
      investor_type        VARCHAR,
      jurisdiction         VARCHAR,
      domicile             VARCHAR,
      legal_entity_did     VARCHAR,
      commitment_amount    DOUBLE PRECISION,
      funded_amount        DOUBLE PRECISION,
      distributed_amount   DOUBLE PRECISION,
      currency             VARCHAR,
      website              VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      confidence           DOUBLE PRECISION,
      notes                VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fund_manager (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         TIMESTAMP,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      did                  VARCHAR,
      manager_id           VARCHAR,
      manager_name         VARCHAR,
      manager_type         VARCHAR,
      jurisdiction         VARCHAR,
      domicile             VARCHAR,
      regulator            VARCHAR,
      legal_entity_did     VARCHAR,
      aum_amount           DOUBLE PRECISION,
      currency             VARCHAR,
      website              VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      confidence           DOUBLE PRECISION,
      notes                VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fund_investee (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         TIMESTAMP,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      did                  VARCHAR,
      investee_id          VARCHAR,
      investee_name        VARCHAR,
      investee_type        VARCHAR,
      jurisdiction         VARCHAR,
      sector               VARCHAR,
      ticker               VARCHAR,
      legal_entity_did     VARCHAR,
      valuation_amount     DOUBLE PRECISION,
      invested_amount      DOUBLE PRECISION,
      ownership_pct        DOUBLE PRECISION,
      currency             VARCHAR,
      website              VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      confidence           DOUBLE PRECISION,
      notes                VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fund_managed_by (
      edge_id              VARCHAR PRIMARY KEY,
      src_vid              VARCHAR NOT NULL,
      dst_vid              VARCHAR NOT NULL,
      relationship         VARCHAR,
      role                 VARCHAR,
      effective_from       VARCHAR,
      effective_to         VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      confidence           DOUBLE PRECISION,
      created_at           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fund_backed_by (
      edge_id              VARCHAR PRIMARY KEY,
      src_vid              VARCHAR NOT NULL,
      dst_vid              VARCHAR NOT NULL,
      relationship         VARCHAR,
      commitment_amount    DOUBLE PRECISION,
      called_amount        DOUBLE PRECISION,
      distributed_amount   DOUBLE PRECISION,
      ownership_pct        DOUBLE PRECISION,
      currency             VARCHAR,
      announced_at         VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      confidence           DOUBLE PRECISION,
      created_at           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fund_invests_in (
      edge_id              VARCHAR PRIMARY KEY,
      src_vid              VARCHAR NOT NULL,
      dst_vid              VARCHAR NOT NULL,
      relationship         VARCHAR,
      investment_stage     VARCHAR,
      invested_amount      DOUBLE PRECISION,
      valuation_amount     DOUBLE PRECISION,
      ownership_pct        DOUBLE PRECISION,
      currency             VARCHAR,
      announced_at         VARCHAR,
      exited_at            VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      confidence           DOUBLE PRECISION,
      created_at           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fund_sponsored_by (
      edge_id              VARCHAR PRIMARY KEY,
      src_vid              VARCHAR NOT NULL,
      dst_vid              VARCHAR NOT NULL,
      relationship         VARCHAR,
      program_type         VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      confidence           DOUBLE PRECISION,
      created_at           VARCHAR
    )
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES
      ('government_fund', 'fund', 25000, 'government / policy funds', 'finance'),
      ('investor_fund', 'fund', 500000, 'fund investors / LP entities', 'finance'),
      ('mutual_fund', 'fund', 150000, 'mutual funds / UCITS', 'finance'),
      ('pension_fund', 'fund', 350000, 'pension funds', 'finance'),
      ('private_fund', 'fund', 300000, 'private funds', 'finance'),
      ('sovereign_fund', 'fund', 250, 'sovereign wealth / strategic funds', 'finance')
    ON CONFLICT (domain) DO UPDATE SET
      app_host = EXCLUDED.app_host,
      world_total = EXCLUDED.world_total,
      unit = EXCLUDED.unit,
      sector = EXCLUDED.sector
  `.execute(db);

  await sql`
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
    )
  `.execute(db);

  await sql`
    INSERT INTO dim_app_host_alias (alias_host, canonical_host)
    VALUES
      ('asset-manager', 'fund'),
      ('fm', 'fund'),
      ('fund', 'fund'),
      ('government-fund', 'fund'),
      ('investor-fund', 'fund'),
      ('ma', 'fund'),
      ('mutual-fund', 'fund'),
      ('pension-fund', 'fund'),
      ('private-fund', 'fund'),
      ('sovereign-fund', 'fund')
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE domain IN (
      'government_fund',
      'investor_fund',
      'mutual_fund',
      'pension_fund',
      'private_fund',
      'sovereign_fund'
    )
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('government_fund', 'fund', 'app.etzhayyim.apps.fund.fund', 25000, 'government / policy funds', 'finance'),
      ('government_fund', 'fund', 'app.etzhayyim.apps.fund.manager', 25000, 'government / policy funds', 'finance'),
      ('government_fund', 'fund', 'app.etzhayyim.apps.fund.investee', 25000, 'government / policy funds', 'finance'),
      ('government_fund', 'fund', 'app.etzhayyim.apps.fund.metric', 25000, 'government / policy funds', 'finance'),
      ('investor_fund', 'fund', 'app.etzhayyim.apps.fund.fund', 500000, 'fund investors / LP entities', 'finance'),
      ('investor_fund', 'fund', 'app.etzhayyim.apps.fund.investor', 500000, 'fund investors / LP entities', 'finance'),
      ('investor_fund', 'fund', 'app.etzhayyim.apps.fund.commitment', 500000, 'fund investors / LP entities', 'finance'),
      ('mutual_fund', 'fund', 'app.etzhayyim.apps.fund.fund', 150000, 'mutual funds / UCITS', 'finance'),
      ('mutual_fund', 'fund', 'app.etzhayyim.apps.fund.manager', 150000, 'mutual funds / UCITS', 'finance'),
      ('mutual_fund', 'fund', 'app.etzhayyim.apps.fund.investee', 150000, 'mutual funds / UCITS', 'finance'),
      ('mutual_fund', 'fund', 'app.etzhayyim.apps.fund.metric', 150000, 'mutual funds / UCITS', 'finance'),
      ('pension_fund', 'fund', 'app.etzhayyim.apps.fund.fund', 350000, 'pension funds', 'finance'),
      ('pension_fund', 'fund', 'app.etzhayyim.apps.fund.investor', 350000, 'pension funds', 'finance'),
      ('pension_fund', 'fund', 'app.etzhayyim.apps.fund.manager', 350000, 'pension funds', 'finance'),
      ('pension_fund', 'fund', 'app.etzhayyim.apps.fund.commitment', 350000, 'pension funds', 'finance'),
      ('pension_fund', 'fund', 'app.etzhayyim.apps.fund.metric', 350000, 'pension funds', 'finance'),
      ('private_fund', 'fund', 'app.etzhayyim.apps.fund.fund', 300000, 'private funds', 'finance'),
      ('private_fund', 'fund', 'app.etzhayyim.apps.fund.investor', 300000, 'private funds', 'finance'),
      ('private_fund', 'fund', 'app.etzhayyim.apps.fund.manager', 300000, 'private funds', 'finance'),
      ('private_fund', 'fund', 'app.etzhayyim.apps.fund.investee', 300000, 'private funds', 'finance'),
      ('private_fund', 'fund', 'app.etzhayyim.apps.fund.commitment', 300000, 'private funds', 'finance'),
      ('private_fund', 'fund', 'app.etzhayyim.apps.fund.metric', 300000, 'private funds', 'finance'),
      ('sovereign_fund', 'fund', 'app.etzhayyim.apps.fund.fund', 250, 'sovereign wealth / strategic funds', 'finance'),
      ('sovereign_fund', 'fund', 'app.etzhayyim.apps.fund.manager', 250, 'sovereign wealth / strategic funds', 'finance'),
      ('sovereign_fund', 'fund', 'app.etzhayyim.apps.fund.investee', 250, 'sovereign wealth / strategic funds', 'finance'),
      ('sovereign_fund', 'fund', 'app.etzhayyim.apps.fund.metric', 250, 'sovereign wealth / strategic funds', 'finance')
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt)::BIGINT AS vertex_count
    FROM (
      SELECT 'legal-entity' AS app_host, COUNT(*)::BIGINT AS cnt FROM vertex_legal_entity
      UNION ALL SELECT 'maps', COUNT(*)::BIGINT FROM vertex_spatial
      UNION ALL SELECT 'gov', COUNT(*)::BIGINT FROM vertex_gov_org
      UNION ALL SELECT 'dns', COUNT(*)::BIGINT FROM vertex_dns_observation
      UNION ALL SELECT 'railway', COUNT(*)::BIGINT FROM vertex_transport
      UNION ALL SELECT 'blockchain', COUNT(*)::BIGINT FROM vertex_blockchain_actor
      UNION ALL SELECT 'gtin', COUNT(*)::BIGINT FROM vertex_gtin_product
      UNION ALL SELECT 'media-gamers', COUNT(*)::BIGINT FROM vertex_game_actor
      UNION ALL SELECT 'media-gamers', COUNT(*)::BIGINT FROM vertex_game_item
      UNION ALL SELECT 'bank', COUNT(*)::BIGINT FROM vertex_finance
      UNION ALL
      SELECT
        COALESCE(a.canonical_host, raw.app_host) AS app_host,
        SUM(raw.cnt)::BIGINT AS cnt
      FROM (
        SELECT split_part(split_part(repo, 'did:web:', 2), '.', 1) AS app_host, COUNT(*)::BIGINT AS cnt
        FROM vertex_fund
        WHERE repo IS NOT NULL
        GROUP BY 1
        UNION ALL
        SELECT split_part(split_part(repo, 'did:web:', 2), '.', 1) AS app_host, COUNT(*)::BIGINT AS cnt
        FROM vertex_fund_investor
        WHERE repo IS NOT NULL
        GROUP BY 1
        UNION ALL
        SELECT split_part(split_part(repo, 'did:web:', 2), '.', 1) AS app_host, COUNT(*)::BIGINT AS cnt
        FROM vertex_fund_manager
        WHERE repo IS NOT NULL
        GROUP BY 1
        UNION ALL
        SELECT split_part(split_part(repo, 'did:web:', 2), '.', 1) AS app_host, COUNT(*)::BIGINT AS cnt
        FROM vertex_fund_investee
        WHERE repo IS NOT NULL
        GROUP BY 1
      ) raw
      LEFT JOIN dim_app_host_alias a
        ON a.alias_host = raw.app_host
      GROUP BY COALESCE(a.canonical_host, raw.app_host)
    ) sub
    GROUP BY app_host
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);
  await sql`
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
    GROUP BY app_host
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE domain IN (
      'government_fund',
      'investor_fund',
      'mutual_fund',
      'pension_fund',
      'private_fund',
      'sovereign_fund'
    )
  `.execute(db);

  await sql`
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
    ) AND canonical_host = 'fund'
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain
    WHERE domain IN (
      'government_fund',
      'investor_fund',
      'mutual_fund',
      'pension_fund',
      'private_fund',
      'sovereign_fund'
    )
  `.execute(db);

  await sql`DROP TABLE IF EXISTS edge_fund_sponsored_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fund_invests_in`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fund_backed_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fund_managed_by`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fund_investee`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fund_manager`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fund_investor`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fund`.execute(db);
}
