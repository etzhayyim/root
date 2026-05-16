DELETE FROM vertex_langgraph_deployment
 WHERE assistant_id = 'gameya_quality_loop';

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'gameya_quality_loop';

FLUSH;
