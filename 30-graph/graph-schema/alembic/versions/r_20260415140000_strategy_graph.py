"""Captured from Kysely migration 20260415140000_strategy_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260415140000_strategy_graph"
down_revision = 'r_20260415133000_profile_actor_topology_backfill'
branch_labels = None
depends_on = None

UP = [{'sql': 'CREATE TABLE IF NOT EXISTS vertex_business_entity (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    entity_code VARCHAR,        -- GJ, GW, GJGL, CommonsOS\n'
         '    legal_name VARCHAR,\n'
         '    status VARCHAR,             -- active | divesting | dormant | dissolved\n'
         '    parent_entity_id VARCHAR,   -- self-ref for subsidiary\n'
         '    incorporated_at VARCHAR,\n'
         '    notes VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_business_domain (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    domain_code VARCHAR,        -- accounting, legal, hr, ses, welfare, ai\n'
         '    display_name VARCHAR,\n'
         '    description VARCHAR,\n'
         '    kyber_dept VARCHAR,         -- link to existing kyber dept taxonomy\n'
         '    status VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_business_case (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    case_code VARCHAR,          -- suzuki-liability / monolith / kaonavi / '
         'real-estate-exit\n'
         '    display_name VARCHAR,\n'
         '    case_type VARCHAR,          -- litigation | m_and_a | collection | divestiture | '
         'project\n'
         '    status VARCHAR,             -- open | in_progress | closed | won | lost\n'
         '    opened_at VARCHAR,\n'
         '    closed_at VARCHAR,\n'
         '    counterparty VARCHAR,\n'
         '    estimated_impact_jpy BIGINT,\n'
         '    document_count BIGINT,\n'
         '    last_activity_at VARCHAR,\n'
         '    responsible_did VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_revenue_stream (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    stream_code VARCHAR,        -- ses / gw-welfare / yoro-credit / kyber-saas / '
         'marketplace\n'
         '    display_name VARCHAR,\n'
         '    status VARCHAR,             -- active | ramping | divesting | planned\n'
         '    current_mrr_jpy BIGINT,\n'
         '    target_mrr_jpy BIGINT,\n'
         '    entity_id VARCHAR,          -- which BusinessEntity owns this stream\n'
         '    launched_at VARCHAR,\n'
         '    gross_margin_bps BIGINT,    -- 10000 = 100%\n'
         '    notes VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_cost_center (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    center_code VARCHAR,        -- real-estate / dormant-hc / infra / litigation\n'
         '    display_name VARCHAR,\n'
         '    category VARCHAR,           -- fixed | variable | one_time\n'
         '    monthly_burn_jpy BIGINT,\n'
         '    entity_id VARCHAR,\n'
         '    reducible_bps BIGINT,       -- how much is reducible (10000 = fully)\n'
         '    notes VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_risk (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    risk_code VARCHAR,          -- litigation-suzuki / cash-runway / key-person\n'
         '    display_name VARCHAR,\n'
         '    risk_type VARCHAR,          -- legal | financial | operational | market | people\n'
         '    severity VARCHAR,           -- critical | high | medium | low\n'
         '    probability_bps BIGINT,\n'
         '    impact_jpy BIGINT,\n'
         '    expected_loss_jpy BIGINT,   -- derived: prob * impact\n'
         '    status VARCHAR,              -- open | mitigating | closed | accepted\n'
         '    discovered_at VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_goal (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    goal_code VARCHAR,          -- G0-profit / G1-litigation-clear\n'
         '    display_name VARCHAR,\n'
         '    goal_type VARCHAR,          -- financial | compliance | strategic | operational\n'
         '    target_value_jpy BIGINT,\n'
         '    target_date VARCHAR,\n'
         '    status VARCHAR,              -- open | on_track | at_risk | achieved | missed\n'
         '    attainment_bps BIGINT,       -- 0-10000\n'
         '    parent_goal_id VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_action (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    action_code VARCHAR,        -- A1-gw-divest / A2-dormant-purge / ...\n'
         '    display_name VARCHAR,\n'
         '    description VARCHAR,\n'
         '    status VARCHAR,              -- planned | in_progress | blocked | done | cancelled\n'
         '    priority BIGINT,             -- 1-100, higher = more urgent\n'
         '    effort_days BIGINT,          -- estimated\n'
         '    confidence_bps BIGINT,       -- 0-10000, estimate confidence\n'
         '    owner_did VARCHAR,\n'
         '    due_date VARCHAR,\n'
         '    started_at VARCHAR,\n'
         '    completed_at VARCHAR,\n'
         '    phase VARCHAR,               -- immediate | short | medium | long\n'
         '    topo_level BIGINT            -- depth in reverse-topo sort\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_infra_capability (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    capability_code VARCHAR,    -- I1-outlook-rules / I2-worker-deploy / I3-cron-sync\n'
         '    display_name VARCHAR,\n'
         '    capability_type VARCHAR,    -- automation | data | compute | governance\n'
         '    status VARCHAR,              -- planned | built | deployed | deprecated\n'
         '    deployed_at VARCHAR,\n'
         '    maintenance_burden VARCHAR   -- low | medium | high\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_kpi (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    kpi_code VARCHAR,           -- monthly-revenue / burn-rate / profit-months\n'
         '    display_name VARCHAR,\n'
         '    unit VARCHAR,               -- jpy | count | bps | days\n'
         '    direction VARCHAR,          -- up | down | target\n'
         '    current_value BIGINT,\n'
         '    target_value BIGINT,\n'
         '    threshold_red BIGINT,\n'
         '    threshold_green BIGINT,\n'
         '    measured_at VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_milestone (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    milestone_code VARCHAR,     -- phase-a-mvp / phase-b-monetize / phase-c-marketplace\n'
         '    display_name VARCHAR,\n'
         '    target_date VARCHAR,\n'
         '    actual_date VARCHAR,\n'
         '    status VARCHAR,\n'
         '    linked_goal_id VARCHAR,\n'
         '    linked_stream_id VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS vertex_strategy_snapshot (\n'
         '    vertex_id VARCHAR PRIMARY KEY,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    snapshot_at VARCHAR,\n'
         '    entity_code VARCHAR,\n'
         '    total_documents BIGINT,\n'
         '    active_users BIGINT,\n'
         '    monthly_revenue_jpy BIGINT,\n'
         '    monthly_burn_jpy BIGINT,\n'
         '    net_margin_jpy BIGINT,\n'
         '    open_risks BIGINT,\n'
         '    open_cases BIGINT,\n'
         '    profit_months BIGINT,\n'
         '    yoy_doc_delta_bps BIGINT,\n'
         '    generator VARCHAR          -- llm-analysis-v1 | manual | cron\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_depends_on (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    dep_type VARCHAR,            -- hard | soft | preferred\n'
         '    slack_days BIGINT            -- leeway in scheduling\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_achieves (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    contribution_bps BIGINT,     -- how much this action contributes to goal\n'
         '    confidence_bps BIGINT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_reduces_cost (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    monthly_reduction_jpy BIGINT,\n'
         '    one_time_cost_jpy BIGINT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_generates_revenue (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    monthly_expected_jpy BIGINT,\n'
         '    horizon_months BIGINT,\n'
         '    confidence_bps BIGINT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_mitigates_risk (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    risk_delta_bps BIGINT        -- expected reduction in expected_loss_jpy\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_enables (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    enablement_type VARCHAR      -- unlocks | accelerates | derisks\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_targets_kpi (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    target_delta BIGINT,\n'
         '    horizon_months BIGINT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_belongs_to_entity (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    since VARCHAR\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_classified_as (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    classifier VARCHAR,\n'
         '    confidence_bps BIGINT\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE TABLE IF NOT EXISTS edge_related_to (\n'
         '    edge_id VARCHAR PRIMARY KEY,\n'
         '    src_vid VARCHAR, dst_vid VARCHAR,\n'
         '    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,\n'
         '    label VARCHAR,\n'
         '    relation VARCHAR             -- spawns | precedes | same_counterparty | '
         'shared_evidence\n'
         '  )',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_action_priority AS\n'
         '    SELECT\n'
         '      a.vertex_id,\n'
         '      a.action_code,\n'
         '      a.display_name,\n'
         '      a.status,\n'
         '      a.phase,\n'
         '      a.topo_level,\n'
         '      COUNT(DISTINCT ach.dst_vid) AS goals_served,\n'
         '      COUNT(DISTINCT mr.dst_vid) AS risks_mitigated,\n'
         '      COALESCE(SUM(rc.monthly_reduction_jpy), 0) AS monthly_cost_reduction,\n'
         '      COALESCE(SUM(gr.monthly_expected_jpy), 0) AS monthly_revenue,\n'
         '      a.effort_days,\n'
         '      a.confidence_bps,\n'
         '      (\n'
         '        (COUNT(DISTINCT ach.dst_vid) * 10 + COUNT(DISTINCT mr.dst_vid) * 5)\n'
         '        * COALESCE(a.confidence_bps, 5000) / 10000\n'
         '        * 1000 / GREATEST(a.effort_days, 1)\n'
         '      ) AS priority_score\n'
         '    FROM vertex_action a\n'
         '    LEFT JOIN edge_achieves ach ON ach.src_vid = a.vertex_id\n'
         '    LEFT JOIN edge_mitigates_risk mr ON mr.src_vid = a.vertex_id\n'
         '    LEFT JOIN edge_reduces_cost rc ON rc.src_vid = a.vertex_id\n'
         '    LEFT JOIN edge_generates_revenue gr ON gr.src_vid = a.vertex_id\n'
         "    WHERE a.status IN ('planned', 'in_progress')\n"
         '    GROUP BY a.vertex_id, a.action_code, a.display_name, a.status, a.phase, '
         'a.topo_level, a.effort_days, a.confidence_bps\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_goal_progress AS\n'
         '    SELECT\n'
         '      g.vertex_id,\n'
         '      g.goal_code,\n'
         '      g.display_name,\n'
         '      g.status AS goal_status,\n'
         '      g.target_value_jpy,\n'
         '      g.target_date,\n'
         '      g.attainment_bps,\n'
         '      COUNT(DISTINCT ach.src_vid) AS action_count,\n'
         "      SUM(CASE WHEN a.status = 'done' THEN 1 ELSE 0 END) AS actions_done,\n"
         "      SUM(CASE WHEN a.status = 'in_progress' THEN 1 ELSE 0 END) AS actions_in_progress,\n"
         "      SUM(CASE WHEN a.status = 'blocked' THEN 1 ELSE 0 END) AS actions_blocked\n"
         '    FROM vertex_goal g\n'
         '    LEFT JOIN edge_achieves ach ON ach.dst_vid = g.vertex_id\n'
         '    LEFT JOIN vertex_action a ON a.vertex_id = ach.src_vid\n'
         '    GROUP BY g.vertex_id, g.goal_code, g.display_name, g.status, g.target_value_jpy, '
         'g.target_date, g.attainment_bps\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_entity_health AS\n'
         '    SELECT\n'
         '      e.vertex_id,\n'
         '      e.entity_code,\n'
         '      e.legal_name,\n'
         '      e.status,\n'
         '      (SELECT COUNT(*) FROM vertex_office_document d\n'
         '        JOIN edge_belongs_to_entity be ON be.src_vid = d.vertex_id\n'
         '        WHERE be.dst_vid = e.vertex_id) AS document_count,\n'
         '      COALESCE(SUM(DISTINCT rs.current_mrr_jpy), 0) AS monthly_revenue,\n'
         '      COALESCE(SUM(DISTINCT cc.monthly_burn_jpy), 0) AS monthly_burn,\n'
         '      COALESCE(SUM(DISTINCT rs.current_mrr_jpy), 0) - COALESCE(SUM(DISTINCT '
         'cc.monthly_burn_jpy), 0) AS net_monthly,\n'
         "      COUNT(DISTINCT bc.vertex_id) FILTER (WHERE bc.status = 'open') AS open_cases,\n"
         "      COUNT(DISTINCT r.vertex_id) FILTER (WHERE r.status = 'open') AS open_risks,\n"
         "      COALESCE(SUM(DISTINCT r.expected_loss_jpy) FILTER (WHERE r.status = 'open'), 0) AS "
         'open_risk_exposure\n'
         '    FROM vertex_business_entity e\n'
         '    LEFT JOIN vertex_revenue_stream rs ON rs.entity_id = e.vertex_id\n'
         '    LEFT JOIN vertex_cost_center cc ON cc.entity_id = e.vertex_id\n'
         '    LEFT JOIN vertex_business_case bc ON bc.responsible_did = e.entity_code\n'
         "    LEFT JOIN vertex_risk r ON r.risk_code LIKE '%' || e.entity_code || '%'\n"
         '    GROUP BY e.vertex_id, e.entity_code, e.legal_name, e.status\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_case_load AS\n'
         '    SELECT\n'
         '      bc.vertex_id,\n'
         '      bc.case_code,\n'
         '      bc.display_name,\n'
         '      bc.case_type,\n'
         '      bc.status,\n'
         '      bc.counterparty,\n'
         '      bc.estimated_impact_jpy,\n'
         '      bc.document_count,\n'
         '      bc.last_activity_at,\n'
         '      bc.responsible_did,\n'
         "      COUNT(DISTINCT a.vertex_id) FILTER (WHERE a.status IN ('planned','in_progress')) "
         'AS open_actions\n'
         '    FROM vertex_business_case bc\n'
         '    LEFT JOIN edge_mitigates_risk mr ON mr.dst_vid IN (SELECT vertex_id FROM vertex_risk '
         "WHERE risk_code LIKE '%' || bc.case_code || '%')\n"
         '    LEFT JOIN vertex_action a ON a.vertex_id = mr.src_vid\n'
         '    GROUP BY bc.vertex_id, bc.case_code, bc.display_name, bc.case_type, bc.status,\n'
         '             bc.counterparty, bc.estimated_impact_jpy, bc.document_count,\n'
         '             bc.last_activity_at, bc.responsible_did\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_revenue_forecast AS\n'
         '    SELECT\n'
         '      rs.stream_code,\n'
         '      rs.display_name,\n'
         '      rs.current_mrr_jpy,\n'
         '      rs.target_mrr_jpy,\n'
         '      rs.status,\n'
         '      SUM(gr.monthly_expected_jpy * gr.confidence_bps / 10000) AS '
         'expected_uplift_monthly,\n'
         '      MIN(gr.horizon_months) AS earliest_horizon_months\n'
         '    FROM vertex_revenue_stream rs\n'
         '    LEFT JOIN edge_generates_revenue gr ON gr.dst_vid = rs.vertex_id\n'
         '    GROUP BY rs.stream_code, rs.display_name, rs.current_mrr_jpy, rs.target_mrr_jpy, '
         'rs.status\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_burn_rate_monthly AS\n'
         '    SELECT\n'
         '      cc.category,\n'
         '      COUNT(*) AS center_count,\n'
         '      SUM(cc.monthly_burn_jpy) AS total_burn,\n'
         '      SUM(cc.monthly_burn_jpy * cc.reducible_bps / 10000) AS reducible_burn,\n'
         '      SUM(rc.monthly_reduction_jpy) AS planned_reduction\n'
         '    FROM vertex_cost_center cc\n'
         '    LEFT JOIN edge_reduces_cost rc ON rc.dst_vid = cc.vertex_id\n'
         '    GROUP BY cc.category\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_critical_path AS\n'
         '    SELECT\n'
         '      i.vertex_id,\n'
         '      i.capability_code,\n'
         '      i.display_name,\n'
         '      i.status,\n'
         '      COUNT(DISTINCT e.src_vid) AS dependent_actions,\n'
         "      COUNT(DISTINCT a.vertex_id) FILTER (WHERE a.status = 'blocked') AS blocked_count,\n"
         '      MAX(a.topo_level) AS max_topo_level\n'
         '    FROM vertex_infra_capability i\n'
         '    LEFT JOIN edge_enables e ON e.src_vid = i.vertex_id\n'
         '    LEFT JOIN vertex_action a ON a.vertex_id = e.dst_vid\n'
         '    GROUP BY i.vertex_id, i.capability_code, i.display_name, i.status\n'
         '    HAVING COUNT(DISTINCT e.src_vid) > 0\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE MATERIALIZED VIEW IF NOT EXISTS mv_strategy_timeline AS\n'
         '    SELECT\n'
         '      m.milestone_code,\n'
         '      m.display_name AS milestone,\n'
         '      m.target_date,\n'
         '      m.actual_date,\n'
         '      m.status AS milestone_status,\n'
         '      g.goal_code,\n'
         '      g.display_name AS goal,\n'
         '      g.attainment_bps,\n'
         '      COUNT(DISTINCT ach.src_vid) AS supporting_actions\n'
         '    FROM vertex_milestone m\n'
         '    LEFT JOIN vertex_goal g ON g.vertex_id = m.linked_goal_id\n'
         '    LEFT JOIN edge_achieves ach ON ach.dst_vid = g.vertex_id\n'
         '    GROUP BY m.milestone_code, m.display_name, m.target_date, m.actual_date, m.status,\n'
         '             g.goal_code, g.display_name, g.attainment_bps\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_strategy_timeline', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_critical_path', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_burn_rate_monthly', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_revenue_forecast', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_case_load', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_entity_health', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_goal_progress', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_action_priority', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_related_to', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_classified_as', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_belongs_to_entity', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_targets_kpi', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_enables', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_mitigates_risk', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_generates_revenue', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_reduces_cost', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_achieves', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_depends_on', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_strategy_snapshot', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_milestone', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kpi', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_infra_capability', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_action', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_goal', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_risk', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_cost_center', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_revenue_stream', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_business_case', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_business_domain', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_business_entity', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
