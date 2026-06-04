-- Down: revert ADR-2605082000 Phase E3 etzhayyimcojp_company_ops decomposition.

UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'etzhayyimcojp-company-ops';

DELETE FROM vertex_langgraph_deployment WHERE assistant_id = 'etzhayyimcojp-company-ops.v2';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'etzhayyimcojp-company-ops.v2';

DELETE FROM vertex_langgraph_assistant WHERE assistant_id = 'etzhayyimcojp-company-ops.v2';

FLUSH;
