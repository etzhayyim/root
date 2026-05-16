UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'saikin.cycle.v1';

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id = 'saikin.cycle.v2';

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'saikin.cycle.v2';

FLUSH;
