import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * sbom.etzhayyim.com — Phase B persistence schema.
 *
 * Two append-only vertex tables for the SBOM artifact registry. Both
 * `cargo-cyclonedx` (software) and `kami-cad-import` (vehicle hardware,
 * CycloneDX `type: "device"`) flow through the same handler and land
 * here unchanged.
 *
 *   vertex_sbom_artifact   — one row per registered SBOM upload
 *   vertex_sbom_component  — one row per CycloneDX `components[]` entry
 *
 * Phase C (forward work) adds vertex_sbom_vuln_match by joining
 * components to yabai's CveEntry graph; that lands in a separate
 * migration so this one stays focused on the persistence skeleton.
 *
 * Indexes:
 *   idx_sbom_artifact_source_sha    — dedup by source content hash
 *   idx_sbom_artifact_vehicle_id    — vehicle-scoped recall queries
 *   idx_sbom_component_artifact_uri — list components for an artifact
 *   idx_sbom_component_purl         — CVE match join key (purl)
 *   idx_sbom_component_supplier_mpn — Takata-style supplier recall
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_sbom_artifact (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      artifact_uri varchar NOT NULL,
      format varchar NOT NULL,
      spec_version varchar NOT NULL,
      source_uri varchar NOT NULL,
      source_sha256 varchar NOT NULL,
      license varchar NOT NULL,
      kind varchar NOT NULL,
      component_count int NOT NULL,
      vehicle_id varchar,
      vehicle_revision varchar,
      total_mass_kg double precision,
      declared_part_count int,
      tool_vendor varchar,
      tool_name varchar,
      tool_version varchar,
      registered_at varchar NOT NULL,
      created_at varchar NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_sbom_artifact_source_sha ON vertex_sbom_artifact(source_sha256)`.execute(db);
  await sql`CREATE INDEX idx_sbom_artifact_vehicle_id ON vertex_sbom_artifact(vehicle_id)`.execute(db);
  await sql`CREATE INDEX idx_sbom_artifact_kind       ON vertex_sbom_artifact(kind)`.execute(db);
  await sql`CREATE INDEX idx_sbom_artifact_registered ON vertex_sbom_artifact(registered_at)`.execute(db);

  await sql`
    CREATE TABLE vertex_sbom_component (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      artifact_uri varchar NOT NULL,
      bom_ref varchar NOT NULL,
      component_type varchar NOT NULL,
      name varchar,
      version varchar,
      purl varchar,
      cpe varchar,
      license varchar,
      supplier_name varchar,
      supplier_mpn varchar,
      parent_bom_ref varchar,
      properties_json varchar,
      created_at varchar NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar
    )
  `.execute(db);

  await sql`CREATE INDEX idx_sbom_component_artifact_uri ON vertex_sbom_component(artifact_uri)`.execute(db);
  await sql`CREATE INDEX idx_sbom_component_purl         ON vertex_sbom_component(purl)`.execute(db);
  await sql`CREATE INDEX idx_sbom_component_cpe          ON vertex_sbom_component(cpe)`.execute(db);
  await sql`CREATE INDEX idx_sbom_component_supplier_mpn ON vertex_sbom_component(supplier_mpn)`.execute(db);
  await sql`CREATE INDEX idx_sbom_component_type         ON vertex_sbom_component(component_type)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_sbom_component_type`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sbom_component_supplier_mpn`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sbom_component_cpe`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sbom_component_purl`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sbom_component_artifact_uri`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sbom_component`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_sbom_artifact_registered`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sbom_artifact_kind`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sbom_artifact_vehicle_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_sbom_artifact_source_sha`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sbom_artifact`.execute(db);
}
