CREATE TABLE IF NOT EXISTS vertex_lo_shipment (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      origin VARCHAR,
      destination VARCHAR,
      cargo_type VARCHAR,
      weight_kg DOUBLE PRECISION,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_lo_shipment_status ON vertex_lo_shipment (status);

CREATE INDEX IF NOT EXISTS idx_lo_shipment_origin ON vertex_lo_shipment (origin);

CREATE TABLE IF NOT EXISTS vertex_lo_route (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      origin VARCHAR,
      destination VARCHAR,
      distance_km DOUBLE PRECISION,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_lo_route_status ON vertex_lo_route (status);

CREATE INDEX IF NOT EXISTS idx_lo_route_origin ON vertex_lo_route (origin);
