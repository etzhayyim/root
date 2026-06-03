DROP INDEX IF EXISTS idx_vertex_claim_challenge_root_hash;

DROP INDEX IF EXISTS idx_vertex_claim_stake_root_hash;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_root_hash;

DROP INDEX IF EXISTS idx_edge_erc725_facade_root_hash;

DROP INDEX IF EXISTS idx_edge_erc725_facade_hash;

DROP INDEX IF EXISTS idx_vertex_erc725_root_identity_addr;

DROP INDEX IF EXISTS idx_vertex_erc725_root_identity_hash;

ALTER TABLE vertex_claim_challenge DROP COLUMN legacy_challenger_did;

ALTER TABLE vertex_claim_challenge DROP COLUMN root_identity_addr;

ALTER TABLE vertex_claim_challenge DROP COLUMN root_did_hash;

ALTER TABLE vertex_claim_challenge DROP COLUMN root_did;

ALTER TABLE vertex_claim_stake DROP COLUMN legacy_claimant_did;

ALTER TABLE vertex_claim_stake DROP COLUMN root_identity_addr;

ALTER TABLE vertex_claim_stake DROP COLUMN root_did_hash;

ALTER TABLE vertex_claim_stake DROP COLUMN root_did;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN migration_status;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN identity_method;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN facade_did_hash;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN facade_did;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN root_identity_addr;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN root_did_hash;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN root_did;

DROP TABLE IF EXISTS edge_erc725_facade_did;

DROP TABLE IF EXISTS vertex_erc725_root_identity;
