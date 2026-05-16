DROP INDEX IF EXISTS idx_medical_source_targets_collection;

DROP INDEX IF EXISTS idx_medical_ingest_run_source_started;

DROP INDEX IF EXISTS idx_medical_ingest_cursor_source;

DROP INDEX IF EXISTS idx_medical_source_asset_source_offset;

DROP INDEX IF EXISTS idx_medical_data_source_source_id;

DROP TABLE IF EXISTS edge_medical_source_targets_collection;

DROP TABLE IF EXISTS vertex_medical_ingest_run;

DROP TABLE IF EXISTS vertex_medical_ingest_cursor;

DROP TABLE IF EXISTS vertex_medical_source_asset;

DROP TABLE IF EXISTS vertex_medical_data_source;
