DROP INDEX IF EXISTS idx_langgraph_assistant_superseded;
DROP INDEX IF EXISTS idx_langgraph_assistant_authored_by;

ALTER TABLE vertex_langgraph_assistant DROP COLUMN IF EXISTS superseded_by;
ALTER TABLE vertex_langgraph_assistant DROP COLUMN IF EXISTS authored_by;
ALTER TABLE vertex_langgraph_assistant DROP COLUMN IF EXISTS checkpointer_mode;
