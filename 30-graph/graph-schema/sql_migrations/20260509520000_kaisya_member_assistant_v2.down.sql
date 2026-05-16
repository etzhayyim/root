-- Rollback Phase E3 kaisya-member-assistant decomposition.

UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'kaisya-member-assistant';

DELETE FROM vertex_langgraph_deployment
 WHERE assistant_id = 'kaisya-member-assistant.v2';
DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id = 'kaisya-member-assistant.v2';
DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'kaisya-member-assistant.v2';

FLUSH;
