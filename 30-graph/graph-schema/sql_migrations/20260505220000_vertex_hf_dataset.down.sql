REVOKE ALL ON vertex_hf_dataset_record FROM kaisya_app;

REVOKE ALL ON vertex_hf_dataset_record FROM root;

REVOKE ALL ON vertex_hf_dataset FROM kaisya_app;

REVOKE ALL ON vertex_hf_dataset FROM root;

DROP MATERIALIZED VIEW IF EXISTS mv_hf_dataset_text_for_training;

DROP TABLE IF EXISTS vertex_hf_dataset_record;

DROP TABLE IF EXISTS vertex_hf_dataset;
