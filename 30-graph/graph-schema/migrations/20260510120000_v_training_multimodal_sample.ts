import { Kysely, sql } from "kysely";

// Baien-MX (ADR 2605101000) multimodal training sample VIEW.
//
// Joins existing RisingWave-native modalities into per-row training
// samples that can drive Baien-MX's per-modality 1.58-bit projector
// branches in a single mixed mini-batch:
//
//   text             := v_training_text.content       (always present)
//   triple           := v_training_triple             (optional; LEFT JOIN by src_vid)
//   vec768           := vertex_vector_embedding_768   (optional; LEFT JOIN by source_vertex_id)
//   vec4096_fp8_uri  := vertex_vector_embedding_4096_fp8 (optional; bytes are stored externally)
//   threed_blob_id   := vertex_3d_blob.vertex_id      (optional)
//
// Every row keeps text non-NULL. Optional columns are NULL when the
// modality is absent for the row's source vertex — the training step
// activates only the projector branches whose column is non-NULL.
//
// Plain VIEW (not MV) for the same reason as v_training_text:
// avoid memory pressure on large UNION ALL scans. The training
// snapshot helper materializes the visible set into B2 / dataset
// snapshot rows the way Oka already does.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE VIEW v_training_multimodal_sample AS
      SELECT
        t.vertex_id                           AS sample_id,
        t.label                               AS text_label,
        t.content                             AS text,
        t.lang                                AS lang,
        tr.relation                           AS triple_relation,
        tr.dst_vid                            AS triple_object,
        v768.embedding_id                     AS vec768_id,
        v768.modality                         AS vec768_modality,
        v768.emb                              AS vec768_emb,
        v4096.embedding_id                    AS vec4096_id,
        v4096.modality                        AS vec4096_modality,
        v4096.uri                             AS vec4096_uri,
        b.vertex_id                           AS threed_blob_id,
        b.modality                            AS threed_modality,
        t.created_date                        AS created_date,
        0                                     AS sensitivity_ord
      FROM v_training_text                       t
      LEFT JOIN v_training_triple                tr     ON tr.src_vid          = t.vertex_id
      LEFT JOIN vertex_vector_embedding_768      v768   ON v768.source_vertex_id = t.vertex_id
      LEFT JOIN vertex_vector_embedding_4096_fp8 v4096  ON v4096.source_vertex_id = t.vertex_id
      LEFT JOIN vertex_3d_blob                   b      ON b.source_vertex_id  = t.vertex_id
  `.execute(db);

  // Snapshot helper table — mirrors vertex_training_shard pattern.
  // One row per snapshot of v_training_multimodal_sample, used by
  // task_train_baien_mx_run to pin the dataset_snapshot_id that
  // vertex_training_run.dataset_snapshot_id points at.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_training_multimodal_snapshot (
      vertex_id        VARCHAR PRIMARY KEY,
      snapshot_id      VARCHAR NOT NULL,
      dataset_label    VARCHAR NOT NULL,
      row_count        BIGINT,
      modality_mask    VARCHAR NOT NULL,
      b2_key           VARCHAR,
      status           VARCHAR DEFAULT 'pending',
      created_date     VARCHAR NOT NULL,
      sensitivity_ord  INT     DEFAULT 0,
      org_id           VARCHAR DEFAULT 'sys',
      user_id          VARCHAR DEFAULT 'sys',
      actor_id         VARCHAR DEFAULT 'sys.training.snapshot',
      created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS v_training_multimodal_sample`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_training_multimodal_snapshot`.execute(db);
}
