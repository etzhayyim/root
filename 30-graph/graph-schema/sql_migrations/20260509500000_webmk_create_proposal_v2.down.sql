-- Rollback Phase E2 webmk_create_proposal decomposition.

UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'webmk_create_proposal';

DELETE FROM vertex_langgraph_deployment
 WHERE assistant_id = 'webmk_create_proposal.v2';
DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id = 'webmk_create_proposal.v2';
DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'webmk_create_proposal.v2';

FLUSH;
