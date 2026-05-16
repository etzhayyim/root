DROP INDEX IF EXISTS idx_sbom_component_type;

DROP INDEX IF EXISTS idx_sbom_component_supplier_mpn;

DROP INDEX IF EXISTS idx_sbom_component_cpe;

DROP INDEX IF EXISTS idx_sbom_component_purl;

DROP INDEX IF EXISTS idx_sbom_component_artifact_uri;

DROP TABLE IF EXISTS vertex_sbom_component;

DROP INDEX IF EXISTS idx_sbom_artifact_registered;

DROP INDEX IF EXISTS idx_sbom_artifact_kind;

DROP INDEX IF EXISTS idx_sbom_artifact_vehicle_id;

DROP INDEX IF EXISTS idx_sbom_artifact_source_sha;

DROP TABLE IF EXISTS vertex_sbom_artifact;
