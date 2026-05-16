"""Captured from Kysely migration 20260419230100_vertex_collector_tables."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260419230100_vertex_collector_tables"
down_revision = 'r_20260419230000_vertex_gmail_account_binding'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_collector_dns_observation (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      node_id VARCHAR, domain VARCHAR, handle VARCHAR, status VARCHAR, observed_at '
         'VARCHAR,\n'
         '      registrar VARCHAR, registrar_handle VARCHAR, registrar_iana_id VARCHAR,\n'
         '      registration_date VARCHAR, expiration_date VARCHAR, last_changed_date VARCHAR,\n'
         '      dnssec VARCHAR, run_id VARCHAR,\n'
         '      a_records VARCHAR, aaaa_records VARCHAR, cname_records VARCHAR,\n'
         '      mx_records VARCHAR, ns_records VARCHAR, txt_records VARCHAR, nameservers VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_collector_dns_snapshot (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      node_id VARCHAR, domain VARCHAR, registrar VARCHAR, dnssec VARCHAR,\n'
         '      run_id VARCHAR, snapshot_at VARCHAR,\n'
         '      a_records VARCHAR, aaaa_records VARCHAR, cname_records VARCHAR,\n'
         '      mx_records VARCHAR, ns_records VARCHAR, txt_records VARCHAR, nameservers VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_collector_dns_change (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      node_id VARCHAR, domain VARCHAR, change_type VARCHAR, field VARCHAR, run_id '
         'VARCHAR,\n'
         '      detected_at VARCHAR, prev_value VARCHAR, new_value VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_collector_organization (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      node_id VARCHAR, name VARCHAR, handle VARCHAR, iana_id VARCHAR, type VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_collector_blockchain_actor (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      address VARCHAR, chain VARCHAR, label VARCHAR, source VARCHAR,\n'
         '      balance VARCHAR, total_received VARCHAR, total_sent VARCHAR,\n'
         '      tx_count BIGINT, unconfirmed_tx_count BIGINT, observed_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_collector_risk_signal (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      node_id VARCHAR, target_node_id VARCHAR, signal_type VARCHAR,\n'
         '      address VARCHAR, chain VARCHAR, currency VARCHAR, domain VARCHAR,\n'
         '      value VARCHAR, confidence VARCHAR, detected_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_collector_archive_snapshot (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      node_id VARCHAR, domain VARCHAR, source VARCHAR, url_key VARCHAR, original '
         'VARCHAR,\n'
         '      mimetype VARCHAR, status_code VARCHAR, digest VARCHAR, observed_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_collector_scan_result (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      node_id VARCHAR, ip VARCHAR, port BIGINT, protocol VARCHAR, state VARCHAR,\n'
         '      service VARCHAR, software VARCHAR, version VARCHAR, banner VARCHAR,\n'
         '      cert_issuer VARCHAR, cert_subject VARCHAR, cert_expires VARCHAR,\n'
         '      tls_version VARCHAR, tls_cipher VARCHAR, os_guess VARCHAR,\n'
         '      scanner_host VARCHAR, scanned_at VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS vertex_collector_scan_result', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_collector_archive_snapshot', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_collector_risk_signal', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_collector_blockchain_actor', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_collector_organization', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_collector_dns_change', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_collector_dns_snapshot', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_collector_dns_observation', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
