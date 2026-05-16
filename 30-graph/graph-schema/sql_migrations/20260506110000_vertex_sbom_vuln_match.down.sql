DROP INDEX IF EXISTS idx_vuln_match_purl;

DROP INDEX IF EXISTS idx_vuln_match_severity;

DROP INDEX IF EXISTS idx_vuln_match_cve_id;

DROP INDEX IF EXISTS idx_vuln_match_artifact_uri;

DROP TABLE IF EXISTS vertex_sbom_vuln_match;

DROP INDEX IF EXISTS idx_cve_entry_source;

DROP INDEX IF EXISTS idx_cve_entry_severity;

DROP INDEX IF EXISTS idx_cve_entry_cpe_pattern;

DROP INDEX IF EXISTS idx_cve_entry_purl_pattern;

DROP TABLE IF EXISTS vertex_cve_entry;
