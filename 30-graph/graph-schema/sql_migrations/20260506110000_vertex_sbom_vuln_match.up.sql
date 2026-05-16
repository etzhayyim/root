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
    );

CREATE INDEX idx_cve_entry_purl_pattern ON vertex_cve_entry(affected_purl_pattern);

CREATE INDEX idx_cve_entry_cpe_pattern  ON vertex_cve_entry(affected_cpe_pattern);

CREATE INDEX idx_cve_entry_severity     ON vertex_cve_entry(severity);

CREATE INDEX idx_cve_entry_source       ON vertex_cve_entry(source);

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
    );

CREATE INDEX idx_vuln_match_artifact_uri ON vertex_sbom_vuln_match(artifact_uri);

CREATE INDEX idx_vuln_match_cve_id       ON vertex_sbom_vuln_match(cve_id);

CREATE INDEX idx_vuln_match_severity     ON vertex_sbom_vuln_match(severity);

CREATE INDEX idx_vuln_match_purl         ON vertex_sbom_vuln_match(component_purl);
