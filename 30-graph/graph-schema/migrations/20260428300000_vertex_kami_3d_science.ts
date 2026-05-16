import type { Kysely } from "kysely";
import { sql } from "kysely";

// kami engine 3D model registry + scientific knowledge graph.
//
// Addresses two needs in one migration:
//   A) 3D model schema — lets maps assemble scenes from DB instead of
//      hardcoding AABB boxes or B2 GLB URIs in JS.
//   B) Scientific classification — periodic table, biological taxonomy,
//      minerals, and paper ingest feed vertex renders + knowledge graph.
//
// Kami WASM surface:
//   set_buildings_json(json)        — AABB boxes (existing)
//   set_mesh_tile(h3, glb)          — photogrammetry GLB (existing)
//   [new] set_vegetation_json(json) — TaxonomicProfile array (kami-vegetation)
//   [new] set_atoms_json(json)      — CPK sphere array (kami-render sphere)
//   [new] set_crystals_json(json)   — unit cell GLB reference
//
// DB→maps assembly flow (new getChunkModels XRPC):
//   SELECT mi.*, md.*, st.render_profile_json
//   FROM vertex_kami_model_instance mi
//   JOIN vertex_kami_model_def md ON md.vertex_id = mi.model_def_id
//   LEFT JOIN vertex_scientific_taxon st ON st.vertex_id = mi.taxonomy_did
//   WHERE mi.tile_h3 = $tile

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── A1: 3D model definition registry ──────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kami_model_def (
      vertex_id        VARCHAR PRIMARY KEY,
      slug             VARCHAR NOT NULL,
      model_kind       VARCHAR NOT NULL,
      lod_levels       BIGINT  DEFAULT 1,
      mesh_uri         VARCHAR,
      mesh_uri_lod1    VARCHAR,
      mesh_uri_lod2    VARCHAR,
      bbox_min_x       DOUBLE PRECISION DEFAULT 0,
      bbox_min_y       DOUBLE PRECISION DEFAULT 0,
      bbox_min_z       DOUBLE PRECISION DEFAULT 0,
      bbox_max_x       DOUBLE PRECISION DEFAULT 1,
      bbox_max_y       DOUBLE PRECISION DEFAULT 1,
      bbox_max_z       DOUBLE PRECISION DEFAULT 1,
      pivot_x          DOUBLE PRECISION DEFAULT 0,
      pivot_y          DOUBLE PRECISION DEFAULT 0,
      pivot_z          DOUBLE PRECISION DEFAULT 0,
      material_json    VARCHAR,
      taxonomy_did     VARCHAR,
      render_kind      VARCHAR NOT NULL DEFAULT 'glb',
      source           VARCHAR NOT NULL DEFAULT 'procedural',
      version          BIGINT  DEFAULT 1,
      status           VARCHAR NOT NULL DEFAULT 'active',
      created_at       VARCHAR NOT NULL,
      sensitivity_ord  BIGINT  DEFAULT 1,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      owner_did        VARCHAR,
      _seq             BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kami_model_def_kind
      ON vertex_kami_model_def (model_kind, status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kami_model_def_taxonomy
      ON vertex_kami_model_def (taxonomy_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kami_model_def_slug
      ON vertex_kami_model_def (slug)
  `.execute(db);

  // ── A2: placed model instances (per H3 tile) ──────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kami_model_instance (
      vertex_id          VARCHAR PRIMARY KEY,
      model_def_id       VARCHAR NOT NULL,
      tile_h3            VARCHAR NOT NULL,
      world_x            DOUBLE PRECISION NOT NULL DEFAULT 0,
      world_y            DOUBLE PRECISION NOT NULL DEFAULT 0,
      world_z            DOUBLE PRECISION NOT NULL DEFAULT 0,
      scale_x            DOUBLE PRECISION DEFAULT 1,
      scale_y            DOUBLE PRECISION DEFAULT 1,
      scale_z            DOUBLE PRECISION DEFAULT 1,
      rot_yaw            DOUBLE PRECISION DEFAULT 0,
      rot_pitch          DOUBLE PRECISION DEFAULT 0,
      rot_roll           DOUBLE PRECISION DEFAULT 0,
      color_r            DOUBLE PRECISION,
      color_g            DOUBLE PRECISION,
      color_b            DOUBLE PRECISION,
      spatial_vertex_id  VARCHAR,
      taxonomy_did       VARCHAR,
      annotation_json    VARCHAR,
      visibility_range_m DOUBLE PRECISION DEFAULT 200,
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    BIGINT  DEFAULT 1,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      owner_did          VARCHAR,
      _seq               BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kami_instance_tile
      ON vertex_kami_model_instance (tile_h3)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kami_instance_model
      ON vertex_kami_model_instance (model_def_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kami_instance_taxonomy
      ON vertex_kami_model_instance (taxonomy_did)
  `.execute(db);

  // ── A3: PBR material catalog ──────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kami_material_def (
      vertex_id            VARCHAR PRIMARY KEY,
      material_name        VARCHAR NOT NULL,
      albedo_r             DOUBLE PRECISION DEFAULT 0.8,
      albedo_g             DOUBLE PRECISION DEFAULT 0.8,
      albedo_b             DOUBLE PRECISION DEFAULT 0.8,
      albedo_a             DOUBLE PRECISION DEFAULT 1,
      metallic             DOUBLE PRECISION DEFAULT 0,
      roughness            DOUBLE PRECISION DEFAULT 0.5,
      emissive_r           DOUBLE PRECISION DEFAULT 0,
      emissive_g           DOUBLE PRECISION DEFAULT 0,
      emissive_b           DOUBLE PRECISION DEFAULT 0,
      opacity              DOUBLE PRECISION DEFAULT 1,
      double_sided         BOOLEAN DEFAULT false,
      albedo_texture_uri   VARCHAR,
      normal_texture_uri   VARCHAR,
      orm_texture_uri      VARCHAR,
      element_did          VARCHAR,
      compound_formula     VARCHAR,
      crystal_system       VARCHAR,
      material_class       VARCHAR,
      created_at           VARCHAR NOT NULL,
      sensitivity_ord      BIGINT  DEFAULT 1,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR,
      owner_did            VARCHAR,
      _seq                 BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kami_material_element
      ON vertex_kami_material_def (element_did)
  `.execute(db);

  // ── B1: periodic table (118 elements) ────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_periodic_element (
      vertex_id            VARCHAR PRIMARY KEY,
      atomic_number        BIGINT NOT NULL,
      symbol               VARCHAR NOT NULL,
      element_name_en      VARCHAR NOT NULL,
      element_name_ja      VARCHAR,
      atomic_mass          DOUBLE PRECISION,
      electronegativity    DOUBLE PRECISION,
      atomic_radius_pm     DOUBLE PRECISION,
      covalent_radius_pm   DOUBLE PRECISION,
      van_der_waals_r_pm   DOUBLE PRECISION,
      melting_point_k      DOUBLE PRECISION,
      boiling_point_k      DOUBLE PRECISION,
      density_gcc          DOUBLE PRECISION,
      electron_config      VARCHAR,
      period               BIGINT,
      group_number         BIGINT,
      block                VARCHAR,
      category             VARCHAR,
      cas_number           VARCHAR,
      kami_sphere_r_pm     DOUBLE PRECISION,
      kami_color_r         DOUBLE PRECISION DEFAULT 0.8,
      kami_color_g         DOUBLE PRECISION DEFAULT 0.8,
      kami_color_b         DOUBLE PRECISION DEFAULT 0.8,
      created_at           VARCHAR NOT NULL,
      sensitivity_ord      BIGINT  DEFAULT 1,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR,
      owner_did            VARCHAR,
      _seq                 BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_periodic_element_symbol
      ON vertex_periodic_element (symbol)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_periodic_element_atomic_number
      ON vertex_periodic_element (atomic_number)
  `.execute(db);

  // ── B2: universal scientific taxonomy ────────────────────────────────
  // Covers: NCBI taxonomy (biology), IMA (mineralogy),
  //         IUPAC/CAS (chemistry), MSE (materials).
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_scientific_taxon (
      vertex_id          VARCHAR PRIMARY KEY,
      taxon_rank         VARCHAR NOT NULL,
      scientific_name    VARCHAR NOT NULL,
      common_name_ja     VARCHAR,
      common_name_en     VARCHAR,
      taxon_code         VARCHAR,
      parent_taxon_did   VARCHAR,
      domain_kind        VARCHAR NOT NULL,
      kami_model_def_id  VARCHAR,
      kami_canopy_shape  VARCHAR,
      render_profile_json VARCHAR,
      description        VARCHAR,
      source             VARCHAR NOT NULL DEFAULT 'ncbi',
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    BIGINT  DEFAULT 1,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      owner_did          VARCHAR,
      _seq               BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_scientific_taxon_domain
      ON vertex_scientific_taxon (domain_kind, taxon_rank)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_scientific_taxon_parent
      ON vertex_scientific_taxon (parent_taxon_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_scientific_taxon_code
      ON vertex_scientific_taxon (taxon_code)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_scientific_taxon_model
      ON vertex_scientific_taxon (kami_model_def_id)
  `.execute(db);

  // ── B3: IMA mineral database ──────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_mineral (
      vertex_id          VARCHAR PRIMARY KEY,
      ima_symbol         VARCHAR,
      mineral_name       VARCHAR NOT NULL,
      chemical_formula   VARCHAR NOT NULL,
      crystal_system     VARCHAR,
      crystal_class      VARCHAR,
      space_group        VARCHAR,
      hardness_min       DOUBLE PRECISION,
      hardness_max       DOUBLE PRECISION,
      density_min        DOUBLE PRECISION,
      density_max        DOUBLE PRECISION,
      luster             VARCHAR,
      color_common       VARCHAR,
      streak             VARCHAR,
      cleavage           VARCHAR,
      ima_number         VARCHAR,
      discovery_year     BIGINT,
      element_dids_json  VARCHAR,
      kami_model_def_id  VARCHAR,
      taxon_did          VARCHAR,
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    BIGINT  DEFAULT 1,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      owner_did          VARCHAR,
      _seq               BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_mineral_crystal_system
      ON vertex_mineral (crystal_system)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_mineral_ima_symbol
      ON vertex_mineral (ima_symbol)
  `.execute(db);

  // ── B4: scientific paper ingest ───────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_scientific_paper (
      vertex_id          VARCHAR PRIMARY KEY,
      doi                VARCHAR,
      arxiv_id           VARCHAR,
      pmid               VARCHAR,
      title              VARCHAR NOT NULL,
      abstract_text      VARCHAR,
      journal            VARCHAR,
      venue              VARCHAR,
      published_at       VARCHAR,
      year               BIGINT,
      citation_count     BIGINT,
      domain             VARCHAR,
      subdomain          VARCHAR,
      embedding_norm     DOUBLE PRECISION,
      ivf_cluster_id     BIGINT,
      source             VARCHAR NOT NULL DEFAULT 'arxiv',
      status             VARCHAR NOT NULL DEFAULT 'raw',
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    BIGINT  DEFAULT 1,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      owner_did          VARCHAR,
      _seq               BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_scientific_paper_domain
      ON vertex_scientific_paper (domain, year)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_scientific_paper_status
      ON vertex_scientific_paper (status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_scientific_paper_ivf
      ON vertex_scientific_paper (ivf_cluster_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_scientific_paper_doi
      ON vertex_scientific_paper (doi)
  `.execute(db);

  // ── C1: edge — taxon → kami 3D model ─────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_taxon_model (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR NOT NULL,
      dst_vid          VARCHAR NOT NULL,
      model_role       VARCHAR NOT NULL DEFAULT 'primary',
      confidence       DOUBLE PRECISION DEFAULT 1.0,
      created_at       VARCHAR NOT NULL,
      sensitivity_ord  BIGINT  DEFAULT 1,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      owner_did        VARCHAR,
      _seq             BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_taxon_model_src
      ON edge_taxon_model (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_taxon_model_dst
      ON edge_taxon_model (dst_vid)
  `.execute(db);

  // ── C2: edge — model → material ──────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_model_material (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR NOT NULL,
      dst_vid          VARCHAR NOT NULL,
      material_slot    VARCHAR NOT NULL DEFAULT 'body',
      created_at       VARCHAR NOT NULL,
      sensitivity_ord  BIGINT  DEFAULT 1,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      owner_did        VARCHAR,
      _seq             BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_model_material_src
      ON edge_model_material (src_vid)
  `.execute(db);

  // ── C3: edge — material → element ────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_material_element (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR NOT NULL,
      dst_vid            VARCHAR NOT NULL,
      weight_fraction    DOUBLE PRECISION,
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    BIGINT  DEFAULT 1,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      owner_did          VARCHAR,
      _seq               BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_material_element_src
      ON edge_material_element (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_material_element_dst
      ON edge_material_element (dst_vid)
  `.execute(db);

  // ── C4: edge — paper → taxon ──────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_paper_taxon (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR NOT NULL,
      dst_vid         VARCHAR NOT NULL,
      relation_kind   VARCHAR NOT NULL DEFAULT 'describes',
      confidence      DOUBLE PRECISION DEFAULT 0.8,
      created_at      VARCHAR NOT NULL,
      sensitivity_ord BIGINT  DEFAULT 1,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      owner_did       VARCHAR,
      _seq            BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_paper_taxon_src
      ON edge_paper_taxon (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_paper_taxon_dst
      ON edge_paper_taxon (dst_vid)
  `.execute(db);

  // ── C5: edge — paper → element ────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_paper_element (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR NOT NULL,
      dst_vid         VARCHAR NOT NULL,
      relation_kind   VARCHAR NOT NULL DEFAULT 'characterizes',
      created_at      VARCHAR NOT NULL,
      sensitivity_ord BIGINT  DEFAULT 1,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      owner_did       VARCHAR,
      _seq            BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_paper_element_src
      ON edge_paper_element (src_vid)
  `.execute(db);

  // ── D1: MV — per-tile model density (drives JS LOD decisions) ─────────
  // Cardinality: #H3-res10 tiles with instances ≤ ~50K globally → safe for MV.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kami_tile_model_density AS
    SELECT
      tile_h3,
      model_kind,
      COUNT(*) AS instance_count,
      COUNT(DISTINCT model_def_id) AS model_def_count,
      MIN(world_x) AS min_x,
      MAX(world_x) AS max_x,
      MIN(world_z) AS min_z,
      MAX(world_z) AS max_z
    FROM vertex_kami_model_instance mi
    JOIN vertex_kami_model_def md ON md.vertex_id = mi.model_def_id
    GROUP BY tile_h3, model_kind
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_kami_tile_density_h3
      ON mv_kami_tile_model_density (tile_h3)
  `.execute(db);

  // ── D2: MV — taxon model coverage (which taxa have 3D models) ─────────
  // Cardinality: #domain_kind × #taxon_rank ≤ 5 × 20 = 100 → trivially safe.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_taxon_model_coverage AS
    SELECT
      domain_kind,
      taxon_rank,
      COUNT(*)                          AS total_taxa,
      COUNT(kami_model_def_id)          AS modelled_taxa,
      COUNT(kami_canopy_shape)          AS vegetation_taxa,
      CAST(COUNT(kami_model_def_id) AS DOUBLE PRECISION)
        / CAST(COUNT(*) AS DOUBLE PRECISION) AS model_coverage_ratio
    FROM vertex_scientific_taxon
    GROUP BY domain_kind, taxon_rank
  `.execute(db);

  // ── D3: MV — paper domain stats (per domain + year) ───────────────────
  // Cardinality: ~10 domains × ~30 years = 300 rows → safe.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_science_paper_domain_stats AS
    SELECT
      domain,
      year,
      COUNT(*)                                 AS paper_count,
      COUNT(CASE WHEN status = 'embedded' THEN 1 END) AS embedded_count,
      COUNT(CASE WHEN status = 'linked'   THEN 1 END) AS linked_count,
      AVG(citation_count)                      AS avg_citations
    FROM vertex_scientific_paper
    GROUP BY domain, year
  `.execute(db);

  // ── D4: MV — element compound coverage ───────────────────────────────
  // Cardinality: 118 elements × material slots → bounded.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_element_material_coverage AS
    SELECT
      el.symbol,
      el.atomic_number,
      el.category,
      COUNT(eme.src_vid) AS material_count
    FROM vertex_periodic_element el
    LEFT JOIN edge_material_element eme ON eme.dst_vid = el.vertex_id
    GROUP BY el.symbol, el.atomic_number, el.category
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    "mv_element_material_coverage",
    "mv_science_paper_domain_stats",
    "mv_taxon_model_coverage",
    "mv_kami_tile_model_density",
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  for (const tbl of [
    "edge_paper_element",
    "edge_paper_taxon",
    "edge_material_element",
    "edge_model_material",
    "edge_taxon_model",
    "vertex_scientific_paper",
    "vertex_mineral",
    "vertex_scientific_taxon",
    "vertex_periodic_element",
    "vertex_kami_material_def",
    "vertex_kami_model_instance",
    "vertex_kami_model_def",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(tbl)}`.execute(db);
  }
}
