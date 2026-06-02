DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id IN ('tsukuru_cad_design_flow.v1','tsukuru_pcb_design_flow.v1');
DELETE FROM vertex_langgraph_assistant WHERE assistant_id IN ('tsukuru_cad_design_flow.v1','tsukuru_pcb_design_flow.v1');
DELETE FROM vertex_mcp_tool_def WHERE nsid IN (
  'com.etzhayyim.apps.tsukuru.cadProject.create',
  'com.etzhayyim.apps.tsukuru.cadPart.upsert',
  'com.etzhayyim.apps.tsukuru.meviy.requestQuote',
  'com.etzhayyim.apps.tsukuru.pcbProject.create',
  'com.etzhayyim.apps.tsukuru.pban.requestQuote'
);
FLUSH;

DROP TABLE IF EXISTS edge_tsukuru_project_part;
DROP TABLE IF EXISTS vertex_tsukuru_cad_part;
DROP TABLE IF EXISTS vertex_tsukuru_cad_project;
DROP TABLE IF EXISTS vertex_tsukuru_pcb_project;
