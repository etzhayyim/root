DROP MATERIALIZED VIEW IF EXISTS mv_langgraph_checkpoint_compression;
DROP MATERIALIZED VIEW IF EXISTS mv_langgraph_checkpoint_dedup;
DROP INDEX IF EXISTS idx_langgraph_checkpoint_thread_cid;
DROP INDEX IF EXISTS idx_langgraph_checkpoint_content_cid;
ALTER TABLE vertex_langgraph_checkpoint DROP COLUMN IF EXISTS blob_stored_bytes;
ALTER TABLE vertex_langgraph_checkpoint DROP COLUMN IF EXISTS blob_size_bytes;
ALTER TABLE vertex_langgraph_checkpoint DROP COLUMN IF EXISTS compression;
ALTER TABLE vertex_langgraph_checkpoint DROP COLUMN IF EXISTS content_cid;
