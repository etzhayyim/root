CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_design (
      vertex_id VARCHAR PRIMARY KEY,
      chip_id VARCHAR NOT NULL,
      chip_name VARCHAR NOT NULL,
      isa VARCHAR NOT NULL,
      process_node_nm INTEGER,
      die_area_mm2 DOUBLE PRECISION,
      transistor_count_b DOUBLE PRECISION,
      open_source_rtl BOOLEAN NOT NULL DEFAULT false,
      rtl_license VARCHAR,
      fab_did VARCHAR,
      tape_out_date VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-soc'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_fab_order (
      vertex_id VARCHAR PRIMARY KEY,
      order_id VARCHAR NOT NULL,
      chip_did VARCHAR NOT NULL,
      fab_did VARCHAR NOT NULL,
      process_node_nm INTEGER,
      wafer_qty INTEGER,
      delivery_estimate VARCHAR,
      price_usd_k DOUBLE PRECISION,
      order_status VARCHAR NOT NULL DEFAULT 'placed',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-soc'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_export_flag (
      vertex_id VARCHAR PRIMARY KEY,
      chip_did VARCHAR NOT NULL,
      flag_type VARCHAR NOT NULL,
      entity_list_entry VARCHAR,
      jurisdiction VARCHAR NOT NULL,
      flagged_at VARCHAR NOT NULL,
      severity VARCHAR NOT NULL,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-soc'
    );

FLUSH;
