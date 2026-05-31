// tier: C
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Bio + physical ontology spine.
 *
 * Adds the missing cross-scale graph backbone for:
 * - life / organisms: gene, protein, cell type, tissue, organ, body system, pathway
 * - matter / materials: element, isotope, molecule, material grade
 *
 * Existing domain-specific tables remain canonical where they already exist
 * (`vertex_seibutsu_taxon`, `vertex_medical`, ATC/ICD/NDC record projections).
 * These tables provide stable vertex/edge targets for normalized joins across
 * those domains instead of overloading generic `vertex_repo_record` payloads.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bio_gene (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      gene_id VARCHAR,
      symbol VARCHAR,
      name VARCHAR,
      organism_taxon_id VARCHAR,
      organism_name VARCHAR,
      chromosome VARCHAR,
      start_pos BIGINT,
      end_pos BIGINT,
      strand VARCHAR,
      gene_type VARCHAR,
      ncbi_gene_id VARCHAR,
      ensembl_gene_id VARCHAR,
      hgnc_id VARCHAR,
      wikidata_qid VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_gene_gene_id ON vertex_bio_gene (gene_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_gene_symbol_taxon ON vertex_bio_gene (symbol, organism_taxon_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_gene_ncbi ON vertex_bio_gene (ncbi_gene_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_gene_ensembl ON vertex_bio_gene (ensembl_gene_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bio_protein (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      protein_id VARCHAR,
      accession VARCHAR,
      name VARCHAR,
      organism_taxon_id VARCHAR,
      gene_id VARCHAR,
      sequence_sha256 VARCHAR,
      length BIGINT,
      protein_type VARCHAR,
      uniprot_id VARCHAR,
      refseq_id VARCHAR,
      pdb_ids_json VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_protein_protein_id ON vertex_bio_protein (protein_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_protein_accession ON vertex_bio_protein (accession)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_protein_gene ON vertex_bio_protein (gene_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_protein_taxon ON vertex_bio_protein (organism_taxon_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bio_cell_type (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      cell_type_id VARCHAR,
      name VARCHAR,
      ontology_id VARCHAR,
      parent_cell_type_id VARCHAR,
      lineage VARCHAR,
      organism_taxon_id VARCHAR,
      marker_genes_json VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_cell_type_id ON vertex_bio_cell_type (cell_type_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_cell_type_ontology ON vertex_bio_cell_type (ontology_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_cell_type_parent ON vertex_bio_cell_type (parent_cell_type_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bio_tissue (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      tissue_id VARCHAR,
      name VARCHAR,
      ontology_id VARCHAR,
      organ_id VARCHAR,
      organism_taxon_id VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_tissue_id ON vertex_bio_tissue (tissue_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_tissue_ontology ON vertex_bio_tissue (ontology_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_tissue_organ ON vertex_bio_tissue (organ_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bio_organ (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      organ_id VARCHAR,
      name VARCHAR,
      ontology_id VARCHAR,
      body_system_id VARCHAR,
      organism_taxon_id VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_organ_id ON vertex_bio_organ (organ_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_organ_ontology ON vertex_bio_organ (ontology_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_organ_system ON vertex_bio_organ (body_system_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bio_body_system (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      body_system_id VARCHAR,
      name VARCHAR,
      ontology_id VARCHAR,
      organism_taxon_id VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_body_system_id ON vertex_bio_body_system (body_system_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_body_system_ontology ON vertex_bio_body_system (ontology_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bio_pathway (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      pathway_id VARCHAR,
      name VARCHAR,
      pathway_type VARCHAR,
      organism_taxon_id VARCHAR,
      source_db VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_pathway_id ON vertex_bio_pathway (pathway_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_pathway_type ON vertex_bio_pathway (pathway_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bio_pathway_taxon ON vertex_bio_pathway (organism_taxon_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_phys_element (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      atomic_number BIGINT,
      symbol VARCHAR,
      name VARCHAR,
      atomic_weight DOUBLE PRECISION,
      period BIGINT,
      group_no BIGINT,
      block VARCHAR,
      element_category VARCHAR,
      standard_state VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_element_atomic_number ON vertex_phys_element (atomic_number)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_element_symbol ON vertex_phys_element (symbol)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_element_category ON vertex_phys_element (element_category)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_phys_isotope (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      isotope_id VARCHAR,
      atomic_number BIGINT,
      element_symbol VARCHAR,
      mass_number BIGINT,
      neutron_count BIGINT,
      half_life VARCHAR,
      decay_modes_json VARCHAR,
      abundance DOUBLE PRECISION,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_isotope_id ON vertex_phys_isotope (isotope_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_isotope_element ON vertex_phys_isotope (atomic_number, element_symbol)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_isotope_mass ON vertex_phys_isotope (mass_number)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_phys_molecule (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      molecule_id VARCHAR,
      name VARCHAR,
      formula VARCHAR,
      canonical_smiles VARCHAR,
      inchikey VARCHAR,
      cas_rn VARCHAR,
      molecular_weight DOUBLE PRECISION,
      molecule_type VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_molecule_id ON vertex_phys_molecule (molecule_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_molecule_inchikey ON vertex_phys_molecule (inchikey)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_molecule_formula ON vertex_phys_molecule (formula)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_molecule_type ON vertex_phys_molecule (molecule_type)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_phys_material (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      material_id VARCHAR,
      name VARCHAR,
      grade VARCHAR,
      material_class VARCHAR,
      standard VARCHAR,
      composition_json VARCHAR,
      properties_json VARCHAR,
      hazard_json VARCHAR,
      source VARCHAR,
      source_url VARCHAR,
      metadata_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_material_id ON vertex_phys_material (material_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_material_grade ON vertex_phys_material (grade)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_material_class ON vertex_phys_material (material_class)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_phys_material_standard ON vertex_phys_material (standard)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_bio_part_of (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      src_kind VARCHAR,
      dst_kind VARCHAR,
      relation_kind VARCHAR NOT NULL,
      evidence_code VARCHAR,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_part_of_src ON edge_bio_part_of (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_part_of_dst ON edge_bio_part_of (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_part_of_kind ON edge_bio_part_of (relation_kind)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_bio_gene_encodes_protein (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      gene_id VARCHAR,
      protein_id VARCHAR,
      transcript_id VARCHAR,
      evidence_code VARCHAR,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_gene_encodes_src ON edge_bio_gene_encodes_protein (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_gene_encodes_dst ON edge_bio_gene_encodes_protein (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_gene_encodes_gene_protein ON edge_bio_gene_encodes_protein (gene_id, protein_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_bio_expressed_in (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      src_kind VARCHAR,
      dst_kind VARCHAR,
      expression_value DOUBLE PRECISION,
      expression_unit VARCHAR,
      condition_label VARCHAR,
      evidence_code VARCHAR,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_expressed_src ON edge_bio_expressed_in (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_expressed_dst ON edge_bio_expressed_in (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_expressed_condition ON edge_bio_expressed_in (condition_label)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_bio_participates_in_pathway (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      src_kind VARCHAR,
      pathway_id VARCHAR,
      role VARCHAR,
      evidence_code VARCHAR,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_pathway_src ON edge_bio_participates_in_pathway (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_pathway_dst ON edge_bio_participates_in_pathway (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_pathway_id ON edge_bio_participates_in_pathway (pathway_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_phys_isotope_of_element (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      isotope_id VARCHAR,
      atomic_number BIGINT,
      element_symbol VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_isotope_src ON edge_phys_isotope_of_element (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_isotope_dst ON edge_phys_isotope_of_element (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_isotope_element ON edge_phys_isotope_of_element (atomic_number, element_symbol)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_phys_molecule_has_component (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      component_kind VARCHAR,
      stoichiometric_count DOUBLE PRECISION,
      role VARCHAR,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_molecule_component_src ON edge_phys_molecule_has_component (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_molecule_component_dst ON edge_phys_molecule_has_component (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_molecule_component_kind ON edge_phys_molecule_has_component (component_kind)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_phys_material_composed_of (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      component_kind VARCHAR,
      fraction_value DOUBLE PRECISION,
      fraction_unit VARCHAR,
      role VARCHAR,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_material_component_src ON edge_phys_material_composed_of (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_material_component_dst ON edge_phys_material_composed_of (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_phys_material_component_kind ON edge_phys_material_composed_of (component_kind)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_bio_entity_composed_of_molecule (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      src_kind VARCHAR,
      molecule_id VARCHAR,
      abundance_value DOUBLE PRECISION,
      abundance_unit VARCHAR,
      evidence_code VARCHAR,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_molecule_src ON edge_bio_entity_composed_of_molecule (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_molecule_dst ON edge_bio_entity_composed_of_molecule (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_bio_molecule_id ON edge_bio_entity_composed_of_molecule (molecule_id)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bio_ontology_counts AS
    SELECT 'gene' AS kind, count(*)::bigint AS vertex_count FROM vertex_bio_gene
    UNION ALL SELECT 'protein', count(*)::bigint FROM vertex_bio_protein
    UNION ALL SELECT 'cell_type', count(*)::bigint FROM vertex_bio_cell_type
    UNION ALL SELECT 'tissue', count(*)::bigint FROM vertex_bio_tissue
    UNION ALL SELECT 'organ', count(*)::bigint FROM vertex_bio_organ
    UNION ALL SELECT 'body_system', count(*)::bigint FROM vertex_bio_body_system
    UNION ALL SELECT 'pathway', count(*)::bigint FROM vertex_bio_pathway
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_phys_ontology_counts AS
    SELECT 'element' AS kind, count(*)::bigint AS vertex_count FROM vertex_phys_element
    UNION ALL SELECT 'isotope', count(*)::bigint FROM vertex_phys_isotope
    UNION ALL SELECT 'molecule', count(*)::bigint FROM vertex_phys_molecule
    UNION ALL SELECT 'material', count(*)::bigint FROM vertex_phys_material
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bio_gene_expression_summary AS
    SELECT
      src_vid,
      dst_vid,
      condition_label,
      count(*)::bigint AS observation_count,
      avg(expression_value) AS avg_expression_value
    FROM edge_bio_expressed_in
    GROUP BY src_vid, dst_vid, condition_label
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_phys_material_composition_summary AS
    SELECT
      src_vid AS material_vid,
      component_kind,
      count(*)::bigint AS component_count,
      sum(COALESCE(fraction_value, 0.0)) AS known_fraction_sum
    FROM edge_phys_material_composed_of
    GROUP BY src_vid, component_kind
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE domain IN (
      'gene_catalog',
      'protein_catalog',
      'cell_type_catalog',
      'anatomy_tissue',
      'anatomy_organ',
      'anatomy_body_system',
      'pathway_catalog',
      'element_catalog',
      'isotope_catalog',
      'molecule_catalog',
      'sozai'
    )
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('gene_catalog', 'bio', 'app.etzhayyim.apps.bio.gene', 100000000, 'gene records across major reference organisms', 'science'),
      ('protein_catalog', 'bio', 'app.etzhayyim.apps.bio.protein', 250000000, 'protein records across public sequence databases', 'science'),
      ('cell_type_catalog', 'bio', 'app.etzhayyim.apps.bio.cellType', 5000, 'curated cell types', 'science'),
      ('anatomy_tissue', 'bio', 'app.etzhayyim.apps.bio.tissue', 50000, 'anatomical tissue entities', 'science'),
      ('anatomy_organ', 'bio', 'app.etzhayyim.apps.bio.organ', 10000, 'anatomical organ entities', 'science'),
      ('anatomy_body_system', 'bio', 'app.etzhayyim.apps.bio.bodySystem', 20, 'body systems', 'science'),
      ('pathway_catalog', 'bio', 'app.etzhayyim.apps.bio.pathway', 30000, 'biological pathways', 'science'),
      ('element_catalog', 'phys', 'app.etzhayyim.apps.phys.element', 118, 'chemical elements', 'science'),
      ('isotope_catalog', 'phys', 'app.etzhayyim.apps.phys.isotope', 3400, 'known isotopes', 'science'),
      ('molecule_catalog', 'phys', 'app.etzhayyim.apps.phys.molecule', 200000000, 'registered molecules and compounds', 'science'),
      ('sozai', 'phys', 'app.etzhayyim.apps.phys.material', 200000, 'material grades', 'manufacturing')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE domain IN (
      'gene_catalog',
      'protein_catalog',
      'cell_type_catalog',
      'anatomy_tissue',
      'anatomy_organ',
      'anatomy_body_system',
      'pathway_catalog',
      'element_catalog',
      'isotope_catalog',
      'molecule_catalog',
      'sozai'
    )
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_phys_material_composition_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_bio_gene_expression_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_phys_ontology_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_bio_ontology_counts`.execute(db);

  await sql`DROP TABLE IF EXISTS edge_bio_entity_composed_of_molecule`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_phys_material_composed_of`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_phys_molecule_has_component`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_phys_isotope_of_element`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_bio_participates_in_pathway`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_bio_expressed_in`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_bio_gene_encodes_protein`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_bio_part_of`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_phys_material`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_phys_molecule`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_phys_isotope`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_phys_element`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bio_pathway`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bio_body_system`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bio_organ`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bio_tissue`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bio_cell_type`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bio_protein`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bio_gene`.execute(db);
}
