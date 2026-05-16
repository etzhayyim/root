CREATE TABLE IF NOT EXISTS vertex_po_purchase_order (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      supplier_id VARCHAR,
      total_amount DOUBLE PRECISION,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_po_purchase_order_supplier_id ON vertex_po_purchase_order (supplier_id);

CREATE INDEX IF NOT EXISTS idx_po_purchase_order_status ON vertex_po_purchase_order (status);

CREATE INDEX IF NOT EXISTS idx_po_purchase_order_actor_did ON vertex_po_purchase_order (actor_did);

CREATE TABLE IF NOT EXISTS vertex_po_supplier (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      contact_email VARCHAR,
      address VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_po_supplier_status ON vertex_po_supplier (status);

CREATE INDEX IF NOT EXISTS idx_po_supplier_actor_did ON vertex_po_supplier (actor_did);
