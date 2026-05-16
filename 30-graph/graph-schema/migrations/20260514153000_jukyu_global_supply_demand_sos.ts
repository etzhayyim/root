import { Kysely, sql } from 'kysely';

// tier: B

/**
 * Jukyu global supply-demand System-of-Systems graph.
 *
 * Adds cross-domain supply nodes, balance observations, supply dependency
 * edges, Pregel run tracking, company exposure rankings, and notification
 * signals. Domain actors remain SSoT; Jukyu normalizes their outputs for
 * global balance and propagation.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jukyu_supply_node (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      domain VARCHAR NOT NULL,
      node_code VARCHAR NOT NULL,
      node_kind VARCHAR NOT NULL,
      display_name VARCHAR,
      country_code VARCHAR,
      region_code VARCHAR,
      locode VARCHAR,
      operator_did VARCHAR,
      product_code VARCHAR,
      product_family VARCHAR,
      capacity_unit VARCHAR,
      supply_capacity DOUBLE PRECISION,
      demand_capacity DOUBLE PRECISION,
      inventory_quantity DOUBLE PRECISION,
      utilization_pct DOUBLE PRECISION,
      status VARCHAR,
      source_table VARCHAR,
      source_vertex_id VARCHAR,
      collection VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jukyu_balance_observation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      observation_id VARCHAR NOT NULL,
      domain VARCHAR NOT NULL,
      country_code VARCHAR,
      region_code VARCHAR,
      product_code VARCHAR,
      product_family VARCHAR,
      supply_quantity DOUBLE PRECISION,
      demand_quantity DOUBLE PRECISION,
      inventory_quantity DOUBLE PRECISION,
      balance_quantity DOUBLE PRECISION,
      quantity_unit VARCHAR,
      price_usd_unit DOUBLE PRECISION,
      observed_at VARCHAR NOT NULL,
      source_kind VARCHAR,
      source_url VARCHAR,
      confidence DOUBLE PRECISION,
      status VARCHAR,
      collection VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jukyu_company_exposure (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      exposure_id VARCHAR NOT NULL,
      run_id VARCHAR,
      company_did VARCHAR NOT NULL,
      company_name VARCHAR,
      domain VARCHAR NOT NULL,
      country_code VARCHAR,
      product_code VARCHAR,
      product_family VARCHAR,
      supply_pressure DOUBLE PRECISION,
      demand_pressure DOUBLE PRECISION,
      price_pressure DOUBLE PRECISION,
      downstream_pressure DOUBLE PRECISION,
      structural_pressure DOUBLE PRECISION,
      risk_score DOUBLE PRECISION,
      confidence DOUBLE PRECISION,
      evidence_json VARCHAR,
      recommended_action VARCHAR,
      status VARCHAR,
      collection VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jukyu_pregel_run (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      run_id VARCHAR NOT NULL,
      graph_name VARCHAR NOT NULL,
      domain VARCHAR,
      seed_country_code VARCHAR,
      seed_company_did VARCHAR,
      scenario_type VARCHAR,
      shock_json VARCHAR,
      max_iterations BIGINT,
      started_at VARCHAR,
      completed_at VARCHAR,
      status VARCHAR,
      summary_json VARCHAR,
      collection VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jukyu_notification_signal (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      signal_id VARCHAR NOT NULL,
      run_id VARCHAR,
      target_company_did VARCHAR NOT NULL,
      target_channel VARCHAR,
      domain VARCHAR NOT NULL,
      country_code VARCHAR,
      product_code VARCHAR,
      product_family VARCHAR,
      severity VARCHAR,
      risk_score DOUBLE PRECISION,
      confidence DOUBLE PRECISION,
      title VARCHAR,
      body VARCHAR,
      evidence_json VARCHAR,
      recommended_action VARCHAR,
      notification_status VARCHAR,
      next_retry_at VARCHAR,
      emitted_at VARCHAR,
      collection VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jukyu_supply_dependency (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      domain VARCHAR NOT NULL,
      relationship VARCHAR NOT NULL,
      product_code VARCHAR,
      product_family VARCHAR,
      capacity_quantity DOUBLE PRECISION,
      quantity_unit VARCHAR,
      lead_time_days DOUBLE PRECISION,
      substitution_difficulty DOUBLE PRECISION,
      dependency_weight DOUBLE PRECISION,
      confidence DOUBLE PRECISION,
      status VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jukyu_company_operates_node (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      role VARCHAR,
      ownership_pct DOUBLE PRECISION,
      confidence DOUBLE PRECISION,
      status VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jukyu_exposure_triggers_signal (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      trigger_kind VARCHAR,
      trigger_score DOUBLE PRECISION,
      status VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_supply_node_domain_country ON vertex_jukyu_supply_node (domain, country_code, product_family)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_supply_node_operator ON vertex_jukyu_supply_node (operator_did, domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_balance_domain_time ON vertex_jukyu_balance_observation (domain, observed_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_balance_country_product ON vertex_jukyu_balance_observation (country_code, product_code, product_family)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_exposure_company ON vertex_jukyu_company_exposure (company_did, domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_exposure_rank ON vertex_jukyu_company_exposure (domain, country_code, risk_score)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_jukyu_notification_target ON vertex_jukyu_notification_signal (target_company_did, notification_status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jukyu_supply_src ON edge_jukyu_supply_dependency (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jukyu_supply_dst ON edge_jukyu_supply_dependency (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jukyu_operates_company ON edge_jukyu_company_operates_node (src_vid)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jukyu_global_balance AS
      SELECT
        domain,
        country_code,
        region_code,
        product_code,
        product_family,
        SUM(COALESCE(supply_quantity, 0.0)) AS supply_quantity,
        SUM(COALESCE(demand_quantity, 0.0)) AS demand_quantity,
        SUM(COALESCE(inventory_quantity, 0.0)) AS inventory_quantity,
        SUM(COALESCE(balance_quantity, COALESCE(supply_quantity, 0.0) - COALESCE(demand_quantity, 0.0))) AS balance_quantity,
        MAX(observed_at) AS latest_observed_at,
        AVG(COALESCE(confidence, 0.0)) AS avg_confidence,
        COUNT(*)::bigint AS observation_count
      FROM vertex_jukyu_balance_observation
      WHERE status IS NULL OR status <> 'deleted'
      GROUP BY domain, country_code, region_code, product_code, product_family
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jukyu_supply_chain_trace AS
      SELECT
        e.edge_id,
        e.domain,
        e.relationship,
        src.vertex_id AS src_vid,
        src.node_code AS src_node_code,
        src.node_kind AS src_node_kind,
        src.display_name AS src_name,
        src.country_code AS src_country_code,
        src.operator_did AS src_operator_did,
        dst.vertex_id AS dst_vid,
        dst.node_code AS dst_node_code,
        dst.node_kind AS dst_node_kind,
        dst.display_name AS dst_name,
        dst.country_code AS dst_country_code,
        dst.operator_did AS dst_operator_did,
        e.product_code,
        e.product_family,
        e.capacity_quantity,
        e.quantity_unit,
        e.lead_time_days,
        e.substitution_difficulty,
        e.dependency_weight,
        e.confidence,
        e.status
      FROM edge_jukyu_supply_dependency e
      JOIN vertex_jukyu_supply_node src ON src.vertex_id = e.src_vid
      JOIN vertex_jukyu_supply_node dst ON dst.vertex_id = e.dst_vid
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jukyu_company_exposure_rank AS
      SELECT
        run_id,
        company_did,
        company_name,
        domain,
        country_code,
        product_code,
        product_family,
        supply_pressure,
        demand_pressure,
        price_pressure,
        downstream_pressure,
        structural_pressure,
        risk_score,
        confidence,
        recommended_action,
        status
      FROM vertex_jukyu_company_exposure
      WHERE status IS NULL OR status IN ('active', 'monitored')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jukyu_notification_outbox AS
      SELECT
        vertex_id,
        signal_id,
        run_id,
        target_company_did,
        target_channel,
        domain,
        country_code,
        product_code,
        product_family,
        severity,
        risk_score,
        confidence,
        title,
        body,
        evidence_json,
        recommended_action,
        notification_status,
        next_retry_at,
        emitted_at
      FROM vertex_jukyu_notification_signal
      WHERE notification_status IN ('pending', 'retry')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_notification_outbox`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_company_exposure_rank`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_supply_chain_trace`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jukyu_global_balance`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jukyu_exposure_triggers_signal`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jukyu_company_operates_node`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jukyu_supply_dependency`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jukyu_notification_signal`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jukyu_pregel_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jukyu_company_exposure`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jukyu_balance_observation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jukyu_supply_node`.execute(db);
}
