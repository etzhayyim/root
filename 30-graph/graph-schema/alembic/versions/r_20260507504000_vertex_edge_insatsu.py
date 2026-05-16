"""Captured from Kysely migration 20260507504000_vertex_edge_insatsu."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507504000_vertex_edge_insatsu"
down_revision = 'r_20260507503000_repository_idx_mv'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_insatsu_print_partner (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      partner_did VARCHAR,\n'
         '      slug VARCHAR,\n'
         '      display_name VARCHAR,\n'
         '      country VARCHAR,\n'
         '      region VARCHAR,\n'
         '      print_methods JSONB,\n'
         '      mail_classes JSONB,\n'
         '      supports_certified_mail BOOLEAN,\n'
         '      daily_capacity_pages BIGINT,\n'
         '      base_cost_usd DOUBLE PRECISION,\n'
         '      per_page_usd DOUBLE PRECISION,\n'
         '      service_levels JSONB,\n'
         '      downstream_actor_did VARCHAR,\n'
         '      created_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_insatsu_print_mail_job (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      job_id VARCHAR,\n'
         '      status VARCHAR,\n'
         '      document_url TEXT,\n'
         '      destination_country VARCHAR,\n'
         '      recipient_name VARCHAR,\n'
         '      address_line1 TEXT,\n'
         '      postal_code VARCHAR,\n'
         '      page_count BIGINT,\n'
         '      quantity BIGINT,\n'
         '      print_method VARCHAR,\n'
         '      mail_class VARCHAR,\n'
         '      service_level VARCHAR,\n'
         '      partner_did VARCHAR,\n'
         '      partner_display_name VARCHAR,\n'
         '      route_type VARCHAR,\n'
         '      downstream_actor_did VARCHAR,\n'
         '      estimated_cost_usd DOUBLE PRECISION,\n'
         '      estimated_total_days BIGINT,\n'
         '      case_id VARCHAR,\n'
         '      subject TEXT,\n'
         '      downstream_dispatch JSONB,\n'
         '      created_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "edge_insatsu_partner_mail_job" (\n'
         '        edge_id VARCHAR PRIMARY KEY,\n'
         '        src_vid VARCHAR,\n'
         '        dst_vid VARCHAR,\n'
         '        relation VARCHAR,\n'
         '        job_id VARCHAR,\n'
         '        sensitivity_ord BIGINT,\n'
         '        owner_did VARCHAR,\n'
         '        actor_id VARCHAR,\n'
         '        created_at VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_insatsu_partner_mail_job_src" ON '
         '"edge_insatsu_partner_mail_job" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_insatsu_partner_mail_job_dst" ON '
         '"edge_insatsu_partner_mail_job" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_insatsu_partner_mail_job_relation" ON '
         '"edge_insatsu_partner_mail_job" (relation)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_insatsu_partner_mail_job_job" ON '
         '"edge_insatsu_partner_mail_job" (job_id)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "edge_insatsu_job_downstream_actor" (\n'
         '        edge_id VARCHAR PRIMARY KEY,\n'
         '        src_vid VARCHAR,\n'
         '        dst_vid VARCHAR,\n'
         '        relation VARCHAR,\n'
         '        job_id VARCHAR,\n'
         '        sensitivity_ord BIGINT,\n'
         '        owner_did VARCHAR,\n'
         '        actor_id VARCHAR,\n'
         '        created_at VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_insatsu_job_downstream_actor_src" ON '
         '"edge_insatsu_job_downstream_actor" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_insatsu_job_downstream_actor_dst" ON '
         '"edge_insatsu_job_downstream_actor" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_insatsu_job_downstream_actor_relation" ON '
         '"edge_insatsu_job_downstream_actor" (relation)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_insatsu_job_downstream_actor_job" ON '
         '"edge_insatsu_job_downstream_actor" (job_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_partner_did ON vertex_insatsu_print_partner '
         '(partner_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_partner_slug ON vertex_insatsu_print_partner '
         '(slug)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_partner_country_region ON '
         'vertex_insatsu_print_partner (country, region)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_partner_downstream ON '
         'vertex_insatsu_print_partner (downstream_actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_partner_print_methods ON '
         'vertex_insatsu_print_partner USING GIN (print_methods)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_partner_mail_classes ON '
         'vertex_insatsu_print_partner USING GIN (mail_classes)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_job_id ON vertex_insatsu_print_mail_job (job_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_job_status_created ON '
         'vertex_insatsu_print_mail_job (status, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_job_destination ON vertex_insatsu_print_mail_job '
         '(destination_country)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_job_partner ON vertex_insatsu_print_mail_job '
         '(partner_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_job_downstream ON vertex_insatsu_print_mail_job '
         '(downstream_actor_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_insatsu_job_case ON vertex_insatsu_print_mail_job '
         '(case_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_insatsu_partner_capacity AS\n'
         '    SELECT\n'
         '      partner_did,\n'
         '      max(slug) AS slug,\n'
         '      max(display_name) AS display_name,\n'
         '      max(country) AS country,\n'
         '      max(region) AS region,\n'
         '      max(downstream_actor_did) AS downstream_actor_did,\n'
         '      max(daily_capacity_pages) AS daily_capacity_pages,\n'
         '      min(base_cost_usd) AS base_cost_usd,\n'
         '      min(per_page_usd) AS per_page_usd,\n'
         '      count(*) AS profile_versions\n'
         '    FROM vertex_insatsu_print_partner\n'
         '    GROUP BY partner_did\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_insatsu_print_mail_job_status AS\n'
         '    SELECT\n'
         '      status,\n'
         '      destination_country,\n'
         '      partner_did,\n'
         '      count(*) AS job_count,\n'
         '      sum(page_count * quantity) AS total_pages,\n'
         '      sum(estimated_cost_usd) AS estimated_cost_usd,\n'
         '      max(created_at) AS latest_created_at\n'
         '    FROM vertex_insatsu_print_mail_job\n'
         '    GROUP BY status, destination_country, partner_did\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_insatsu_print_mail_job_status', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_insatsu_partner_capacity', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_insatsu_job_downstream_actor', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_insatsu_partner_mail_job', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_insatsu_print_mail_job', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_insatsu_print_partner', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
