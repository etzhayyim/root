import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * sbom.etzhayyim.com — Phase C: vuln-match schema.
 *
 *   vertex_cve_entry        — CVE feed (NVD / OSV / GHSA / Renault FAR / etc.)
 *   vertex_sbom_vuln_match  — one row per (component, cve) pair detected
 *
 * `vertex_cve_entry` is owned by sbom but populated by upstream feeders
 * (`yabai.etzhayyim.com` ingest-cve, OSV API, GitHub GHSA mirror). This
 * migration only creates the empty table — separate ingestion BPMNs
 * fill it.
 *
 * `vertex_sbom_vuln_match` is the projection consumed by the SBOM
 * blast-radius queries (Phase D). The match is detected at register
 * time by `task_sbom_run_vuln_match` joining the just-persisted
 * components to `vertex_cve_entry` by purl / cpe pattern.
 *
 * Indexes:
 *   idx_cve_entry_purl_pattern    — purl LIKE join
 *   idx_cve_entry_cpe_pattern     — cpe LIKE join
 *   idx_cve_entry_severity        — severity-bucketed dashboards
 *   idx_vuln_match_artifact_uri   — list matches for an artifact
 *   idx_vuln_match_cve_id         — blast-radius (this CVE → all artifacts)
 *   idx_vuln_match_severity       — high-severity-first triage
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_cve_entry (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      cve_id varchar NOT NULL,
      severity varchar,
      cvss_score double precision,
      summary varchar,
      published_at varchar,
      modified_at varchar,
      affected_purl_pattern varchar,
      affected_cpe_pattern varchar,
      source varchar,
      source_url varchar,
      created_at varchar NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar
    )
  `.execute(db);
  await sql`CREATE INDEX idx_cve_entry_purl_pattern ON vertex_cve_entry(affected_purl_pattern)`.execute(db);
  await sql`CREATE INDEX idx_cve_entry_cpe_pattern  ON vertex_cve_entry(affected_cpe_pattern)`.execute(db);
  await sql`CREATE INDEX idx_cve_entry_severity     ON vertex_cve_entry(severity)`.execute(db);
  await sql`CREATE INDEX idx_cve_entry_source       ON vertex_cve_entry(source)`.execute(db);

  await sql`
    CREATE TABLE vertex_sbom_vuln_match (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      artifact_uri varchar NOT NULL,
      component_bom_ref varchar NOT NULL,
      component_purl varchar,
      component_cpe varchar,
      cve_id varchar NOT NULL,
      severity varchar,
      cvss_score double precision,
      matched_via varchar NOT NULL,
      matched_at varchar NOT NULL,
      created_at varchar NOT NULL,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar
    )
  `.execute(db);
  await sql`CREATE INDEX idx_vuln_match_artifact_uri ON vertex_sbom_vuln_match(artifact_uri)`.execute(db);
  await sql`CREATE INDEX idx_vuln_match_cve_id       ON vertex_sbom_vuln_match(cve_id)`.execute(db);
  await sql`CREATE INDEX idx_vuln_match_severity     ON vertex_sbom_vuln_match(severity)`.execute(db);
  await sql`CREATE INDEX idx_vuln_match_purl         ON vertex_sbom_vuln_match(component_purl)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vuln_match_purl`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vuln_match_severity`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vuln_match_cve_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vuln_match_artifact_uri`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sbom_vuln_match`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_cve_entry_source`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_cve_entry_severity`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_cve_entry_cpe_pattern`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_cve_entry_purl_pattern`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cve_entry`.execute(db);
}
