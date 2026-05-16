import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
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
    )
  `.execute(db);

  await sql`
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
    )
  `.execute(db);

  await sql`
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
    )
  `.execute(db);

  await sql`CREATE INDEX idx_vertex_mold_allergen_species ON vertex_mold_allergen (species, allergen)`.execute(db);
  await sql`CREATE INDEX idx_vertex_mold_air_sampling_site_at ON vertex_mold_air_sampling (site, sampled_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_vertex_mold_slit_candidate_species_phase ON vertex_mold_slit_candidate (species, phase, created_at DESC)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_mold_slit_candidate`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mold_air_sampling`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mold_allergen`.execute(db);
}
