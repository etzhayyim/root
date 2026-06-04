-- ADR-2605082000 (amended) — extend vertex_langgraph_assistant for self-evolution lineage.
--
-- Adds 3 columns required by data-only graph evolution:
--   checkpointer_mode  — selects checkpoint backend per ADR-2605082100
--                        ('none' | 'postgres' | 'rw_vertex')
--   authored_by        — DID of the agent/operator that proposed this assistant version
--                        (did:plc:... | did:etzhayyim:agent:... | did:web:...)
--   superseded_by      — assistant_id of the next version that replaced this row,
--                        NULL = current. Immutable history per ADR-0036 hard-delete.
--
-- We do NOT add a separate `lifecycle` column: vertex_langgraph_deployment.status
-- ('active' | 'disabled') already pins which assistant_id+version is live.
-- shadow/canary semantics are expressed by deploying multiple assistant rows and
-- routing in front of the loader, not by a column on the assistant itself.

ALTER TABLE vertex_langgraph_assistant
  ADD COLUMN IF NOT EXISTS checkpointer_mode varchar DEFAULT 'none';

ALTER TABLE vertex_langgraph_assistant
  ADD COLUMN IF NOT EXISTS authored_by varchar;

ALTER TABLE vertex_langgraph_assistant
  ADD COLUMN IF NOT EXISTS superseded_by varchar;

CREATE INDEX IF NOT EXISTS idx_langgraph_assistant_authored_by
  ON vertex_langgraph_assistant (authored_by);

CREATE INDEX IF NOT EXISTS idx_langgraph_assistant_superseded
  ON vertex_langgraph_assistant (superseded_by);
