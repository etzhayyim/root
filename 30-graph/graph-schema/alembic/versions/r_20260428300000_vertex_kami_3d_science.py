"""Captured from Kysely migration 20260428300000_vertex_kami_3d_science."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428300000_vertex_kami_3d_science"
down_revision = 'r_20260428290000_seed_legal_corpus_body_embed_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kami_model_def (\n'
         '      vertex_id        VARCHAR PRIMARY KEY,\n'
         '      slug             VARCHAR NOT NULL,\n'
         '      model_kind       VARCHAR NOT NULL,\n'
         '      lod_levels       BIGINT  DEFAULT 1,\n'
         '      mesh_uri         VARCHAR,\n'
         '      mesh_uri_lod1    VARCHAR,\n'
         '      mesh_uri_lod2    VARCHAR,\n'
         '      bbox_min_x       DOUBLE PRECISION DEFAULT 0,\n'
         '      bbox_min_y       DOUBLE PRECISION DEFAULT 0,\n'
         '      bbox_min_z       DOUBLE PRECISION DEFAULT 0,\n'
         '      bbox_max_x       DOUBLE PRECISION DEFAULT 1,\n'
         '      bbox_max_y       DOUBLE PRECISION DEFAULT 1,\n'
         '      bbox_max_z       DOUBLE PRECISION DEFAULT 1,\n'
         '      pivot_x          DOUBLE PRECISION DEFAULT 0,\n'
         '      pivot_y          DOUBLE PRECISION DEFAULT 0,\n'
         '      pivot_z          DOUBLE PRECISION DEFAULT 0,\n'
         '      material_json    VARCHAR,\n'
         '      taxonomy_did     VARCHAR,\n'
         "      render_kind      VARCHAR NOT NULL DEFAULT 'glb',\n"
         "      source           VARCHAR NOT NULL DEFAULT 'procedural',\n"
         '      version          BIGINT  DEFAULT 1,\n'
         "      status           VARCHAR NOT NULL DEFAULT 'active',\n"
         '      created_at       VARCHAR NOT NULL,\n'
         '      sensitivity_ord  BIGINT  DEFAULT 1,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR,\n'
         '      owner_did        VARCHAR,\n'
         '      _seq             BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_kami_model_def_kind\n'
         '      ON vertex_kami_model_def (model_kind, status)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_kami_model_def_taxonomy\n'
         '      ON vertex_kami_model_def (taxonomy_did)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_kami_model_def_slug\n'
         '      ON vertex_kami_model_def (slug)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kami_model_instance (\n'
         '      vertex_id          VARCHAR PRIMARY KEY,\n'
         '      model_def_id       VARCHAR NOT NULL,\n'
         '      tile_h3            VARCHAR NOT NULL,\n'
         '      world_x            DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      world_y            DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      world_z            DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      scale_x            DOUBLE PRECISION DEFAULT 1,\n'
         '      scale_y            DOUBLE PRECISION DEFAULT 1,\n'
         '      scale_z            DOUBLE PRECISION DEFAULT 1,\n'
         '      rot_yaw            DOUBLE PRECISION DEFAULT 0,\n'
         '      rot_pitch          DOUBLE PRECISION DEFAULT 0,\n'
         '      rot_roll           DOUBLE PRECISION DEFAULT 0,\n'
         '      color_r            DOUBLE PRECISION,\n'
         '      color_g            DOUBLE PRECISION,\n'
         '      color_b            DOUBLE PRECISION,\n'
         '      spatial_vertex_id  VARCHAR,\n'
         '      taxonomy_did       VARCHAR,\n'
         '      annotation_json    VARCHAR,\n'
         '      visibility_range_m DOUBLE PRECISION DEFAULT 200,\n'
         '      created_at         VARCHAR NOT NULL,\n'
         '      sensitivity_ord    BIGINT  DEFAULT 1,\n'
         '      org_id             VARCHAR,\n'
         '      user_id            VARCHAR,\n'
         '      actor_id           VARCHAR,\n'
         '      owner_did          VARCHAR,\n'
         '      _seq               BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_kami_instance_tile\n'
         '      ON vertex_kami_model_instance (tile_h3)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_kami_instance_model\n'
         '      ON vertex_kami_model_instance (model_def_id)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_kami_instance_taxonomy\n'
         '      ON vertex_kami_model_instance (taxonomy_did)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_kami_material_def (\n'
         '      vertex_id            VARCHAR PRIMARY KEY,\n'
         '      material_name        VARCHAR NOT NULL,\n'
         '      albedo_r             DOUBLE PRECISION DEFAULT 0.8,\n'
         '      albedo_g             DOUBLE PRECISION DEFAULT 0.8,\n'
         '      albedo_b             DOUBLE PRECISION DEFAULT 0.8,\n'
         '      albedo_a             DOUBLE PRECISION DEFAULT 1,\n'
         '      metallic             DOUBLE PRECISION DEFAULT 0,\n'
         '      roughness            DOUBLE PRECISION DEFAULT 0.5,\n'
         '      emissive_r           DOUBLE PRECISION DEFAULT 0,\n'
         '      emissive_g           DOUBLE PRECISION DEFAULT 0,\n'
         '      emissive_b           DOUBLE PRECISION DEFAULT 0,\n'
         '      opacity              DOUBLE PRECISION DEFAULT 1,\n'
         '      double_sided         BOOLEAN DEFAULT false,\n'
         '      albedo_texture_uri   VARCHAR,\n'
         '      normal_texture_uri   VARCHAR,\n'
         '      orm_texture_uri      VARCHAR,\n'
         '      element_did          VARCHAR,\n'
         '      compound_formula     VARCHAR,\n'
         '      crystal_system       VARCHAR,\n'
         '      material_class       VARCHAR,\n'
         '      created_at           VARCHAR NOT NULL,\n'
         '      sensitivity_ord      BIGINT  DEFAULT 1,\n'
         '      org_id               VARCHAR,\n'
         '      user_id              VARCHAR,\n'
         '      actor_id             VARCHAR,\n'
         '      owner_did            VARCHAR,\n'
         '      _seq                 BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_kami_material_element\n'
         '      ON vertex_kami_material_def (element_did)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_periodic_element (\n'
         '      vertex_id            VARCHAR PRIMARY KEY,\n'
         '      atomic_number        BIGINT NOT NULL,\n'
         '      symbol               VARCHAR NOT NULL,\n'
         '      element_name_en      VARCHAR NOT NULL,\n'
         '      element_name_ja      VARCHAR,\n'
         '      atomic_mass          DOUBLE PRECISION,\n'
         '      electronegativity    DOUBLE PRECISION,\n'
         '      atomic_radius_pm     DOUBLE PRECISION,\n'
         '      covalent_radius_pm   DOUBLE PRECISION,\n'
         '      van_der_waals_r_pm   DOUBLE PRECISION,\n'
         '      melting_point_k      DOUBLE PRECISION,\n'
         '      boiling_point_k      DOUBLE PRECISION,\n'
         '      density_gcc          DOUBLE PRECISION,\n'
         '      electron_config      VARCHAR,\n'
         '      period               BIGINT,\n'
         '      group_number         BIGINT,\n'
         '      block                VARCHAR,\n'
         '      category             VARCHAR,\n'
         '      cas_number           VARCHAR,\n'
         '      kami_sphere_r_pm     DOUBLE PRECISION,\n'
         '      kami_color_r         DOUBLE PRECISION DEFAULT 0.8,\n'
         '      kami_color_g         DOUBLE PRECISION DEFAULT 0.8,\n'
         '      kami_color_b         DOUBLE PRECISION DEFAULT 0.8,\n'
         '      created_at           VARCHAR NOT NULL,\n'
         '      sensitivity_ord      BIGINT  DEFAULT 1,\n'
         '      org_id               VARCHAR,\n'
         '      user_id              VARCHAR,\n'
         '      actor_id             VARCHAR,\n'
         '      owner_did            VARCHAR,\n'
         '      _seq                 BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_periodic_element_symbol\n'
         '      ON vertex_periodic_element (symbol)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_periodic_element_atomic_number\n'
         '      ON vertex_periodic_element (atomic_number)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_scientific_taxon (\n'
         '      vertex_id          VARCHAR PRIMARY KEY,\n'
         '      taxon_rank         VARCHAR NOT NULL,\n'
         '      scientific_name    VARCHAR NOT NULL,\n'
         '      common_name_ja     VARCHAR,\n'
         '      common_name_en     VARCHAR,\n'
         '      taxon_code         VARCHAR,\n'
         '      parent_taxon_did   VARCHAR,\n'
         '      domain_kind        VARCHAR NOT NULL,\n'
         '      kami_model_def_id  VARCHAR,\n'
         '      kami_canopy_shape  VARCHAR,\n'
         '      render_profile_json VARCHAR,\n'
         '      description        VARCHAR,\n'
         "      source             VARCHAR NOT NULL DEFAULT 'ncbi',\n"
         '      created_at         VARCHAR NOT NULL,\n'
         '      sensitivity_ord    BIGINT  DEFAULT 1,\n'
         '      org_id             VARCHAR,\n'
         '      user_id            VARCHAR,\n'
         '      actor_id           VARCHAR,\n'
         '      owner_did          VARCHAR,\n'
         '      _seq               BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_scientific_taxon_domain\n'
         '      ON vertex_scientific_taxon (domain_kind, taxon_rank)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_scientific_taxon_parent\n'
         '      ON vertex_scientific_taxon (parent_taxon_did)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_scientific_taxon_code\n'
         '      ON vertex_scientific_taxon (taxon_code)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_scientific_taxon_model\n'
         '      ON vertex_scientific_taxon (kami_model_def_id)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_mineral (\n'
         '      vertex_id          VARCHAR PRIMARY KEY,\n'
         '      ima_symbol         VARCHAR,\n'
         '      mineral_name       VARCHAR NOT NULL,\n'
         '      chemical_formula   VARCHAR NOT NULL,\n'
         '      crystal_system     VARCHAR,\n'
         '      crystal_class      VARCHAR,\n'
         '      space_group        VARCHAR,\n'
         '      hardness_min       DOUBLE PRECISION,\n'
         '      hardness_max       DOUBLE PRECISION,\n'
         '      density_min        DOUBLE PRECISION,\n'
         '      density_max        DOUBLE PRECISION,\n'
         '      luster             VARCHAR,\n'
         '      color_common       VARCHAR,\n'
         '      streak             VARCHAR,\n'
         '      cleavage           VARCHAR,\n'
         '      ima_number         VARCHAR,\n'
         '      discovery_year     BIGINT,\n'
         '      element_dids_json  VARCHAR,\n'
         '      kami_model_def_id  VARCHAR,\n'
         '      taxon_did          VARCHAR,\n'
         '      created_at         VARCHAR NOT NULL,\n'
         '      sensitivity_ord    BIGINT  DEFAULT 1,\n'
         '      org_id             VARCHAR,\n'
         '      user_id            VARCHAR,\n'
         '      actor_id           VARCHAR,\n'
         '      owner_did          VARCHAR,\n'
         '      _seq               BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_mineral_crystal_system\n'
         '      ON vertex_mineral (crystal_system)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_mineral_ima_symbol\n'
         '      ON vertex_mineral (ima_symbol)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_scientific_paper (\n'
         '      vertex_id          VARCHAR PRIMARY KEY,\n'
         '      doi                VARCHAR,\n'
         '      arxiv_id           VARCHAR,\n'
         '      pmid               VARCHAR,\n'
         '      title              VARCHAR NOT NULL,\n'
         '      abstract_text      VARCHAR,\n'
         '      journal            VARCHAR,\n'
         '      venue              VARCHAR,\n'
         '      published_at       VARCHAR,\n'
         '      year               BIGINT,\n'
         '      citation_count     BIGINT,\n'
         '      domain             VARCHAR,\n'
         '      subdomain          VARCHAR,\n'
         '      embedding_norm     DOUBLE PRECISION,\n'
         '      ivf_cluster_id     BIGINT,\n'
         "      source             VARCHAR NOT NULL DEFAULT 'arxiv',\n"
         "      status             VARCHAR NOT NULL DEFAULT 'raw',\n"
         '      created_at         VARCHAR NOT NULL,\n'
         '      sensitivity_ord    BIGINT  DEFAULT 1,\n'
         '      org_id             VARCHAR,\n'
         '      user_id            VARCHAR,\n'
         '      actor_id           VARCHAR,\n'
         '      owner_did          VARCHAR,\n'
         '      _seq               BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_scientific_paper_domain\n'
         '      ON vertex_scientific_paper (domain, year)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_scientific_paper_status\n'
         '      ON vertex_scientific_paper (status)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_scientific_paper_ivf\n'
         '      ON vertex_scientific_paper (ivf_cluster_id)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_scientific_paper_doi\n'
         '      ON vertex_scientific_paper (doi)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_taxon_model (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR NOT NULL,\n'
         '      dst_vid          VARCHAR NOT NULL,\n'
         "      model_role       VARCHAR NOT NULL DEFAULT 'primary',\n"
         '      confidence       DOUBLE PRECISION DEFAULT 1.0,\n'
         '      created_at       VARCHAR NOT NULL,\n'
         '      sensitivity_ord  BIGINT  DEFAULT 1,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR,\n'
         '      owner_did        VARCHAR,\n'
         '      _seq             BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_taxon_model_src\n'
         '      ON edge_taxon_model (src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_taxon_model_dst\n'
         '      ON edge_taxon_model (dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_model_material (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR NOT NULL,\n'
         '      dst_vid          VARCHAR NOT NULL,\n'
         "      material_slot    VARCHAR NOT NULL DEFAULT 'body',\n"
         '      created_at       VARCHAR NOT NULL,\n'
         '      sensitivity_ord  BIGINT  DEFAULT 1,\n'
         '      org_id           VARCHAR,\n'
         '      user_id          VARCHAR,\n'
         '      actor_id         VARCHAR,\n'
         '      owner_did        VARCHAR,\n'
         '      _seq             BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_model_material_src\n'
         '      ON edge_model_material (src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_material_element (\n'
         '      edge_id            VARCHAR PRIMARY KEY,\n'
         '      src_vid            VARCHAR NOT NULL,\n'
         '      dst_vid            VARCHAR NOT NULL,\n'
         '      weight_fraction    DOUBLE PRECISION,\n'
         '      created_at         VARCHAR NOT NULL,\n'
         '      sensitivity_ord    BIGINT  DEFAULT 1,\n'
         '      org_id             VARCHAR,\n'
         '      user_id            VARCHAR,\n'
         '      actor_id           VARCHAR,\n'
         '      owner_did          VARCHAR,\n'
         '      _seq               BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_material_element_src\n'
         '      ON edge_material_element (src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_material_element_dst\n'
         '      ON edge_material_element (dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_paper_taxon (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      src_vid         VARCHAR NOT NULL,\n'
         '      dst_vid         VARCHAR NOT NULL,\n'
         "      relation_kind   VARCHAR NOT NULL DEFAULT 'describes',\n"
         '      confidence      DOUBLE PRECISION DEFAULT 0.8,\n'
         '      created_at      VARCHAR NOT NULL,\n'
         '      sensitivity_ord BIGINT  DEFAULT 1,\n'
         '      org_id          VARCHAR,\n'
         '      user_id         VARCHAR,\n'
         '      actor_id        VARCHAR,\n'
         '      owner_did       VARCHAR,\n'
         '      _seq            BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_paper_taxon_src\n'
         '      ON edge_paper_taxon (src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_paper_taxon_dst\n'
         '      ON edge_paper_taxon (dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_paper_element (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      src_vid         VARCHAR NOT NULL,\n'
         '      dst_vid         VARCHAR NOT NULL,\n'
         "      relation_kind   VARCHAR NOT NULL DEFAULT 'characterizes',\n"
         '      created_at      VARCHAR NOT NULL,\n'
         '      sensitivity_ord BIGINT  DEFAULT 1,\n'
         '      org_id          VARCHAR,\n'
         '      user_id         VARCHAR,\n'
         '      actor_id        VARCHAR,\n'
         '      owner_did       VARCHAR,\n'
         '      _seq            BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_paper_element_src\n'
         '      ON edge_paper_element (src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kami_tile_model_density AS\n'
         '    SELECT\n'
         '      tile_h3,\n'
         '      model_kind,\n'
         '      COUNT(*) AS instance_count,\n'
         '      COUNT(DISTINCT model_def_id) AS model_def_count,\n'
         '      MIN(world_x) AS min_x,\n'
         '      MAX(world_x) AS max_x,\n'
         '      MIN(world_z) AS min_z,\n'
         '      MAX(world_z) AS max_z\n'
         '    FROM vertex_kami_model_instance mi\n'
         '    JOIN vertex_kami_model_def md ON md.vertex_id = mi.model_def_id\n'
         '    GROUP BY tile_h3, model_kind\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_mv_kami_tile_density_h3\n'
         '      ON mv_kami_tile_model_density (tile_h3)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_taxon_model_coverage AS\n'
         '    SELECT\n'
         '      domain_kind,\n'
         '      taxon_rank,\n'
         '      COUNT(*)                          AS total_taxa,\n'
         '      COUNT(kami_model_def_id)          AS modelled_taxa,\n'
         '      COUNT(kami_canopy_shape)          AS vegetation_taxa,\n'
         '      CAST(COUNT(kami_model_def_id) AS DOUBLE PRECISION)\n'
         '        / CAST(COUNT(*) AS DOUBLE PRECISION) AS model_coverage_ratio\n'
         '    FROM vertex_scientific_taxon\n'
         '    GROUP BY domain_kind, taxon_rank\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_science_paper_domain_stats AS\n'
         '    SELECT\n'
         '      domain,\n'
         '      year,\n'
         '      COUNT(*)                                 AS paper_count,\n'
         "      COUNT(CASE WHEN status = 'embedded' THEN 1 END) AS embedded_count,\n"
         "      COUNT(CASE WHEN status = 'linked'   THEN 1 END) AS linked_count,\n"
         '      AVG(citation_count)                      AS avg_citations\n'
         '    FROM vertex_scientific_paper\n'
         '    GROUP BY domain, year\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_element_material_coverage AS\n'
         '    SELECT\n'
         '      el.symbol,\n'
         '      el.atomic_number,\n'
         '      el.category,\n'
         '      COUNT(eme.src_vid) AS material_count\n'
         '    FROM vertex_periodic_element el\n'
         '    LEFT JOIN edge_material_element eme ON eme.dst_vid = el.vertex_id\n'
         '    GROUP BY el.symbol, el.atomic_number, el.category\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_element_material_coverage', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_science_paper_domain_stats', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_taxon_model_coverage', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kami_tile_model_density', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_paper_element', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_paper_taxon', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_material_element', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_model_material', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_taxon_model', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_scientific_paper', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_mineral', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_scientific_taxon', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_periodic_element', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kami_material_def', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kami_model_instance', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_kami_model_def', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
