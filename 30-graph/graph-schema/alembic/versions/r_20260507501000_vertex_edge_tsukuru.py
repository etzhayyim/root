"""Captured from Kysely migration 20260507501000_vertex_edge_tsukuru."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507501000_vertex_edge_tsukuru"
down_revision = 'r_20260507500000_vertex_yorishiro_flyio_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_manufacturer" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturer_key" ON '
         '"vertex_tsukuru_manufacturer" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturer_status" ON '
         '"vertex_tsukuru_manufacturer" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturer_created_at" ON '
         '"vertex_tsukuru_manufacturer" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturer_owner" ON '
         '"vertex_tsukuru_manufacturer" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_factory" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_factory_key" ON "vertex_tsukuru_factory" '
         '(vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_factory_status" ON '
         '"vertex_tsukuru_factory" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_factory_created_at" ON '
         '"vertex_tsukuru_factory" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_factory_owner" ON '
         '"vertex_tsukuru_factory" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_production_order" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_production_order_key" ON '
         '"vertex_tsukuru_production_order" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_production_order_status" ON '
         '"vertex_tsukuru_production_order" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_production_order_created_at" ON '
         '"vertex_tsukuru_production_order" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_production_order_owner" ON '
         '"vertex_tsukuru_production_order" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_production_progress" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_production_progress_key" ON '
         '"vertex_tsukuru_production_progress" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_production_progress_status" ON '
         '"vertex_tsukuru_production_progress" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_production_progress_created_at" ON '
         '"vertex_tsukuru_production_progress" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_production_progress_owner" ON '
         '"vertex_tsukuru_production_progress" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_quality_inspection" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_quality_inspection_key" ON '
         '"vertex_tsukuru_quality_inspection" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_quality_inspection_status" ON '
         '"vertex_tsukuru_quality_inspection" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_quality_inspection_created_at" ON '
         '"vertex_tsukuru_quality_inspection" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_quality_inspection_owner" ON '
         '"vertex_tsukuru_quality_inspection" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_manufacturing_cell" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturing_cell_key" ON '
         '"vertex_tsukuru_manufacturing_cell" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturing_cell_status" ON '
         '"vertex_tsukuru_manufacturing_cell" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturing_cell_created_at" ON '
         '"vertex_tsukuru_manufacturing_cell" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturing_cell_owner" ON '
         '"vertex_tsukuru_manufacturing_cell" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_manufacturing_output" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturing_output_key" ON '
         '"vertex_tsukuru_manufacturing_output" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturing_output_status" ON '
         '"vertex_tsukuru_manufacturing_output" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturing_output_created_at" ON '
         '"vertex_tsukuru_manufacturing_output" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_manufacturing_output_owner" ON '
         '"vertex_tsukuru_manufacturing_output" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_software_integration" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_software_integration_key" ON '
         '"vertex_tsukuru_software_integration" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_software_integration_status" ON '
         '"vertex_tsukuru_software_integration" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_software_integration_created_at" ON '
         '"vertex_tsukuru_software_integration" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_software_integration_owner" ON '
         '"vertex_tsukuru_software_integration" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_logistics_route" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_logistics_route_key" ON '
         '"vertex_tsukuru_logistics_route" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_logistics_route_status" ON '
         '"vertex_tsukuru_logistics_route" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_logistics_route_created_at" ON '
         '"vertex_tsukuru_logistics_route" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_logistics_route_owner" ON '
         '"vertex_tsukuru_logistics_route" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_autonomy_operation" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_autonomy_operation_key" ON '
         '"vertex_tsukuru_autonomy_operation" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_autonomy_operation_status" ON '
         '"vertex_tsukuru_autonomy_operation" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_autonomy_operation_created_at" ON '
         '"vertex_tsukuru_autonomy_operation" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_autonomy_operation_owner" ON '
         '"vertex_tsukuru_autonomy_operation" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_supplier_exchange_package" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_supplier_exchange_package_key" ON '
         '"vertex_tsukuru_supplier_exchange_package" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_supplier_exchange_package_status" ON '
         '"vertex_tsukuru_supplier_exchange_package" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_supplier_exchange_package_created_at" ON '
         '"vertex_tsukuru_supplier_exchange_package" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_supplier_exchange_package_owner" ON '
         '"vertex_tsukuru_supplier_exchange_package" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_euv_manufacturing_flow" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_euv_manufacturing_flow_key" ON '
         '"vertex_tsukuru_euv_manufacturing_flow" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_euv_manufacturing_flow_status" ON '
         '"vertex_tsukuru_euv_manufacturing_flow" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_euv_manufacturing_flow_created_at" ON '
         '"vertex_tsukuru_euv_manufacturing_flow" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_euv_manufacturing_flow_owner" ON '
         '"vertex_tsukuru_euv_manufacturing_flow" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_tsukuru_certification" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_certification_key" ON '
         '"vertex_tsukuru_certification" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_certification_status" ON '
         '"vertex_tsukuru_certification" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_certification_created_at" ON '
         '"vertex_tsukuru_certification" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_tsukuru_certification_owner" ON '
         '"vertex_tsukuru_certification" (owner_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_manufacturer_factory" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_factory_key" ON '
         '"edge_tsukuru_manufacturer_factory" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_factory_src" ON '
         '"edge_tsukuru_manufacturer_factory" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_factory_dst" ON '
         '"edge_tsukuru_manufacturer_factory" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_factory_relation" ON '
         '"edge_tsukuru_manufacturer_factory" (relation)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_manufacturer_order" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_order_key" ON '
         '"edge_tsukuru_manufacturer_order" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_order_src" ON '
         '"edge_tsukuru_manufacturer_order" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_order_dst" ON '
         '"edge_tsukuru_manufacturer_order" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_order_relation" ON '
         '"edge_tsukuru_manufacturer_order" (relation)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_manufacturer_certification" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_certification_key" ON '
         '"edge_tsukuru_manufacturer_certification" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_certification_src" ON '
         '"edge_tsukuru_manufacturer_certification" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_certification_dst" ON '
         '"edge_tsukuru_manufacturer_certification" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_manufacturer_certification_relation" ON '
         '"edge_tsukuru_manufacturer_certification" (relation)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_order_progress" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_progress_key" ON '
         '"edge_tsukuru_order_progress" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_progress_src" ON '
         '"edge_tsukuru_order_progress" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_progress_dst" ON '
         '"edge_tsukuru_order_progress" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_progress_relation" ON '
         '"edge_tsukuru_order_progress" (relation)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_order_inspection" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_inspection_key" ON '
         '"edge_tsukuru_order_inspection" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_inspection_src" ON '
         '"edge_tsukuru_order_inspection" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_inspection_dst" ON '
         '"edge_tsukuru_order_inspection" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_inspection_relation" ON '
         '"edge_tsukuru_order_inspection" (relation)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_order_manufacturing_cell" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_manufacturing_cell_key" ON '
         '"edge_tsukuru_order_manufacturing_cell" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_manufacturing_cell_src" ON '
         '"edge_tsukuru_order_manufacturing_cell" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_manufacturing_cell_dst" ON '
         '"edge_tsukuru_order_manufacturing_cell" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_manufacturing_cell_relation" ON '
         '"edge_tsukuru_order_manufacturing_cell" (relation)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_order_manufacturing_output" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_manufacturing_output_key" ON '
         '"edge_tsukuru_order_manufacturing_output" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_manufacturing_output_src" ON '
         '"edge_tsukuru_order_manufacturing_output" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_manufacturing_output_dst" ON '
         '"edge_tsukuru_order_manufacturing_output" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_manufacturing_output_relation" ON '
         '"edge_tsukuru_order_manufacturing_output" (relation)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_order_supplier_package" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_supplier_package_key" ON '
         '"edge_tsukuru_order_supplier_package" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_supplier_package_src" ON '
         '"edge_tsukuru_order_supplier_package" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_supplier_package_dst" ON '
         '"edge_tsukuru_order_supplier_package" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_supplier_package_relation" ON '
         '"edge_tsukuru_order_supplier_package" (relation)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_tsukuru_order_euv_flow" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_euv_flow_key" ON '
         '"edge_tsukuru_order_euv_flow" (edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_euv_flow_src" ON '
         '"edge_tsukuru_order_euv_flow" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_euv_flow_dst" ON '
         '"edge_tsukuru_order_euv_flow" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_tsukuru_order_euv_flow_relation" ON '
         '"edge_tsukuru_order_euv_flow" (relation)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS slug VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS legal_name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS country_iso3 VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS category VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS industry_code VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS verification_tier '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS risk_tier VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS onboarding_status '
         'VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_country_category\n'
         '      ON vertex_tsukuru_manufacturer (\n'
         '        country_iso3,\n'
         '        category\n'
         '      )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_did ON vertex_tsukuru_manufacturer '
         '(did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_slug ON vertex_tsukuru_manufacturer '
         '(slug)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_industry_code ON '
         'vertex_tsukuru_manufacturer (industry_code)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_risk_tier ON '
         'vertex_tsukuru_manufacturer (risk_tier)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_onboarding_tier\n'
         '      ON vertex_tsukuru_manufacturer (onboarding_status, verification_tier)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_tsukuru_order_mfg_status\n'
         '      ON vertex_tsukuru_production_order (\n'
         "        (value_json::jsonb ->> 'manufacturerDid'),\n"
         "        (value_json::jsonb ->> 'status')\n"
         '      )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_tsukuru_order_customer\n'
         "      ON vertex_tsukuru_production_order ((value_json::jsonb ->> 'customerId'))\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_tsukuru_inspection_order_result\n'
         '      ON vertex_tsukuru_quality_inspection (\n'
         "        (value_json::jsonb ->> 'productionOrderId'),\n"
         "        (value_json::jsonb ->> 'result')\n"
         '      )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tsukuru_platform_stats AS\n'
         '    SELECT\n'
         '      (SELECT count(*) FROM vertex_tsukuru_manufacturer) AS total_manufacturers,\n'
         '      (SELECT count(*) FROM vertex_tsukuru_factory) AS total_factories,\n'
         '      (SELECT count(*) FROM vertex_tsukuru_production_order) AS total_production_orders\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tsukuru_manufacturer_industry_counts AS\n'
         '    SELECT industry_code, risk_tier, onboarding_status, count(*) AS cnt\n'
         '    FROM vertex_tsukuru_manufacturer\n'
         '    GROUP BY industry_code, risk_tier, onboarding_status\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tsukuru_order_status_counts AS\n'
         "    SELECT value_json::jsonb ->> 'status' AS status, count(*) AS cnt\n"
         '    FROM vertex_tsukuru_production_order\n'
         "    GROUP BY value_json::jsonb ->> 'status'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_tsukuru_order_status_counts', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_tsukuru_manufacturer_industry_counts',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_tsukuru_platform_stats', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_order_euv_flow"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_order_supplier_package"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_order_manufacturing_output"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_order_manufacturing_cell"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_order_inspection"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_order_progress"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_manufacturer_certification"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_manufacturer_order"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_tsukuru_manufacturer_factory"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_certification"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_euv_manufacturing_flow"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_supplier_exchange_package"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_autonomy_operation"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_logistics_route"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_software_integration"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_manufacturing_output"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_manufacturing_cell"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_quality_inspection"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_production_progress"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_production_order"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_factory"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_tsukuru_manufacturer"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
