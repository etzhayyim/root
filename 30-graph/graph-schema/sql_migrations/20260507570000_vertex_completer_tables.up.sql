CREATE TABLE IF NOT EXISTS vertex_completer_audit (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      actor_did VARCHAR,
      actor_name VARCHAR,
      score BIGINT,
      effect VARCHAR,
      total_findings BIGINT,
      critical_findings BIGINT,
      high_findings BIGINT,
      evaluated_jurisdictions VARCHAR,
      rule_bundle_ids VARCHAR,
      summary VARCHAR,
      evaluated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_completer_audit_actor_did ON vertex_completer_audit (actor_did);

CREATE INDEX IF NOT EXISTS idx_completer_audit_evaluated_at ON vertex_completer_audit (evaluated_at);

CREATE INDEX IF NOT EXISTS idx_completer_audit_effect ON vertex_completer_audit (effect);

CREATE TABLE IF NOT EXISTS vertex_completer_finding (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      audit_id VARCHAR,
      actor_did VARCHAR,
      rule_id VARCHAR,
      rule_title VARCHAR,
      jurisdiction VARCHAR,
      risk_level VARCHAR,
      obligation_kind VARCHAR,
      summary VARCHAR,
      remediation_hint VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_completer_finding_audit_id ON vertex_completer_finding (audit_id);

CREATE INDEX IF NOT EXISTS idx_completer_finding_actor_did ON vertex_completer_finding (actor_did);

CREATE INDEX IF NOT EXISTS idx_completer_finding_risk_level ON vertex_completer_finding (risk_level);

CREATE TABLE IF NOT EXISTS vertex_completer_remediation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      finding_id VARCHAR,
      action_plan VARCHAR,
      priority VARCHAR,
      estimated_effort VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_completer_remediation_finding_id ON vertex_completer_remediation (finding_id);
