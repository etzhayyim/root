-- Down: revert lawfirm-marketing-ops Phase E3 decomposition.

UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'lawfirm-marketing-ops';

DELETE FROM vertex_langgraph_deployment
 WHERE assistant_id = 'lawfirm-marketing-ops.v2';

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id = 'lawfirm-marketing-ops.v2';

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'lawfirm-marketing-ops.v2';

FLUSH;
