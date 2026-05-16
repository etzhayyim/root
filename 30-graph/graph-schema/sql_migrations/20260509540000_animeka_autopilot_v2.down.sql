-- Rollback Phase E3 animeka_autopilot decomposition.

UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'animeka_autopilot';

DELETE FROM vertex_langgraph_deployment
 WHERE assistant_id = 'animeka_autopilot.v2';
DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id = 'animeka_autopilot.v2';
DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'animeka_autopilot.v2';

FLUSH;
