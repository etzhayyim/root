"""Captured from Kysely migration 20260428183700_open_sales."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428183700_open_sales"
down_revision = 'r_20260428183600_open_smartphone_patent'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_sales_lead (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      lead_id VARCHAR NOT NULL,\n'
         '      full_name VARCHAR NOT NULL,\n'
         '      email VARCHAR,\n'
         '      company VARCHAR,\n'
         '      source VARCHAR,\n'
         '      lead_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         "      status VARCHAR NOT NULL DEFAULT 'new',\n"
         '      assigned_did VARCHAR,\n'
         '      notes VARCHAR,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_sales_contact (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      contact_id VARCHAR NOT NULL,\n'
         '      full_name VARCHAR NOT NULL,\n'
         '      email VARCHAR,\n'
         '      phone VARCHAR,\n'
         '      account_did VARCHAR,\n'
         '      role VARCHAR,\n'
         '      linkedin_url VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_sales_account (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      account_id VARCHAR NOT NULL,\n'
         '      company_name VARCHAR NOT NULL,\n'
         '      domain VARCHAR,\n'
         '      industry VARCHAR,\n'
         '      employee_count INTEGER,\n'
         '      arr_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         "      tier VARCHAR NOT NULL DEFAULT 'prospect',\n"
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_sales_opportunity (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      opp_id VARCHAR NOT NULL,\n'
         '      account_did VARCHAR,\n'
         '      title VARCHAR NOT NULL,\n'
         "      stage VARCHAR NOT NULL DEFAULT 'prospecting',\n"
         '      probability_pct DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         '      amount_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         '      close_date VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      lost_reason VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'open',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_sales_activity (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      activity_id VARCHAR NOT NULL,\n'
         '      opp_did VARCHAR,\n'
         '      contact_did VARCHAR,\n'
         '      kind VARCHAR NOT NULL,\n'
         '      summary VARCHAR NOT NULL,\n'
         '      outcome VARCHAR,\n'
         '      logged_by VARCHAR NOT NULL,\n'
         '      logged_at VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_sales_quote (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      quote_id VARCHAR NOT NULL,\n'
         '      opp_did VARCHAR NOT NULL,\n'
         '      total_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         "      currency VARCHAR NOT NULL DEFAULT 'USD',\n"
         '      valid_until VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'draft',\n"
         '      line_items_json VARCHAR,\n'
         '      llm_summary VARCHAR,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_sales_forecast (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      forecast_id VARCHAR NOT NULL,\n'
         '      period VARCHAR NOT NULL,\n'
         '      pipeline_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         '      weighted_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         '      closed_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         '      ai_forecast_usd DOUBLE PRECISION,\n'
         '      confidence_pct DOUBLE PRECISION,\n'
         '      notes VARCHAR,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 0,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_sales_pipeline_health AS\n'
         '    SELECT\n'
         '      stage,\n'
         '      count(*) AS opp_count,\n'
         '      sum(amount_usd) AS total_pipeline_usd,\n'
         '      avg(probability_pct) AS avg_probability_pct,\n'
         '      sum(amount_usd * probability_pct / 100.0) AS weighted_usd\n'
         '    FROM vertex_open_sales_opportunity\n'
         "    WHERE status = 'open'\n"
         '    GROUP BY stage\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_sales_stage_velocity AS\n'
         '    SELECT\n'
         '      stage,\n'
         '      count(*) AS opp_count,\n'
         '      avg(amount_usd) AS avg_deal_size_usd,\n'
         "      sum(CASE WHEN status = 'won' THEN 1 ELSE 0 END) AS won_count,\n"
         "      sum(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) AS lost_count\n"
         '    FROM vertex_open_sales_opportunity\n'
         '    GROUP BY stage\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_sales_activity_summary AS\n'
         '    SELECT\n'
         '      opp_did,\n'
         '      kind,\n'
         '      count(*) AS activity_count\n'
         '    FROM vertex_open_sales_activity\n'
         '    GROUP BY opp_did, kind\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_open_sales_activity_summary', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_open_sales_stage_velocity', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_open_sales_pipeline_health', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_sales_forecast', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_sales_quote', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_sales_activity', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_sales_opportunity', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_sales_account', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_sales_contact', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_sales_lead', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
