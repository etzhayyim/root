-- Rollback Phase E1 shosha_agent_loop partial decomposition.
-- The bulk-51 v1 row remains in the registry; clearing the superseded_by
-- mark restores the v1 path. Removing the v2 rows is best-effort (a later
-- v3 deployment may rely on the same vertex_id PKs).

UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'shosha_agent_loop';

DELETE FROM vertex_langgraph_deployment
 WHERE assistant_id = 'shosha_agent_loop.v2';
DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id = 'shosha_agent_loop.v2';
DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'shosha_agent_loop.v2';

FLUSH;
