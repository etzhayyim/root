CREATE TABLE IF NOT EXISTS vertex_wire_transfer (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      from_did VARCHAR,
      to_did VARCHAR,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_wire_transfer_from_did ON vertex_wire_transfer (from_did);

CREATE INDEX IF NOT EXISTS idx_wire_transfer_to_did ON vertex_wire_transfer (to_did);

CREATE INDEX IF NOT EXISTS idx_wire_transfer_status ON vertex_wire_transfer (status);

CREATE TABLE IF NOT EXISTS vertex_wire_message (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      from_did VARCHAR,
      to_did VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_wire_message_from_did ON vertex_wire_message (from_did);

CREATE INDEX IF NOT EXISTS idx_wire_message_to_did ON vertex_wire_message (to_did);
