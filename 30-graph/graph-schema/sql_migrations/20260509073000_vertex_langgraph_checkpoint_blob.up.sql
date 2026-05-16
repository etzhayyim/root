-- Real content-addressed dedup for LangGraph checkpoints.
-- Pointer rows in vertex_langgraph_checkpoint reference blob rows by content_cid.
-- RW PK = implicit upsert: re-INSERT same content_cid is idempotent.

CREATE TABLE IF NOT EXISTS vertex_langgraph_checkpoint_blob (
  vertex_id varchar PRIMARY KEY,        -- = content_cid (sha256 hex)
  blob varchar NOT NULL,
  compression varchar NOT NULL DEFAULT 'none',
  blob_size_bytes bigint NOT NULL DEFAULT 0,
  blob_stored_bytes bigint NOT NULL DEFAULT 0,
  first_seen_at varchar NOT NULL,
  created_at varchar NOT NULL,
  sensitivity_ord int DEFAULT 0,
  owner_did varchar
);

-- mv: dedup savings (low cardinality: bounded by distinct content_cid count).
-- Joins pointer count from checkpoint table with single-row blob storage.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_langgraph_checkpoint_blob_savings AS
  SELECT
    'all'                                                  AS scope,
    COUNT(*)                                               AS unique_blobs,
    SUM(blob_size_bytes)                                   AS unique_logical_bytes,
    SUM(blob_stored_bytes)                                 AS unique_stored_bytes
  FROM vertex_langgraph_checkpoint_blob;
