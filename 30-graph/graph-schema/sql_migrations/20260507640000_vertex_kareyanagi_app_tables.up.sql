CREATE TABLE IF NOT EXISTS vertex_kareyanagi_listing (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      seller_did VARCHAR,
      product_name VARCHAR,
      price DOUBLE PRECISION,
      currency VARCHAR,
      quantity BIGINT,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_kareyanagi_listing_seller ON vertex_kareyanagi_listing (seller_did);

CREATE INDEX IF NOT EXISTS idx_kareyanagi_listing_status ON vertex_kareyanagi_listing (status);

CREATE TABLE IF NOT EXISTS vertex_kareyanagi_order (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      buyer_did VARCHAR,
      listing_id VARCHAR,
      quantity BIGINT,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_kareyanagi_order_buyer ON vertex_kareyanagi_order (buyer_did);

CREATE INDEX IF NOT EXISTS idx_kareyanagi_order_listing ON vertex_kareyanagi_order (listing_id);

CREATE INDEX IF NOT EXISTS idx_kareyanagi_order_status ON vertex_kareyanagi_order (status);
