-- ADR-2605082100: per-assistant checkpointer mode.
-- Modes: 'none' (default) | 'rw_vertex' | 'postgres'
-- Loader's COALESCE(checkpointer_mode, 'none') handles pre-migration NULLs.

ALTER TABLE vertex_langgraph_assistant
  ADD COLUMN IF NOT EXISTS checkpointer_mode varchar DEFAULT 'none';
