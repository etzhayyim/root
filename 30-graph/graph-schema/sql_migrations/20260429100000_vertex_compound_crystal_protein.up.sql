CREATE TABLE IF NOT EXISTS vertex_compound (
      vertex_id           VARCHAR PRIMARY KEY,
      pubchem_cid         VARCHAR NOT NULL,
      iupac_name          VARCHAR,
      common_name         VARCHAR,
      molecular_formula   VARCHAR,
      molecular_weight    DOUBLE PRECISION,
      smiles              VARCHAR,
      inchi               VARCHAR,
      inchi_key           VARCHAR,
      charge              INT DEFAULT 0,
      h_bond_donors       INT,
      h_bond_acceptors    INT,
      rotatable_bonds     INT,
      xlogp               DOUBLE PRECISION,
      tpsa                DOUBLE PRECISION,
      complexity          DOUBLE PRECISION,
      phase_std           VARCHAR,
      kami_model_def_id   VARCHAR,
      created_at          VARCHAR NOT NULL,
      sensitivity_ord     INT DEFAULT 0,
      org_id              VARCHAR,
      owner_did           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_compound_pubchem_cid
      ON vertex_compound (pubchem_cid);

CREATE INDEX IF NOT EXISTS idx_compound_inchi_key
      ON vertex_compound (inchi_key);

CREATE INDEX IF NOT EXISTS idx_compound_formula
      ON vertex_compound (molecular_formula);

CREATE TABLE IF NOT EXISTS vertex_crystal_structure (
      vertex_id           VARCHAR PRIMARY KEY,
      source_ref_id       VARCHAR NOT NULL,
      source_kind         VARCHAR NOT NULL,
      crystal_system      VARCHAR,
      space_group         VARCHAR,
      space_group_number  INT,
      a_ang               DOUBLE PRECISION,
      b_ang               DOUBLE PRECISION,
      c_ang               DOUBLE PRECISION,
      alpha_deg           DOUBLE PRECISION,
      beta_deg            DOUBLE PRECISION,
      gamma_deg           DOUBLE PRECISION,
      z_value             INT,
      density_calc        DOUBLE PRECISION,
      unit_cell_cid       VARCHAR,
      glb_cid             VARCHAR,
      cif_cid             VARCHAR,
      cod_id              VARCHAR,
      icsd_id             VARCHAR,
      created_at          VARCHAR NOT NULL,
      sensitivity_ord     INT DEFAULT 0,
      org_id              VARCHAR,
      owner_did           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_crystal_source_ref
      ON vertex_crystal_structure (source_ref_id);

CREATE INDEX IF NOT EXISTS idx_crystal_space_group_num
      ON vertex_crystal_structure (space_group_number);

CREATE TABLE IF NOT EXISTS vertex_protein (
      vertex_id           VARCHAR PRIMARY KEY,
      uniprot_id          VARCHAR NOT NULL,
      entry_name          VARCHAR,
      protein_name        VARCHAR,
      gene_name           VARCHAR,
      organism            VARCHAR,
      taxon_id            VARCHAR,
      sequence_length     INT,
      molecular_weight    DOUBLE PRECISION,
      subcell_location    VARCHAR,
      function_text       VARCHAR,
      pfam_ids_json       VARCHAR,
      go_ids_json         VARCHAR,
      pdb_ids_json        VARCHAR,
      embed_cid           VARCHAR,
      kg_linked           INT DEFAULT 0,
      created_at          VARCHAR NOT NULL,
      sensitivity_ord     INT DEFAULT 0,
      org_id              VARCHAR,
      owner_did           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_protein_uniprot_id
      ON vertex_protein (uniprot_id);

CREATE INDEX IF NOT EXISTS idx_protein_taxon_id
      ON vertex_protein (taxon_id);

CREATE TABLE IF NOT EXISTS edge_compound_element (
      edge_id             VARCHAR PRIMARY KEY,
      compound_did        VARCHAR NOT NULL,
      element_sym         VARCHAR NOT NULL,
      element_did         VARCHAR,
      atom_count          INT,
      mass_pct            DOUBLE PRECISION,
      created_at          VARCHAR NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_edge_compound_element_compound
      ON edge_compound_element (compound_did);

CREATE INDEX IF NOT EXISTS idx_edge_compound_element_sym
      ON edge_compound_element (element_sym);

CREATE TABLE IF NOT EXISTS edge_mineral_crystal (
      edge_id             VARCHAR PRIMARY KEY,
      mineral_did         VARCHAR NOT NULL,
      crystal_did         VARCHAR NOT NULL,
      source              VARCHAR DEFAULT 'cod',
      created_at          VARCHAR NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_edge_mineral_crystal_mineral
      ON edge_mineral_crystal (mineral_did);

CREATE TABLE IF NOT EXISTS edge_compound_crystal (
      edge_id             VARCHAR PRIMARY KEY,
      compound_did        VARCHAR NOT NULL,
      crystal_did         VARCHAR NOT NULL,
      source              VARCHAR DEFAULT 'cod',
      created_at          VARCHAR NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_edge_compound_crystal_compound
      ON edge_compound_crystal (compound_did);

CREATE TABLE IF NOT EXISTS edge_protein_element (
      edge_id             VARCHAR PRIMARY KEY,
      protein_did         VARCHAR NOT NULL,
      element_sym         VARCHAR NOT NULL,
      element_did         VARCHAR,
      role                VARCHAR DEFAULT 'bulk',
      created_at          VARCHAR NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_edge_protein_element_protein
      ON edge_protein_element (protein_did);

CREATE TABLE IF NOT EXISTS edge_paper_compound (
      edge_id             VARCHAR PRIMARY KEY,
      paper_did           VARCHAR NOT NULL,
      compound_did        VARCHAR NOT NULL,
      mention_count       INT DEFAULT 1,
      created_at          VARCHAR NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_edge_paper_compound_paper
      ON edge_paper_compound (paper_did);

CREATE TABLE IF NOT EXISTS edge_paper_protein (
      edge_id             VARCHAR PRIMARY KEY,
      paper_did           VARCHAR NOT NULL,
      protein_did         VARCHAR NOT NULL,
      mention_count       INT DEFAULT 1,
      created_at          VARCHAR NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_edge_paper_protein_paper
      ON edge_paper_protein (paper_did);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_compound_element_coverage AS
    SELECT
      ce.element_sym,
      COUNT(DISTINCT ce.compound_did)  AS compound_count,
      MIN(ce.created_at)               AS first_edge_at
    FROM edge_compound_element ce
    GROUP BY ce.element_sym;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_crystal_coverage AS
    SELECT
      cs.crystal_system,
      COUNT(*)                         AS structure_count,
      MIN(cs.created_at)               AS first_at
    FROM vertex_crystal_structure cs
    GROUP BY cs.crystal_system;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_protein_taxon_coverage AS
    SELECT
      p.taxon_id,
      COUNT(*)                         AS protein_count,
      SUM(p.kg_linked)                 AS linked_count,
      MIN(p.created_at)                AS first_at
    FROM vertex_protein p
    WHERE p.taxon_id IS NOT NULL
    GROUP BY p.taxon_id;
