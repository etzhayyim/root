import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (training run / checkpoint / eval lineage. hyperparams +
//          weight metadata + eval scores; no Tier-3 PII. Weight bytes
//          are stored in B2 — RW holds reference + sha256 only.)

/**
 * RisingWave-native model training + weight lineage schema.
 *
 * ADR-2605070700 — adds run / checkpoint / eval lineage on top of the
 * already-live corpus export path (`v_training_text` / `v_training_triple`
 * → B2 shard → HF Hub `etzhayyim/etzhayyim-corpus`, ADR Phase D 2026-05-01).
 *
 * Weight artifact 2-store layout (mirrors ADR-2604300135 Hume distillation):
 *   - B2: `etzhayyim-training-data/v1/checkpoints/{run_id}/step-{NNNNNN}.safetensors`
 *   - RW: `vertex_training_checkpoint.weight_b2_uri` + `weight_sha256` only
 *
 * Tables (4 vertex + 3 edge + 2 streaming MV):
 *   vertex_training_dataset_snapshot   immutable corpus shard set
 *   vertex_training_run                one fine-tune / distill run
 *   vertex_training_checkpoint         weight reference per step
 *   vertex_training_eval               bench result per checkpoint
 *   edge_training_consumed_dataset     run → dataset_snapshot
 *   edge_training_distilled_from       student_run → teacher (run | actor DID)
 *   edge_training_promoted_to          checkpoint → serving alias
 *   mv_training_run_status             queued/running/done/failed by kind
 *   mv_training_active_serving         current alias → checkpoint
 *
 * Naming: `vertex_id` content-addressed per ADR-0041:
 *   run         = at://did:web:training.etzhayyim.com/com.etzhayyim.training.run/{run_id}
 *   checkpoint  = at://did:web:training.etzhayyim.com/com.etzhayyim.training.checkpoint/{run_id}-step-{NNNNNN}
 *   eval        = at://did:web:training.etzhayyim.com/com.etzhayyim.training.eval/{checkpoint_id}-{bench_name}
 *   dataset     = at://did:web:training.etzhayyim.com/com.etzhayyim.training.datasetSnapshot/{dataset_name}-{content_hash[:12]}
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Vertex: dataset snapshot ──────────────────────────────────────
  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Vertex: training run ──────────────────────────────────────────
  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Vertex: training checkpoint ───────────────────────────────────
  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Vertex: training eval ─────────────────────────────────────────
  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Edge: run consumed dataset ────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_training_consumed_dataset (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      role varchar NOT NULL,
      mix_ratio double precision,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Edge: distilled from (student → teacher) ──────────────────────
  // dst_vid = teacher run vertex_id OR teacher actor DID
  // teacher_kind ∈ {'run', 'actor', 'artifact'}
  await sql`
    CREATE TABLE IF NOT EXISTS edge_training_distilled_from (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      teacher_kind varchar NOT NULL,
      distill_method varchar,
      temperature double precision,
      sample_count bigint,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Edge: promoted to serving ─────────────────────────────────────
  // src_vid = checkpoint vertex_id, dst_vid = serving alias string
  // status = 'active' | 'retired'. App-layer enforces 1 active edge per alias.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_training_promoted_to (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      alias varchar NOT NULL,
      serving_target varchar,
      promoted_at varchar NOT NULL,
      retired_at varchar,
      promoted_by varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Streaming MV: run status by kind ──────────────────────────────
  // Cardinality bounded by kind (4) × status (4) = 16 groups. Safe.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_training_run_status AS
      SELECT
        kind,
        status,
        COUNT(*) AS run_count,
        MAX(started_at) AS last_started_at,
        MAX(ended_at) AS last_ended_at
      FROM vertex_training_run
      GROUP BY kind, status
  `.execute(db);

  // ── Streaming MV: active serving alias → checkpoint ───────────────
  // Cardinality bounded by alias count (~tens). Safe.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_training_active_serving AS
      SELECT
        alias,
        src_vid AS checkpoint_vertex_id,
        serving_target,
        promoted_at,
        promoted_by
      FROM edge_training_promoted_to
      WHERE status = 'active'
  `.execute(db);

  // ── Grants ────────────────────────────────────────────────────────
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_training_dataset_snapshot TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_training_dataset_snapshot TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_training_run TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_training_run TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_training_checkpoint TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_training_checkpoint TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_training_eval TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_training_eval TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_training_consumed_dataset TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_training_consumed_dataset TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_training_distilled_from TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_training_distilled_from TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_training_promoted_to TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_training_promoted_to TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`REVOKE ALL ON edge_training_promoted_to FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON edge_training_promoted_to FROM root`.execute(db);
  await sql`REVOKE ALL ON edge_training_distilled_from FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON edge_training_distilled_from FROM root`.execute(db);
  await sql`REVOKE ALL ON edge_training_consumed_dataset FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON edge_training_consumed_dataset FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_training_eval FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_training_eval FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_training_checkpoint FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_training_checkpoint FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_training_run FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_training_run FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_training_dataset_snapshot FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_training_dataset_snapshot FROM root`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_training_active_serving`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_training_run_status`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_training_promoted_to`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_training_distilled_from`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_training_consumed_dataset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_training_eval`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_training_checkpoint`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_training_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_training_dataset_snapshot`.execute(db);
}
