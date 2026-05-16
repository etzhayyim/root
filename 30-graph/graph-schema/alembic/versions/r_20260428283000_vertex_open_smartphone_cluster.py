"""Captured from Kysely migration 20260428283000_vertex_open_smartphone_cluster."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428283000_vertex_open_smartphone_cluster"
down_revision = 'r_20260428280000_seed_claim_auto_challenge_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      bom_id VARCHAR NOT NULL,\n'
         '      design_name VARCHAR NOT NULL,\n'
         '      version VARCHAR NOT NULL,\n'
         '      soc_did VARCHAR,\n'
         '      modem_did VARCHAR,\n'
         '      os_did VARCHAR,\n'
         '      ems_facility_did VARCHAR,\n'
         '      target_price_usd DOUBLE PRECISION,\n'
         '      open_score_pct DOUBLE PRECISION,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom_line (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      line_id VARCHAR NOT NULL,\n'
         '      bom_did VARCHAR NOT NULL,\n'
         '      component_type VARCHAR NOT NULL,\n'
         '      vendor_name VARCHAR NOT NULL,\n'
         '      part_number VARCHAR NOT NULL,\n'
         '      unit_cost_usd DOUBLE PRECISION,\n'
         '      open_source BOOLEAN NOT NULL DEFAULT false,\n'
         '      license VARCHAR,\n'
         '      patent_did VARCHAR,\n'
         '      alternative_count INTEGER NOT NULL DEFAULT 0,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom_sourcer (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      bom_line_did VARCHAR NOT NULL,\n'
         '      alt_vendor VARCHAR NOT NULL,\n'
         '      alt_part_number VARCHAR NOT NULL,\n'
         '      alt_unit_cost_usd DOUBLE PRECISION,\n'
         '      open_source BOOLEAN NOT NULL DEFAULT false,\n'
         '      availability VARCHAR,\n'
         '      lead_time_weeks INTEGER,\n'
         '      notes VARCHAR,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_ems_facility (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      facility_id VARCHAR NOT NULL,\n'
         '      operator_name VARCHAR NOT NULL,\n'
         '      operator_lei VARCHAR,\n'
         '      location_iso3 VARCHAR NOT NULL,\n'
         '      city VARCHAR,\n'
         '      facility_type VARCHAR NOT NULL,\n'
         '      monthly_capacity_units BIGINT,\n'
         '      certifications VARCHAR,\n'
         '      rba_audit_status VARCHAR,\n'
         '      conflict_mineral_compliant BOOLEAN NOT NULL DEFAULT false,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_ems_order (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      order_id VARCHAR NOT NULL,\n'
         '      facility_did VARCHAR NOT NULL,\n'
         '      bom_did VARCHAR NOT NULL,\n'
         '      quantity_units BIGINT NOT NULL,\n'
         '      target_unit_cost_usd DOUBLE PRECISION,\n'
         '      delivery_quarter VARCHAR,\n'
         '      quality_standard VARCHAR,\n'
         "      order_status VARCHAR NOT NULL DEFAULT 'pending',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_spec (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      modem_id VARCHAR NOT NULL,\n'
         '      chip_name VARCHAR NOT NULL,\n'
         '      rat_support VARCHAR,\n'
         '      baseband_chip VARCHAR,\n'
         '      open_source_fw BOOLEAN NOT NULL DEFAULT false,\n'
         '      fw_license VARCHAR,\n'
         '      max_dl_mbps DOUBLE PRECISION,\n'
         '      max_ul_mbps DOUBLE PRECISION,\n'
         '      release_year INTEGER,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_type_approval (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      modem_did VARCHAR NOT NULL,\n'
         '      authority VARCHAR NOT NULL,\n'
         '      certificate_no VARCHAR NOT NULL,\n'
         '      jurisdiction_iso3 VARCHAR NOT NULL,\n'
         '      approved_at VARCHAR,\n'
         '      expiry_date VARCHAR,\n'
         '      rat_approved VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_sep_dep (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      modem_did VARCHAR NOT NULL,\n'
         '      patent_no VARCHAR NOT NULL,\n'
         '      holder_did VARCHAR,\n'
         '      rat VARCHAR NOT NULL,\n'
         '      frand_declared BOOLEAN NOT NULL DEFAULT false,\n'
         '      pool_id VARCHAR,\n'
         '      expiry_date VARCHAR,\n'
         "      blocker_status VARCHAR NOT NULL DEFAULT 'unknown',\n"
         "      severity VARCHAR NOT NULL DEFAULT 'medium',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_build (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      build_id VARCHAR NOT NULL,\n'
         '      os_name VARCHAR NOT NULL,\n'
         '      os_base VARCHAR NOT NULL,\n'
         '      version VARCHAR NOT NULL,\n'
         '      kernel_version VARCHAR,\n'
         '      soc_support VARCHAR,\n'
         '      open_blobs_pct DOUBLE PRECISION,\n'
         '      verified_boot BOOLEAN NOT NULL DEFAULT false,\n'
         '      build_url VARCHAR,\n'
         '      release_date VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_hal_driver (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      driver_id VARCHAR NOT NULL,\n'
         '      os_did VARCHAR NOT NULL,\n'
         '      soc_did VARCHAR,\n'
         '      sensor_did VARCHAR,\n'
         '      driver_type VARCHAR NOT NULL,\n'
         '      upstream_status VARCHAR,\n'
         '      vendor_blobs_required BOOLEAN NOT NULL DEFAULT false,\n'
         '      license VARCHAR,\n'
         '      version VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_ota (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      ota_id VARCHAR NOT NULL,\n'
         '      os_did VARCHAR NOT NULL,\n'
         '      from_version VARCHAR NOT NULL,\n'
         '      to_version VARCHAR NOT NULL,\n'
         '      release_notes_url VARCHAR,\n'
         '      patch_level VARCHAR,\n'
         '      cve_fixes VARCHAR,\n'
         '      ota_size_mb DOUBLE PRECISION,\n'
         '      signed BOOLEAN NOT NULL DEFAULT false,\n'
         '      release_date VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_sep (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      patent_no VARCHAR NOT NULL,\n'
         '      holder_did VARCHAR,\n'
         '      rat VARCHAR NOT NULL,\n'
         '      standard VARCHAR,\n'
         '      frand_declared BOOLEAN NOT NULL DEFAULT false,\n'
         '      pool_id VARCHAR,\n'
         '      expiry_date VARCHAR,\n'
         "      blocker_status VARCHAR NOT NULL DEFAULT 'unknown',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_pool (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      pool_id VARCHAR NOT NULL,\n'
         '      pool_name VARCHAR NOT NULL,\n'
         '      administrator VARCHAR,\n'
         '      standards_covered VARCHAR,\n'
         '      member_count INTEGER NOT NULL DEFAULT 0,\n'
         '      license_fee_usd_per_unit DOUBLE PRECISION,\n'
         '      frand_compliant BOOLEAN NOT NULL DEFAULT false,\n'
         '      url VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_dep (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      dep_id VARCHAR NOT NULL,\n'
         '      component_type VARCHAR NOT NULL,\n'
         '      component_did VARCHAR,\n'
         '      patent_no VARCHAR NOT NULL,\n'
         '      holder_did VARCHAR,\n'
         '      standard VARCHAR,\n'
         '      dependency_type VARCHAR NOT NULL,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_sensor_module (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      sensor_id VARCHAR NOT NULL,\n'
         '      sensor_type VARCHAR NOT NULL,\n'
         '      vendor VARCHAR NOT NULL,\n'
         '      model VARCHAR NOT NULL,\n'
         '      interface_type VARCHAR,\n'
         '      open_driver BOOLEAN NOT NULL DEFAULT false,\n'
         '      mainline_kernel_status VARCHAR,\n'
         '      pixel_count_mp DOUBLE PRECISION,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_sensor_calibration (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      sensor_did VARCHAR NOT NULL,\n'
         '      calibration_type VARCHAR NOT NULL,\n'
         '      standard_ref VARCHAR,\n'
         '      calibrated_at VARCHAR NOT NULL,\n'
         '      valid_until VARCHAR,\n'
         '      calibrated_by VARCHAR,\n'
         '      pass BOOLEAN NOT NULL DEFAULT false,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_design (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      chip_id VARCHAR NOT NULL,\n'
         '      chip_name VARCHAR NOT NULL,\n'
         '      isa VARCHAR NOT NULL,\n'
         '      process_node_nm INTEGER,\n'
         '      die_area_mm2 DOUBLE PRECISION,\n'
         '      transistor_count_b DOUBLE PRECISION,\n'
         '      open_source_rtl BOOLEAN NOT NULL DEFAULT false,\n'
         '      rtl_license VARCHAR,\n'
         '      fab_did VARCHAR,\n'
         '      tape_out_date VARCHAR,\n'
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_fab_order (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      order_id VARCHAR NOT NULL,\n'
         '      chip_did VARCHAR NOT NULL,\n'
         '      fab_did VARCHAR NOT NULL,\n'
         '      process_node_nm INTEGER,\n'
         '      wafer_qty INTEGER,\n'
         '      delivery_estimate VARCHAR,\n'
         '      price_usd_k DOUBLE PRECISION,\n'
         "      order_status VARCHAR NOT NULL DEFAULT 'pending',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 1,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_export_flag (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      chip_did VARCHAR NOT NULL,\n'
         '      flag_type VARCHAR NOT NULL,\n'
         '      entity_list_entry VARCHAR,\n'
         '      jurisdiction VARCHAR NOT NULL,\n'
         '      flagged_at VARCHAR NOT NULL,\n'
         "      severity VARCHAR NOT NULL DEFAULT 'medium',\n"
         "      status VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2,\n'
         '      org_id VARCHAR NOT NULL,\n'
         '      user_id VARCHAR NOT NULL,\n'
         '      actor_id VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_soc_export_flag', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_soc_fab_order', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_soc_design', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_sensor_calibration', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_sensor_module', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_patent_dep', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_patent_pool', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_patent_sep', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_os_ota', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_os_hal_driver', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_os_build', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_modem_sep_dep', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_modem_type_approval', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_modem_spec', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_ems_order', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_ems_facility', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_bom_sourcer', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_bom_line', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_smartphone_bom', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
