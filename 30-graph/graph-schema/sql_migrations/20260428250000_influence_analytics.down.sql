DROP MATERIALIZED VIEW IF EXISTS mv_influence_centrality;

DROP TABLE IF EXISTS vertex_influence_score;

DROP INDEX IF EXISTS idx_bprel_type;

DROP INDEX IF EXISTS idx_bprel_dst;

DROP INDEX IF EXISTS idx_bprel_src;

DROP INDEX IF EXISTS idx_bpedu_person;

DROP INDEX IF EXISTS idx_bpcert_person;

DROP INDEX IF EXISTS idx_bpskill_person;

DROP INDEX IF EXISTS idx_bpcareer_person;

ALTER TABLE edge_business_person_relation DROP COLUMN IF EXISTS verification_status;

ALTER TABLE edge_business_person_relation DROP COLUMN IF EXISTS confidence;
