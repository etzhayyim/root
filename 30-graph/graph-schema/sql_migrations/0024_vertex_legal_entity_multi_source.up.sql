ALTER TABLE vertex_legal_entity ADD COLUMN IF NOT EXISTS source VARCHAR;

ALTER TABLE vertex_legal_entity ADD COLUMN IF NOT EXISTS source_record_id VARCHAR;

ALTER TABLE vertex_legal_entity ADD COLUMN IF NOT EXISTS wikidata_qid VARCHAR;

ALTER TABLE vertex_legal_entity ADD COLUMN IF NOT EXISTS opencorporates_id VARCHAR;
