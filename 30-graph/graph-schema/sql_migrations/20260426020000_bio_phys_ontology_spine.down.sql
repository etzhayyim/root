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
    );

DROP MATERIALIZED VIEW IF EXISTS mv_phys_material_composition_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_bio_gene_expression_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_phys_ontology_counts;

DROP MATERIALIZED VIEW IF EXISTS mv_bio_ontology_counts;

DROP TABLE IF EXISTS edge_bio_entity_composed_of_molecule;

DROP TABLE IF EXISTS edge_phys_material_composed_of;

DROP TABLE IF EXISTS edge_phys_molecule_has_component;

DROP TABLE IF EXISTS edge_phys_isotope_of_element;

DROP TABLE IF EXISTS edge_bio_participates_in_pathway;

DROP TABLE IF EXISTS edge_bio_expressed_in;

DROP TABLE IF EXISTS edge_bio_gene_encodes_protein;

DROP TABLE IF EXISTS edge_bio_part_of;

DROP TABLE IF EXISTS vertex_phys_material;

DROP TABLE IF EXISTS vertex_phys_molecule;

DROP TABLE IF EXISTS vertex_phys_isotope;

DROP TABLE IF EXISTS vertex_phys_element;

DROP TABLE IF EXISTS vertex_bio_pathway;

DROP TABLE IF EXISTS vertex_bio_body_system;

DROP TABLE IF EXISTS vertex_bio_organ;

DROP TABLE IF EXISTS vertex_bio_tissue;

DROP TABLE IF EXISTS vertex_bio_cell_type;

DROP TABLE IF EXISTS vertex_bio_protein;

DROP TABLE IF EXISTS vertex_bio_gene;
