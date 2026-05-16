"""Captured from Kysely migration 20260424310000_vertex_bim_tables."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424310000_vertex_bim_tables"
down_revision = 'r_20260424300000_vertex_cad_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_project (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      rkey             VARCHAR,\n'
         '      repo             VARCHAR,\n'
         '      name             VARCHAR,\n'
         '      description      VARCHAR,\n'
         '      units_length     VARCHAR,\n'
         '      units_angle      VARCHAR,\n'
         '      units_time       VARCHAR,\n'
         '      true_north_rad   DOUBLE PRECISION,\n'
         '      world_origin_x   DOUBLE PRECISION,\n'
         '      world_origin_y   DOUBLE PRECISION,\n'
         '      world_origin_z   DOUBLE PRECISION,\n'
         '      head_revision_id VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_revision (\n'
         '      vertex_id          VARCHAR PRIMARY KEY,\n'
         '      _seq               BIGINT,\n'
         '      created_date       DATE,\n'
         '      sensitivity_ord    BIGINT,\n'
         '      owner_did          VARCHAR,\n'
         '      rkey               VARCHAR,\n'
         '      repo               VARCHAR,\n'
         '      project_id         VARCHAR,\n'
         '      parent_revision_id VARCHAR,\n'
         '      source_format      VARCHAR,\n'
         '      schema_version     VARCHAR,\n'
         '      source_blob_key    VARCHAR,\n'
         '      tessellation_key   VARCHAR,\n'
         '      tessellation_tol   DOUBLE PRECISION,\n'
         '      bbox_min_x         DOUBLE PRECISION,\n'
         '      bbox_min_y         DOUBLE PRECISION,\n'
         '      bbox_min_z         DOUBLE PRECISION,\n'
         '      bbox_max_x         DOUBLE PRECISION,\n'
         '      bbox_max_y         DOUBLE PRECISION,\n'
         '      bbox_max_z         DOUBLE PRECISION,\n'
         '      status             VARCHAR,\n'
         '      message            VARCHAR,\n'
         '      created_at         VARCHAR,\n'
         '      org_id             VARCHAR,\n'
         '      user_id            VARCHAR,\n'
         '      actor_id           VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_revision_project ON vertex_bim_revision '
         '(project_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_revision_status ON vertex_bim_revision '
         '(status)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_building (\n'
         '      vertex_id           VARCHAR PRIMARY KEY,\n'
         '      _seq                BIGINT,\n'
         '      created_date        DATE,\n'
         '      sensitivity_ord     BIGINT,\n'
         '      owner_did           VARCHAR,\n'
         '      rkey                VARCHAR,\n'
         '      repo                VARCHAR,\n'
         '      revision_id         VARCHAR,\n'
         '      project_id          VARCHAR,\n'
         '      global_id           VARCHAR,\n'
         '      name                VARCHAR,\n'
         '      reference_elevation DOUBLE PRECISION,\n'
         '      latitude_deg        DOUBLE PRECISION,\n'
         '      longitude_deg       DOUBLE PRECISION,\n'
         '      elevation_m         DOUBLE PRECISION,\n'
         '      created_at          VARCHAR,\n'
         '      org_id              VARCHAR,\n'
         '      user_id             VARCHAR,\n'
         '      actor_id            VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_building_revision ON vertex_bim_building '
         '(revision_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_storey (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      rkey             VARCHAR,\n'
         '      repo             VARCHAR,\n'
         '      revision_id      VARCHAR,\n'
         '      building_id      VARCHAR,\n'
         '      global_id        VARCHAR,\n'
         '      name             VARCHAR,\n'
         '      elevation        DOUBLE PRECISION,\n'
         '      height           DOUBLE PRECISION,\n'
         '      bbox_min_x       DOUBLE PRECISION,\n'
         '      bbox_min_y       DOUBLE PRECISION,\n'
         '      bbox_min_z       DOUBLE PRECISION,\n'
         '      bbox_max_x       DOUBLE PRECISION,\n'
         '      bbox_max_y       DOUBLE PRECISION,\n'
         '      bbox_max_z       DOUBLE PRECISION,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_storey_building ON vertex_bim_storey '
         '(building_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_storey_revision ON vertex_bim_storey '
         '(revision_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_space (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      rkey             VARCHAR,\n'
         '      repo             VARCHAR,\n'
         '      revision_id      VARCHAR,\n'
         '      storey_id        VARCHAR,\n'
         '      building_id      VARCHAR,\n'
         '      global_id        VARCHAR,\n'
         '      name             VARCHAR,\n'
         '      long_name        VARCHAR,\n'
         '      label            VARCHAR,\n'
         '      category         VARCHAR,\n'
         '      height           DOUBLE PRECISION,\n'
         '      gross_area_m2    DOUBLE PRECISION,\n'
         '      net_area_m2      DOUBLE PRECISION,\n'
         '      gross_volume_m3  DOUBLE PRECISION,\n'
         '      net_volume_m3    DOUBLE PRECISION,\n'
         '      boundary_json    VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_space_storey ON vertex_bim_space (storey_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_space_category ON vertex_bim_space (category)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_element (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      created_date      DATE,\n'
         '      sensitivity_ord   BIGINT,\n'
         '      owner_did         VARCHAR,\n'
         '      rkey              VARCHAR,\n'
         '      repo              VARCHAR,\n'
         '      revision_id       VARCHAR,\n'
         '      storey_id         VARCHAR,\n'
         '      building_id       VARCHAR,\n'
         '      global_id         VARCHAR,\n'
         '      name              VARCHAR,\n'
         '      kind              VARCHAR,\n'
         '      geometry_kind     VARCHAR,\n'
         '      mesh_blob_key     VARCHAR,\n'
         '      triangle_count    BIGINT,\n'
         '      base_color_hex    VARCHAR,\n'
         '      placement_json    VARCHAR,\n'
         '      classification_src VARCHAR,\n'
         '      classification_code VARCHAR,\n'
         '      material_json     VARCHAR,\n'
         '      gross_area_m2     DOUBLE PRECISION,\n'
         '      net_area_m2       DOUBLE PRECISION,\n'
         '      gross_volume_m3   DOUBLE PRECISION,\n'
         '      weight_kg         DOUBLE PRECISION,\n'
         '      length_m          DOUBLE PRECISION,\n'
         '      created_at        VARCHAR,\n'
         '      org_id            VARCHAR,\n'
         '      user_id           VARCHAR,\n'
         '      actor_id          VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_element_storey ON vertex_bim_element '
         '(storey_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_element_kind ON vertex_bim_element (kind)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_element_revision ON vertex_bim_element '
         '(revision_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_pset (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      rkey             VARCHAR,\n'
         '      repo             VARCHAR,\n'
         '      parent_vertex_id VARCHAR,\n'
         '      parent_kind      VARCHAR,\n'
         '      pset_name        VARCHAR,\n'
         '      props_json       VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_pset_parent ON vertex_bim_pset '
         '(parent_vertex_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_pset_name ON vertex_bim_pset (pset_name)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_annotation (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      rkey             VARCHAR,\n'
         '      repo             VARCHAR,\n'
         '      element_id       VARCHAR,\n'
         '      storey_id        VARCHAR,\n'
         '      kind             VARCHAR,\n'
         '      severity         VARCHAR,\n'
         '      text             VARCHAR,\n'
         '      viewpoint_json   VARCHAR,\n'
         '      assigned_to      VARCHAR,\n'
         '      reply_to         VARCHAR,\n'
         '      status           VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_annotation_element ON vertex_bim_annotation '
         '(element_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_annotation_status ON vertex_bim_annotation '
         '(status)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_bim_job (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      rkey             VARCHAR,\n'
         '      repo             VARCHAR,\n'
         '      job_kind         VARCHAR,\n'
         '      project_id       VARCHAR,\n'
         '      revision_id      VARCHAR,\n'
         '      target           VARCHAR,\n'
         '      source_blob_key  VARCHAR,\n'
         '      output_blob_key  VARCHAR,\n'
         '      status           VARCHAR,\n'
         '      error_message    VARCHAR,\n'
         '      estimated_secs   BIGINT,\n'
         '      started_at       VARCHAR,\n'
         '      finished_at      VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_job_revision ON vertex_bim_job (revision_id)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_job_status ON vertex_bim_job (status)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_bim_job_kind ON vertex_bim_job (job_kind)',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_bim_has_revision (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_revision_src ON edge_bim_has_revision '
         '(src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_revision_dst ON edge_bim_has_revision '
         '(dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_bim_has_building (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_building_src ON edge_bim_has_building '
         '(src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_building_dst ON edge_bim_has_building '
         '(dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_bim_has_storey (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_storey_src ON edge_bim_has_storey '
         '(src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_storey_dst ON edge_bim_has_storey '
         '(dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_bim_has_space (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_space_src ON edge_bim_has_space '
         '(src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_space_dst ON edge_bim_has_space '
         '(dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_bim_has_element (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_element_src ON edge_bim_has_element '
         '(src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_element_dst ON edge_bim_has_element '
         '(dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_bim_bounded_by (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_bounded_by_src ON edge_bim_bounded_by '
         '(src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_bounded_by_dst ON edge_bim_bounded_by '
         '(dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_bim_has_pset (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_pset_src ON edge_bim_has_pset (src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_has_pset_dst ON edge_bim_has_pset (dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_bim_annotated_by (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '      sensitivity_ord  BIGINT,\n'
         '      owner_did        VARCHAR,\n'
         '      created_at       VARCHAR,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_annotated_by_src ON edge_bim_annotated_by '
         '(src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_bim_annotated_by_dst ON edge_bim_annotated_by '
         '(dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_revision_dst', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_revision_src', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_bim_has_revision', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_building_dst', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_building_src', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_bim_has_building', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_storey_dst', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_storey_src', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_bim_has_storey', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_space_dst', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_space_src', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_bim_has_space', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_element_dst', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_element_src', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_bim_has_element', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_bounded_by_dst', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_bounded_by_src', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_bim_bounded_by', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_pset_dst', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_has_pset_src', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_bim_has_pset', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_annotated_by_dst', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_bim_annotated_by_src', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_bim_annotated_by', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_job_kind', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_job_status', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_job_revision', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_job', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_annotation_status', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_annotation_element', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_annotation', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_pset_name', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_pset_parent', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_pset', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_element_revision', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_element_kind', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_element_storey', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_element', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_space_category', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_space_storey', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_space', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_storey_revision', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_storey_building', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_storey', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_building_revision', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_building', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_revision_status', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_vertex_bim_revision_project', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_revision', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_bim_project', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
