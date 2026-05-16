CREATE TABLE vertex_mold_allergen (
      vertex_id              VARCHAR PRIMARY KEY,
      _seq                   BIGINT NOT NULL,
      owner_did              VARCHAR NOT NULL,
      species                VARCHAR NOT NULL,
      allergen               VARCHAR NOT NULL,
      uniprot                VARCHAR,
      mw_kda                 DOUBLE PRECISION,
      biochemical_function   VARCHAR,
      source                 VARCHAR NOT NULL,
      created_at             TIMESTAMPTZ NOT NULL,
      actor_id               VARCHAR
    );

CREATE TABLE vertex_mold_air_sampling (
      vertex_id                  VARCHAR PRIMARY KEY,
      _seq                       BIGINT NOT NULL,
      owner_did                  VARCHAR NOT NULL,
      session_id                 VARCHAR NOT NULL,
      site                       VARCHAR NOT NULL,
      sampled_at                 TIMESTAMPTZ NOT NULL,
      method                     VARCHAR NOT NULL,
      alternaria_count_per_m3    DOUBLE PRECISION NOT NULL,
      cladosporium_count_per_m3  DOUBLE PRECISION NOT NULL,
      aspergillus_count_per_m3   DOUBLE PRECISION NOT NULL,
      penicillium_count_per_m3   DOUBLE PRECISION NOT NULL,
      temperature_c              DOUBLE PRECISION NOT NULL,
      relative_humidity          DOUBLE PRECISION NOT NULL,
      created_at                 TIMESTAMPTZ NOT NULL,
      actor_id                   VARCHAR
    );

CREATE TABLE vertex_mold_slit_candidate (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT NOT NULL,
      owner_did             VARCHAR NOT NULL,
      candidate_id          VARCHAR NOT NULL,
      species               VARCHAR NOT NULL,
      allergen_source       VARCHAR NOT NULL,
      major_allergen        VARCHAR,
      dosage_form           VARCHAR NOT NULL,
      buildup_weeks         INTEGER NOT NULL,
      maintenance_dose_jau  DOUBLE PRECISION NOT NULL,
      excipients_json       VARCHAR NOT NULL,
      target_indication     VARCHAR NOT NULL,
      design_lineage        VARCHAR NOT NULL,
      phase                 VARCHAR NOT NULL,
      created_at            TIMESTAMPTZ NOT NULL,
      actor_id              VARCHAR
    );

CREATE INDEX idx_vertex_mold_allergen_species ON vertex_mold_allergen (species, allergen);

CREATE INDEX idx_vertex_mold_air_sampling_site_at ON vertex_mold_air_sampling (site, sampled_at DESC);

CREATE INDEX idx_vertex_mold_slit_candidate_species_phase ON vertex_mold_slit_candidate (species, phase, created_at DESC);
