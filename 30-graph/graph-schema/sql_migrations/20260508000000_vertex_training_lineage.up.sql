CREATE TABLE IF NOT EXISTS vertex_training_dataset_snapshot (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      snapshot_id varchar NOT NULL,
      dataset_name varchar NOT NULL,
      label varchar,
      b2_prefix varchar NOT NULL,
      shard_count bigint,
      row_count bigint,
      byte_size bigint,
      content_hash varchar,
      hf_repo_id varchar,
      hf_revision varchar,
      source_view varchar,
      filter_expr varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_training_run (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      run_id varchar NOT NULL,
      kind varchar NOT NULL,
      base_model varchar NOT NULL,
      base_model_revision varchar,
      dataset_snapshot_id varchar,
      teacher_run_id varchar,
      teacher_actor_did varchar,
      hyperparams_json varchar,
      gpu_target varchar,
      gpu_count int,
      seed bigint,
      total_steps bigint,
      completed_steps bigint,
      status varchar NOT NULL,
      started_at varchar,
      ended_at varchar,
      failure_reason varchar,
      triggered_by varchar,
      bpmn_process_instance_key varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_training_checkpoint (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      checkpoint_id varchar NOT NULL,
      run_id varchar NOT NULL,
      step bigint NOT NULL,
      epoch double precision,
      train_loss double precision,
      eval_loss double precision,
      learning_rate double precision,
      weight_b2_uri varchar NOT NULL,
      weight_byte_size bigint,
      weight_sha256 varchar,
      adapter_kind varchar,
      adapter_rank int,
      is_final boolean,
      tokenizer_b2_uri varchar,
      training_args_b2_uri varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_training_eval (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      eval_id varchar NOT NULL,
      checkpoint_id varchar NOT NULL,
      run_id varchar NOT NULL,
      bench_name varchar NOT NULL,
      eval_dataset_snapshot_id varchar,
      metrics_json varchar,
      primary_metric varchar,
      primary_score double precision,
      sample_count bigint,
      duration_seconds double precision,
      eval_runner varchar,
      status varchar NOT NULL,
      evaluated_at varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_training_consumed_dataset (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      role varchar NOT NULL,
      mix_ratio double precision,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_training_distilled_from (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      teacher_kind varchar NOT NULL,
      distill_method varchar,
      temperature double precision,
      sample_count bigint,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_training_promoted_to (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      alias varchar NOT NULL,
      serving_target varchar,
      promoted_at varchar NOT NULL,
      retired_at varchar,
      promoted_by varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_training_run_status AS
      SELECT
        kind,
        status,
        COUNT(*) AS run_count,
        MAX(started_at) AS last_started_at,
        MAX(ended_at) AS last_ended_at
      FROM vertex_training_run
      GROUP BY kind, status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_training_active_serving AS
      SELECT
        alias,
        src_vid AS checkpoint_vertex_id,
        serving_target,
        promoted_at,
        promoted_by
      FROM edge_training_promoted_to
      WHERE status = 'active';

GRANT SELECT, INSERT, UPDATE ON vertex_training_dataset_snapshot TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_training_dataset_snapshot TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_training_run TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_training_run TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_training_checkpoint TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_training_checkpoint TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_training_eval TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_training_eval TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON edge_training_consumed_dataset TO root;

GRANT SELECT, INSERT, UPDATE ON edge_training_consumed_dataset TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON edge_training_distilled_from TO root;

GRANT SELECT, INSERT, UPDATE ON edge_training_distilled_from TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON edge_training_promoted_to TO root;

GRANT SELECT, INSERT, UPDATE ON edge_training_promoted_to TO kaisya_app;
