CREATE TABLE IF NOT EXISTS vertex_oil_country_profile (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      did VARCHAR,
      repo VARCHAR,
      country_code VARCHAR,
      role_flags VARCHAR,
      reserve_rank BIGINT,
      production_rank BIGINT,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_oil_company (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      did VARCHAR,
      repo VARCHAR,
      name VARCHAR,
      company_type VARCHAR,
      hq_country VARCHAR,
      sanctions_status VARCHAR,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_oil_basin (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      basin_code VARCHAR,
      basin_name VARCHAR,
      country_code VARCHAR,
      basin_type VARCHAR,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_oil_field (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      field_code VARCHAR,
      basin_code VARCHAR,
      field_type VARCHAR,
      operator_did VARCHAR,
      country_code VARCHAR,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_oil_pipeline (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      pipeline_code VARCHAR,
      commodity VARCHAR,
      operator_did VARCHAR,
      capacity_bpd BIGINT,
      length_km DOUBLE PRECISION,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_oil_terminal (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      terminal_code VARCHAR,
      terminal_type VARCHAR,
      locode VARCHAR,
      operator_did VARCHAR,
      storage_capacity BIGINT,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_refinery (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      refinery_code VARCHAR,
      operator_did VARCHAR,
      throughput_bpd BIGINT,
      complexity_index DOUBLE PRECISION,
      country_code VARCHAR,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_oil_cargo (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      cargo_id VARCHAR,
      commodity VARCHAR,
      grade_code VARCHAR,
      quantity BIGINT,
      load_port VARCHAR,
      discharge_port VARCHAR,
      laycan VARCHAR,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_crude_grade (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      grade_code VARCHAR,
      api_gravity DOUBLE PRECISION,
      sulfur_pct DOUBLE PRECISION,
      benchmark_link VARCHAR,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_product_grade (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      product_code VARCHAR,
      product_family VARCHAR,
      sulfur_band VARCHAR,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_pricing_benchmark (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      benchmark_code VARCHAR,
      region VARCHAR,
      commodity VARCHAR,
      publisher VARCHAR,
      status VARCHAR,
      collection VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_oil_coverage_snapshot (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      actor_did VARCHAR,
      actor_name VARCHAR,
      nanoid VARCHAR,
      bucket VARCHAR,
      node_count BIGINT,
      latest_seq BIGINT,
      summary VARCHAR,
      repo VARCHAR,
      collection VARCHAR,
      status VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_operates (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      label VARCHAR,
      role VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_feeds (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      label VARCHAR,
      commodity VARCHAR,
      capacity BIGINT,
      unit VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_flows_to (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      label VARCHAR,
      commodity VARCHAR,
      volume BIGINT,
      unit VARCHAR,
      time_bucket VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_loaded_at (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      label VARCHAR,
      loaded_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_discharged_at (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      label VARCHAR,
      discharged_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_priced_against (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      label VARCHAR,
      basis VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_constrained_by (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      label VARCHAR,
      severity VARCHAR,
      status VARCHAR
    );
