-- ADR-2605080600 — checkpoint dedup + compression columns.
-- Shannon source coding (zlib) + content-addressed storage (sha256 cid).
-- Backwards compatible: existing rows have content_cid=NULL, compression='none'.

ALTER TABLE vertex_langgraph_checkpoint
  ADD COLUMN IF NOT EXISTS content_cid varchar;

ALTER TABLE vertex_langgraph_checkpoint
  ADD COLUMN IF NOT EXISTS compression varchar DEFAULT 'none';

ALTER TABLE vertex_langgraph_checkpoint
  ADD COLUMN IF NOT EXISTS blob_size_bytes bigint DEFAULT 0;

ALTER TABLE vertex_langgraph_checkpoint
  ADD COLUMN IF NOT EXISTS blob_stored_bytes bigint DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_langgraph_checkpoint_content_cid
  ON vertex_langgraph_checkpoint (content_cid);

CREATE INDEX IF NOT EXISTS idx_langgraph_checkpoint_thread_cid
  ON vertex_langgraph_checkpoint (thread_id, content_cid);

-- mv: per-thread dedup ratio (low cardinality, one row per active thread).
-- Safe: GROUP BY thread_id only — checkpoint count per thread is bounded
-- by graph step count (<< 10K typical), thread count is small.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_langgraph_checkpoint_dedup AS
  SELECT
    thread_id,
    COUNT(*)                                          AS checkpoint_count,
    COUNT(DISTINCT content_cid)                       AS unique_content_count,
    SUM(blob_size_bytes)                              AS total_logical_bytes,
    SUM(blob_stored_bytes)                            AS total_stored_bytes
  FROM vertex_langgraph_checkpoint
  WHERE content_cid IS NOT NULL
  GROUP BY thread_id;

-- mv: compression-method coverage (low cardinality: 2-3 distinct values).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_langgraph_checkpoint_compression AS
  SELECT
    compression,
    COUNT(*)               AS row_count,
    SUM(blob_size_bytes)   AS logical_bytes,
    SUM(blob_stored_bytes) AS stored_bytes
  FROM vertex_langgraph_checkpoint
  GROUP BY compression;
