-- Reverse of 20260510000000_vertex_kafun_langgraph.up.sql.

DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id IN (
  'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/kafun-research-langgraph-v1',
  'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/kafun-think-langgraph-v1',
  'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/kafun-tick-langgraph-v1'
);
DELETE FROM vertex_langgraph_deployment WHERE vertex_id IN (
  'langgraph.kafun.research.v1', 'langgraph.kafun.think.v1', 'langgraph.kafun.tick.v1'
);
DELETE FROM vertex_langgraph_assistant WHERE vertex_id IN (
  'kafun.research.v1', 'kafun.think.v1', 'kafun.tick.v1'
);

DROP TABLE IF EXISTS vertex_kafun_action;
DROP TABLE IF EXISTS vertex_kafun_proposal;
DROP TABLE IF EXISTS vertex_kafun_insight;
DROP TABLE IF EXISTS vertex_kafun_research;
