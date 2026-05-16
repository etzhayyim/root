ALTER TABLE vertex_contracts_socialcontract
      RENAME TO vertex_contracts_social_contract;

CREATE INDEX IF NOT EXISTS idx_contracts_social_contract_jurisdiction
      ON vertex_contracts_social_contract (jurisdiction);

CREATE INDEX IF NOT EXISTS idx_contracts_social_contract_source_record_id
      ON vertex_contracts_social_contract (source_record_id);
