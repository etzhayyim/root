CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom (
      vertex_id VARCHAR PRIMARY KEY,
      bom_id VARCHAR NOT NULL,
      design_name VARCHAR NOT NULL,
      version VARCHAR NOT NULL,
      soc_did VARCHAR,
      modem_did VARCHAR,
      os_did VARCHAR,
      ems_facility_did VARCHAR,
      target_price_usd DOUBLE PRECISION,
      open_score_pct DOUBLE PRECISION,
      key_closed_risks VARCHAR,
      recommendations VARCHAR,
      scored_at VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'draft',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-bom'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom_line (
      vertex_id VARCHAR PRIMARY KEY,
      line_id VARCHAR NOT NULL,
      bom_did VARCHAR NOT NULL,
      component_type VARCHAR NOT NULL,
      vendor_name VARCHAR NOT NULL,
      part_number VARCHAR NOT NULL,
      unit_cost_usd DOUBLE PRECISION,
      open_source BOOLEAN NOT NULL DEFAULT false,
      license VARCHAR,
      patent_did VARCHAR,
      alternative_count INTEGER NOT NULL DEFAULT 0,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-bom'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom_sourcer (
      vertex_id VARCHAR PRIMARY KEY,
      bom_line_did VARCHAR NOT NULL,
      alt_vendor VARCHAR NOT NULL,
      alt_part_number VARCHAR,
      alt_unit_cost_usd DOUBLE PRECISION,
      open_source BOOLEAN NOT NULL DEFAULT false,
      availability VARCHAR,
      lead_time_weeks INTEGER,
      notes VARCHAR,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-bom'
    );

FLUSH;
