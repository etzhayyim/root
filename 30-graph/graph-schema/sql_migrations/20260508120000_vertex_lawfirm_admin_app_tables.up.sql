CREATE TABLE IF NOT EXISTS vertex_lawfirm_admin_case (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      client_id VARCHAR,
      case_type VARCHAR,
      status VARCHAR,
      description VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_lawfirm_admin_case_status ON vertex_lawfirm_admin_case (status);

CREATE INDEX IF NOT EXISTS idx_lawfirm_admin_case_client_id ON vertex_lawfirm_admin_case (client_id);

CREATE TABLE IF NOT EXISTS vertex_lawfirm_admin_client (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      email VARCHAR,
      phone VARCHAR,
      org_name VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_lawfirm_admin_client_status ON vertex_lawfirm_admin_client (status);

CREATE INDEX IF NOT EXISTS idx_lawfirm_admin_client_email ON vertex_lawfirm_admin_client (email);
