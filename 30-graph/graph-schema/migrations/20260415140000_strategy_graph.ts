import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: A
// tier: B
// tier: C

/**
 * Strategy Graph — persist executive analysis (goals, actions, dependencies,
 * revenue/cost centers, risks, KPIs, milestones) as queryable graph data.
 *
 * Pattern: Observation/Analysis is the SSoT of strategic planning. Rather than
 * rewriting management docs ad-hoc in Markdown, express the business state +
 * intervention topology as vertex/edge so that:
 *   - critical-path / bottleneck can be computed (mv_critical_path)
 *   - goal-attainment is traceable (Action → achieves → Goal + kpi rollup)
 *   - dependency order is Kysely-queryable for dashboards (reverse topo sort)
 *   - snapshots are parquet-archivable for longitudinal comparison
 *
 * Complements existing vertex_office_document / vertex_email_message (operational
 * evidence) — Strategy Graph is the reasoning layer above the raw signal graph.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Business state vertices ─────────────────────────────────────────
  await sql`CREATE TABLE IF NOT EXISTS vertex_business_entity (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    entity_code VARCHAR,        -- GJ, GW, GJGL, CommonsOS
    legal_name VARCHAR,
    status VARCHAR,             -- active | divesting | dormant | dissolved
    parent_entity_id VARCHAR,   -- self-ref for subsidiary
    incorporated_at VARCHAR,
    notes VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_business_domain (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    domain_code VARCHAR,        -- accounting, legal, hr, ses, welfare, ai
    display_name VARCHAR,
    description VARCHAR,
    kyber_dept VARCHAR,         -- link to existing kyber dept taxonomy
    status VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_business_case (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    case_code VARCHAR,          -- suzuki-liability / monolith / kaonavi / real-estate-exit
    display_name VARCHAR,
    case_type VARCHAR,          -- litigation | m_and_a | collection | divestiture | project
    status VARCHAR,             -- open | in_progress | closed | won | lost
    opened_at VARCHAR,
    closed_at VARCHAR,
    counterparty VARCHAR,
    estimated_impact_jpy BIGINT,
    document_count BIGINT,
    last_activity_at VARCHAR,
    responsible_did VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_revenue_stream (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    stream_code VARCHAR,        -- ses / gw-welfare / yoro-credit / kyber-saas / marketplace
    display_name VARCHAR,
    status VARCHAR,             -- active | ramping | divesting | planned
    current_mrr_jpy BIGINT,
    target_mrr_jpy BIGINT,
    entity_id VARCHAR,          -- which BusinessEntity owns this stream
    launched_at VARCHAR,
    gross_margin_bps BIGINT,    -- 10000 = 100%
    notes VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_cost_center (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    center_code VARCHAR,        -- real-estate / dormant-hc / infra / litigation
    display_name VARCHAR,
    category VARCHAR,           -- fixed | variable | one_time
    monthly_burn_jpy BIGINT,
    entity_id VARCHAR,
    reducible_bps BIGINT,       -- how much is reducible (10000 = fully)
    notes VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_risk (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    risk_code VARCHAR,          -- litigation-suzuki / cash-runway / key-person
    display_name VARCHAR,
    risk_type VARCHAR,          -- legal | financial | operational | market | people
    severity VARCHAR,           -- critical | high | medium | low
    probability_bps BIGINT,
    impact_jpy BIGINT,
    expected_loss_jpy BIGINT,   -- derived: prob * impact
    status VARCHAR,              -- open | mitigating | closed | accepted
    discovered_at VARCHAR
  )`.execute(db);

  // ── Strategy / planning vertices ────────────────────────────────────
  await sql`CREATE TABLE IF NOT EXISTS vertex_goal (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    goal_code VARCHAR,          -- G0-profit / G1-litigation-clear
    display_name VARCHAR,
    goal_type VARCHAR,          -- financial | compliance | strategic | operational
    target_value_jpy BIGINT,
    target_date VARCHAR,
    status VARCHAR,              -- open | on_track | at_risk | achieved | missed
    attainment_bps BIGINT,       -- 0-10000
    parent_goal_id VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_action (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    action_code VARCHAR,        -- A1-gw-divest / A2-dormant-purge / ...
    display_name VARCHAR,
    description VARCHAR,
    status VARCHAR,              -- planned | in_progress | blocked | done | cancelled
    priority BIGINT,             -- 1-100, higher = more urgent
    effort_days BIGINT,          -- estimated
    confidence_bps BIGINT,       -- 0-10000, estimate confidence
    owner_did VARCHAR,
    due_date VARCHAR,
    started_at VARCHAR,
    completed_at VARCHAR,
    phase VARCHAR,               -- immediate | short | medium | long
    topo_level BIGINT            -- depth in reverse-topo sort
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_infra_capability (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    capability_code VARCHAR,    -- I1-outlook-rules / I2-worker-deploy / I3-cron-sync
    display_name VARCHAR,
    capability_type VARCHAR,    -- automation | data | compute | governance
    status VARCHAR,              -- planned | built | deployed | deprecated
    deployed_at VARCHAR,
    maintenance_burden VARCHAR   -- low | medium | high
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_kpi (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    kpi_code VARCHAR,           -- monthly-revenue / burn-rate / profit-months
    display_name VARCHAR,
    unit VARCHAR,               -- jpy | count | bps | days
    direction VARCHAR,          -- up | down | target
    current_value BIGINT,
    target_value BIGINT,
    threshold_red BIGINT,
    threshold_green BIGINT,
    measured_at VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS vertex_milestone (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    milestone_code VARCHAR,     -- phase-a-mvp / phase-b-monetize / phase-c-marketplace
    display_name VARCHAR,
    target_date VARCHAR,
    actual_date VARCHAR,
    status VARCHAR,
    linked_goal_id VARCHAR,
    linked_stream_id VARCHAR
  )`.execute(db);

  // Time-series snapshots — append-only, supports longitudinal analysis
  await sql`CREATE TABLE IF NOT EXISTS vertex_strategy_snapshot (
    vertex_id VARCHAR PRIMARY KEY,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    snapshot_at VARCHAR,
    entity_code VARCHAR,
    total_documents BIGINT,
    active_users BIGINT,
    monthly_revenue_jpy BIGINT,
    monthly_burn_jpy BIGINT,
    net_margin_jpy BIGINT,
    open_risks BIGINT,
    open_cases BIGINT,
    profit_months BIGINT,
    yoy_doc_delta_bps BIGINT,
    generator VARCHAR          -- llm-analysis-v1 | manual | cron
  )`.execute(db);

  // ── Edges ───────────────────────────────────────────────────────────
  await sql`CREATE TABLE IF NOT EXISTS edge_depends_on (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    dep_type VARCHAR,            -- hard | soft | preferred
    slack_days BIGINT            -- leeway in scheduling
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_achieves (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    contribution_bps BIGINT,     -- how much this action contributes to goal
    confidence_bps BIGINT
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_reduces_cost (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    monthly_reduction_jpy BIGINT,
    one_time_cost_jpy BIGINT
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_generates_revenue (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    monthly_expected_jpy BIGINT,
    horizon_months BIGINT,
    confidence_bps BIGINT
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_mitigates_risk (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    risk_delta_bps BIGINT        -- expected reduction in expected_loss_jpy
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_enables (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    enablement_type VARCHAR      -- unlocks | accelerates | derisks
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_targets_kpi (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    target_delta BIGINT,
    horizon_months BIGINT
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_belongs_to_entity (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    since VARCHAR
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_classified_as (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    classifier VARCHAR,
    confidence_bps BIGINT
  )`.execute(db);

  await sql`CREATE TABLE IF NOT EXISTS edge_related_to (
    edge_id VARCHAR PRIMARY KEY,
    src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
    label VARCHAR,
    relation VARCHAR             -- spawns | precedes | same_counterparty | shared_evidence
  )`.execute(db);

  // ── Materialized Views ──────────────────────────────────────────────

  // Action priority = (goal impact × risk mitigation × confidence) / effort
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_action_priority AS
    SELECT
      a.vertex_id,
      a.action_code,
      a.display_name,
      a.status,
      a.phase,
      a.topo_level,
      COUNT(DISTINCT ach.dst_vid) AS goals_served,
      COUNT(DISTINCT mr.dst_vid) AS risks_mitigated,
      COALESCE(SUM(rc.monthly_reduction_jpy), 0) AS monthly_cost_reduction,
      COALESCE(SUM(gr.monthly_expected_jpy), 0) AS monthly_revenue,
      a.effort_days,
      a.confidence_bps,
      (
        (COUNT(DISTINCT ach.dst_vid) * 10 + COUNT(DISTINCT mr.dst_vid) * 5)
        * COALESCE(a.confidence_bps, 5000) / 10000
        * 1000 / GREATEST(a.effort_days, 1)
      ) AS priority_score
    FROM vertex_action a
    LEFT JOIN edge_achieves ach ON ach.src_vid = a.vertex_id
    LEFT JOIN edge_mitigates_risk mr ON mr.src_vid = a.vertex_id
    LEFT JOIN edge_reduces_cost rc ON rc.src_vid = a.vertex_id
    LEFT JOIN edge_generates_revenue gr ON gr.src_vid = a.vertex_id
    WHERE a.status IN ('planned', 'in_progress')
    GROUP BY a.vertex_id, a.action_code, a.display_name, a.status, a.phase, a.topo_level, a.effort_days, a.confidence_bps
  `.execute(db);

  // Goal progress rollup
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_goal_progress AS
    SELECT
      g.vertex_id,
      g.goal_code,
      g.display_name,
      g.status AS goal_status,
      g.target_value_jpy,
      g.target_date,
      g.attainment_bps,
      COUNT(DISTINCT ach.src_vid) AS action_count,
      SUM(CASE WHEN a.status = 'done' THEN 1 ELSE 0 END) AS actions_done,
      SUM(CASE WHEN a.status = 'in_progress' THEN 1 ELSE 0 END) AS actions_in_progress,
      SUM(CASE WHEN a.status = 'blocked' THEN 1 ELSE 0 END) AS actions_blocked
    FROM vertex_goal g
    LEFT JOIN edge_achieves ach ON ach.dst_vid = g.vertex_id
    LEFT JOIN vertex_action a ON a.vertex_id = ach.src_vid
    GROUP BY g.vertex_id, g.goal_code, g.display_name, g.status, g.target_value_jpy, g.target_date, g.attainment_bps
  `.execute(db);

  // Per-entity health: docs + cost + revenue + risk
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_entity_health AS
    SELECT
      e.vertex_id,
      e.entity_code,
      e.legal_name,
      e.status,
      (SELECT COUNT(*) FROM vertex_office_document d
        JOIN edge_belongs_to_entity be ON be.src_vid = d.vertex_id
        WHERE be.dst_vid = e.vertex_id) AS document_count,
      COALESCE(SUM(DISTINCT rs.current_mrr_jpy), 0) AS monthly_revenue,
      COALESCE(SUM(DISTINCT cc.monthly_burn_jpy), 0) AS monthly_burn,
      COALESCE(SUM(DISTINCT rs.current_mrr_jpy), 0) - COALESCE(SUM(DISTINCT cc.monthly_burn_jpy), 0) AS net_monthly,
      COUNT(DISTINCT bc.vertex_id) FILTER (WHERE bc.status = 'open') AS open_cases,
      COUNT(DISTINCT r.vertex_id) FILTER (WHERE r.status = 'open') AS open_risks,
      COALESCE(SUM(DISTINCT r.expected_loss_jpy) FILTER (WHERE r.status = 'open'), 0) AS open_risk_exposure
    FROM vertex_business_entity e
    LEFT JOIN vertex_revenue_stream rs ON rs.entity_id = e.vertex_id
    LEFT JOIN vertex_cost_center cc ON cc.entity_id = e.vertex_id
    LEFT JOIN vertex_business_case bc ON bc.responsible_did = e.entity_code
    LEFT JOIN vertex_risk r ON r.risk_code LIKE '%' || e.entity_code || '%'
    GROUP BY e.vertex_id, e.entity_code, e.legal_name, e.status
  `.execute(db);

  // Case load: 訴訟等の active case + doc count
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_case_load AS
    SELECT
      bc.vertex_id,
      bc.case_code,
      bc.display_name,
      bc.case_type,
      bc.status,
      bc.counterparty,
      bc.estimated_impact_jpy,
      bc.document_count,
      bc.last_activity_at,
      bc.responsible_did,
      COUNT(DISTINCT a.vertex_id) FILTER (WHERE a.status IN ('planned','in_progress')) AS open_actions
    FROM vertex_business_case bc
    LEFT JOIN edge_mitigates_risk mr ON mr.dst_vid IN (SELECT vertex_id FROM vertex_risk WHERE risk_code LIKE '%' || bc.case_code || '%')
    LEFT JOIN vertex_action a ON a.vertex_id = mr.src_vid
    GROUP BY bc.vertex_id, bc.case_code, bc.display_name, bc.case_type, bc.status,
             bc.counterparty, bc.estimated_impact_jpy, bc.document_count,
             bc.last_activity_at, bc.responsible_did
  `.execute(db);

  // Revenue forecast rollup (by month horizon)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_revenue_forecast AS
    SELECT
      rs.stream_code,
      rs.display_name,
      rs.current_mrr_jpy,
      rs.target_mrr_jpy,
      rs.status,
      SUM(gr.monthly_expected_jpy * gr.confidence_bps / 10000) AS expected_uplift_monthly,
      MIN(gr.horizon_months) AS earliest_horizon_months
    FROM vertex_revenue_stream rs
    LEFT JOIN edge_generates_revenue gr ON gr.dst_vid = rs.vertex_id
    GROUP BY rs.stream_code, rs.display_name, rs.current_mrr_jpy, rs.target_mrr_jpy, rs.status
  `.execute(db);

  // Burn rate by category
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_burn_rate_monthly AS
    SELECT
      cc.category,
      COUNT(*) AS center_count,
      SUM(cc.monthly_burn_jpy) AS total_burn,
      SUM(cc.monthly_burn_jpy * cc.reducible_bps / 10000) AS reducible_burn,
      SUM(rc.monthly_reduction_jpy) AS planned_reduction
    FROM vertex_cost_center cc
    LEFT JOIN edge_reduces_cost rc ON rc.dst_vid = cc.vertex_id
    GROUP BY cc.category
  `.execute(db);

  // Critical path — infra with most dependent actions (bottlenecks)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_critical_path AS
    SELECT
      i.vertex_id,
      i.capability_code,
      i.display_name,
      i.status,
      COUNT(DISTINCT e.src_vid) AS dependent_actions,
      COUNT(DISTINCT a.vertex_id) FILTER (WHERE a.status = 'blocked') AS blocked_count,
      MAX(a.topo_level) AS max_topo_level
    FROM vertex_infra_capability i
    LEFT JOIN edge_enables e ON e.src_vid = i.vertex_id
    LEFT JOIN vertex_action a ON a.vertex_id = e.dst_vid
    GROUP BY i.vertex_id, i.capability_code, i.display_name, i.status
    HAVING COUNT(DISTINCT e.src_vid) > 0
  `.execute(db);

  // Strategy timeline — milestone × action × goal
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_strategy_timeline AS
    SELECT
      m.milestone_code,
      m.display_name AS milestone,
      m.target_date,
      m.actual_date,
      m.status AS milestone_status,
      g.goal_code,
      g.display_name AS goal,
      g.attainment_bps,
      COUNT(DISTINCT ach.src_vid) AS supporting_actions
    FROM vertex_milestone m
    LEFT JOIN vertex_goal g ON g.vertex_id = m.linked_goal_id
    LEFT JOIN edge_achieves ach ON ach.dst_vid = g.vertex_id
    GROUP BY m.milestone_code, m.display_name, m.target_date, m.actual_date, m.status,
             g.goal_code, g.display_name, g.attainment_bps
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    'mv_strategy_timeline', 'mv_critical_path', 'mv_burn_rate_monthly',
    'mv_revenue_forecast', 'mv_case_load', 'mv_entity_health',
    'mv_goal_progress', 'mv_action_priority',
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  for (const t of [
    'edge_related_to', 'edge_classified_as', 'edge_belongs_to_entity',
    'edge_targets_kpi', 'edge_enables', 'edge_mitigates_risk',
    'edge_generates_revenue', 'edge_reduces_cost', 'edge_achieves',
    'edge_depends_on',
    'vertex_strategy_snapshot', 'vertex_milestone', 'vertex_kpi',
    'vertex_infra_capability', 'vertex_action', 'vertex_goal',
    'vertex_risk', 'vertex_cost_center', 'vertex_revenue_stream',
    'vertex_business_case', 'vertex_business_domain', 'vertex_business_entity',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
