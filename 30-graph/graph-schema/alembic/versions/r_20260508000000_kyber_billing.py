"""Captured from Kysely migration 20260508000000_kyber_billing."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508000000_kyber_billing"
down_revision = 'r_20260507920000_bpmn_lexicon_binding_routing_target'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_billing_tenant (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      tenant_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         "      plan_id VARCHAR NOT NULL DEFAULT 'free',\n"
         '      stripe_customer_id VARCHAR,\n'
         '      stripe_subscription_id VARCHAR,\n'
         '      plan_activated_at VARCHAR NOT NULL,\n'
         '      trial_ends_at VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      max_users INTEGER NOT NULL DEFAULT 1,\n'
         '      max_monthly_txns INTEGER NOT NULL DEFAULT 100,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      updated_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_usage_meter (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      tenant_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      meter_type VARCHAR NOT NULL,\n'
         '      period_month VARCHAR NOT NULL,\n'
         '      delta_count BIGINT NOT NULL DEFAULT 0,\n'
         '      reported_to_stripe BOOLEAN NOT NULL DEFAULT FALSE,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_stripe_report (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      tenant_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      period_month VARCHAR NOT NULL,\n'
         '      meter_type VARCHAR NOT NULL,\n'
         '      total_count BIGINT NOT NULL DEFAULT 0,\n'
         '      stripe_event_id VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'pending',\n"
         '      reported_at VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kyber_monthly_usage AS\n'
         '    SELECT\n'
         '      tenant_id,\n'
         '      org_did,\n'
         '      meter_type,\n'
         '      period_month,\n'
         '      sum(delta_count) AS total_count\n'
         '    FROM vertex_kyber_usage_meter\n'
         '    GROUP BY tenant_id, org_did, meter_type, period_month\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kyber_tenant_usage_summary AS\n'
         '    SELECT\n'
         '      t.tenant_id,\n'
         '      t.org_did,\n'
         '      t.plan_id,\n'
         '      t.status AS tenant_status,\n'
         '      t.max_users,\n'
         '      t.max_monthly_txns,\n'
         "      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'xrpc_request'), 0) AS "
         'xrpc_requests_total,\n'
         "      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'rw_row'), 0) AS "
         'rw_rows_total,\n'
         "      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'llm_token'), 0) AS "
         'llm_tokens_total,\n'
         "      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'zeebe_instance'), 0) AS "
         'zeebe_instances_total,\n'
         "      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'pds_byte'), 0) AS "
         'pds_bytes_total\n'
         '    FROM vertex_kyber_billing_tenant t\n'
         '    LEFT JOIN vertex_kyber_usage_meter u ON t.tenant_id = u.tenant_id\n'
         '    GROUP BY t.tenant_id, t.org_did, t.plan_id, t.status, t.max_users, '
         't.max_monthly_txns\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kyber_tenant_usage_summary', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kyber_monthly_usage', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_stripe_report', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_usage_meter', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_billing_tenant', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
