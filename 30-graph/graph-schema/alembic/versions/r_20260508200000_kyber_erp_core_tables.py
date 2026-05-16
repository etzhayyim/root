"""Captured from Kysely migration 20260508200000_kyber_erp_core_tables."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508200000_kyber_erp_core_tables"
down_revision = 'r_20260508155000_vertex_wvme_app_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_account (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      account_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      code VARCHAR NOT NULL,\n'
         '      name VARCHAR NOT NULL,\n'
         '      account_type VARCHAR NOT NULL,\n'
         '      seed BOOLEAN NOT NULL DEFAULT FALSE,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_journal_entry (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      entry_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      date VARCHAR NOT NULL,\n'
         '      description VARCHAR,\n'
         '      debit_account VARCHAR NOT NULL,\n'
         '      credit_account VARCHAR NOT NULL,\n'
         '      amount DOUBLE PRECISION NOT NULL,\n'
         "      currency VARCHAR NOT NULL DEFAULT 'USD',\n"
         '      reference VARCHAR,\n'
         '      period VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_invoice (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      invoice_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      invoice_number VARCHAR NOT NULL,\n'
         '      invoice_type VARCHAR NOT NULL,\n'
         '      party_did VARCHAR,\n'
         '      party_name VARCHAR,\n'
         '      issue_date VARCHAR NOT NULL,\n'
         '      due_date VARCHAR,\n'
         '      subtotal DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      tax DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      total DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         "      currency VARCHAR NOT NULL DEFAULT 'USD',\n"
         "      status VARCHAR NOT NULL DEFAULT 'draft',\n"
         '      items_json VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_employee (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      employee_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      employee_number VARCHAR NOT NULL,\n'
         '      first_name VARCHAR NOT NULL,\n'
         '      last_name VARCHAR NOT NULL,\n'
         '      email VARCHAR,\n'
         '      department VARCHAR,\n'
         '      position VARCHAR,\n'
         "      employment_type VARCHAR NOT NULL DEFAULT 'full-time',\n"
         '      hire_date VARCHAR NOT NULL,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_purchase_order (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      po_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      po_number VARCHAR NOT NULL,\n'
         '      vendor_did VARCHAR,\n'
         '      vendor_name VARCHAR,\n'
         '      order_date VARCHAR NOT NULL,\n'
         '      expected_delivery VARCHAR,\n'
         '      subtotal DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      tax DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      total DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         "      currency VARCHAR NOT NULL DEFAULT 'USD',\n"
         "      status VARCHAR NOT NULL DEFAULT 'draft',\n"
         '      items_json VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_inventory_item (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      item_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      sku VARCHAR NOT NULL,\n'
         '      name VARCHAR NOT NULL,\n'
         '      description VARCHAR,\n'
         '      category VARCHAR,\n'
         '      quantity_on_hand DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      unit_cost DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      reorder_point DOUBLE PRECISION,\n'
         '      warehouse VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_sales_order (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      order_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      order_number VARCHAR NOT NULL,\n'
         '      customer_did VARCHAR,\n'
         '      customer_name VARCHAR,\n'
         '      order_date VARCHAR NOT NULL,\n'
         '      expected_delivery VARCHAR,\n'
         '      subtotal DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      tax DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      total DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         "      currency VARCHAR NOT NULL DEFAULT 'USD',\n"
         "      status VARCHAR NOT NULL DEFAULT 'draft',\n"
         '      items_json VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_fixed_asset (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      asset_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      asset_number VARCHAR NOT NULL,\n'
         '      name VARCHAR NOT NULL,\n'
         '      category VARCHAR,\n'
         '      acquisition_date VARCHAR NOT NULL,\n'
         '      acquisition_cost DOUBLE PRECISION NOT NULL,\n'
         '      useful_life_years INTEGER NOT NULL,\n'
         "      depreciation_method VARCHAR NOT NULL DEFAULT 'straight-line',\n"
         '      salvage_value DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      accumulated_depreciation DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      net_book_value DOUBLE PRECISION NOT NULL,\n'
         '      location VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_depreciation_run (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      run_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      period VARCHAR NOT NULL,\n'
         '      total_depreciation DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      asset_count INTEGER NOT NULL DEFAULT 0,\n'
         "      status VARCHAR NOT NULL DEFAULT 'completed',\n"
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_policy_control (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      control_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      control_code VARCHAR NOT NULL,\n'
         '      name VARCHAR NOT NULL,\n'
         '      description VARCHAR,\n'
         '      framework VARCHAR,\n'
         '      category VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      owner_did VARCHAR,\n'
         '      review_date VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_risk_issue (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      issue_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      title VARCHAR NOT NULL,\n'
         '      description VARCHAR,\n'
         '      category VARCHAR,\n'
         "      likelihood VARCHAR NOT NULL DEFAULT 'medium',\n"
         "      impact VARCHAR NOT NULL DEFAULT 'medium',\n"
         '      risk_score INTEGER,\n'
         "      status VARCHAR NOT NULL DEFAULT 'open',\n"
         '      owner_did VARCHAR,\n'
         '      due_date VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_department (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      department_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      role VARCHAR NOT NULL,\n'
         '      dept_did VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kyber_integration_binding (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      binding_id VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      integration_id VARCHAR NOT NULL,\n'
         '      name VARCHAR NOT NULL,\n'
         '      description VARCHAR,\n'
         '      category VARCHAR,\n'
         '      xrpc_method VARCHAR,\n'
         '      synced_at VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS vertex_kyber_integration_binding', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_department', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_risk_issue', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_policy_control', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_depreciation_run', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_fixed_asset', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_sales_order', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_inventory_item', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_purchase_order', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_employee', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_invoice', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_journal_entry', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kyber_account', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
