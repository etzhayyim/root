DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id IN ('tsukuru_cad_design_flow.v1','tsukuru_pcb_design_flow.v1');
DELETE FROM vertex_langgraph_assistant WHERE assistant_id IN ('tsukuru_cad_design_flow.v1','tsukuru_pcb_design_flow.v1');
DELETE FROM vertex_mcp_tool_def WHERE nsid IN (
  'ai.gftd.apps.tsukuru.cadProject.create',
  'ai.gftd.apps.tsukuru.cadPart.upsert',
  'ai.gftd.apps.tsukuru.meviy.requestQuote',
  'ai.gftd.apps.tsukuru.pcbProject.create',
  'ai.gftd.apps.tsukuru.pban.requestQuote'
);
FLUSH;

DROP TABLE IF EXISTS edge_tsukuru_project_part;
DROP TABLE IF EXISTS vertex_tsukuru_cad_part;
DROP TABLE IF EXISTS vertex_tsukuru_cad_project;
DROP TABLE IF EXISTS vertex_tsukuru_pcb_project;
