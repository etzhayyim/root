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
    );

CREATE INDEX idx_sbom_artifact_source_sha ON vertex_sbom_artifact(source_sha256);

CREATE INDEX idx_sbom_artifact_vehicle_id ON vertex_sbom_artifact(vehicle_id);

CREATE INDEX idx_sbom_artifact_kind       ON vertex_sbom_artifact(kind);

CREATE INDEX idx_sbom_artifact_registered ON vertex_sbom_artifact(registered_at);

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
    );

CREATE INDEX idx_sbom_component_artifact_uri ON vertex_sbom_component(artifact_uri);

CREATE INDEX idx_sbom_component_purl         ON vertex_sbom_component(purl);

CREATE INDEX idx_sbom_component_cpe          ON vertex_sbom_component(cpe);

CREATE INDEX idx_sbom_component_supplier_mpn ON vertex_sbom_component(supplier_mpn);

CREATE INDEX idx_sbom_component_type         ON vertex_sbom_component(component_type);
