CREATE TABLE IF NOT EXISTS vertex_open_smartphone_ems_facility (
      vertex_id VARCHAR PRIMARY KEY,
      facility_id VARCHAR NOT NULL,
      operator_name VARCHAR NOT NULL,
      operator_lei VARCHAR,
      location_iso3 VARCHAR NOT NULL,
      city VARCHAR,
      facility_type VARCHAR NOT NULL,
      monthly_capacity_units INTEGER,
      certifications VARCHAR,
      rba_audit_status VARCHAR,
      conflict_mineral_compliant BOOLEAN NOT NULL DEFAULT false,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-ems'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_ems_order (
      vertex_id VARCHAR PRIMARY KEY,
      order_id VARCHAR NOT NULL,
      facility_did VARCHAR NOT NULL,
      bom_did VARCHAR,
      quantity_units INTEGER NOT NULL,
      target_unit_cost_usd DOUBLE PRECISION,
      delivery_quarter VARCHAR,
      quality_standard VARCHAR,
      order_status VARCHAR NOT NULL DEFAULT 'planned',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-ems'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_ems_compliance (
      vertex_id VARCHAR PRIMARY KEY,
      facility_did VARCHAR NOT NULL,
      issue_type VARCHAR NOT NULL,
      severity VARCHAR,
      description VARCHAR,
      detected_at VARCHAR,
      resolved_at VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'open',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-ems'
    );

FLUSH;
