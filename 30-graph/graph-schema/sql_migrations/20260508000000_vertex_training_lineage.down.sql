REVOKE ALL ON edge_training_promoted_to FROM kaisya_app;

REVOKE ALL ON edge_training_promoted_to FROM root;

REVOKE ALL ON edge_training_distilled_from FROM kaisya_app;

REVOKE ALL ON edge_training_distilled_from FROM root;

REVOKE ALL ON edge_training_consumed_dataset FROM kaisya_app;

REVOKE ALL ON edge_training_consumed_dataset FROM root;

REVOKE ALL ON vertex_training_eval FROM kaisya_app;

REVOKE ALL ON vertex_training_eval FROM root;

REVOKE ALL ON vertex_training_checkpoint FROM kaisya_app;

REVOKE ALL ON vertex_training_checkpoint FROM root;

REVOKE ALL ON vertex_training_run FROM kaisya_app;

REVOKE ALL ON vertex_training_run FROM root;

REVOKE ALL ON vertex_training_dataset_snapshot FROM kaisya_app;

REVOKE ALL ON vertex_training_dataset_snapshot FROM root;

DROP MATERIALIZED VIEW IF EXISTS mv_training_active_serving;

DROP MATERIALIZED VIEW IF EXISTS mv_training_run_status;

DROP TABLE IF EXISTS edge_training_promoted_to;

DROP TABLE IF EXISTS edge_training_distilled_from;

DROP TABLE IF EXISTS edge_training_consumed_dataset;

DROP TABLE IF EXISTS vertex_training_eval;

DROP TABLE IF EXISTS vertex_training_checkpoint;

DROP TABLE IF EXISTS vertex_training_run;

DROP TABLE IF EXISTS vertex_training_dataset_snapshot;
