DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'ai.gftd.apps.openIsicA.classifyCrop',
  'ai.gftd.apps.openIsicA.classifyLivestock',
  'ai.gftd.apps.openIsicA.classifyForestry',
  'ai.gftd.apps.openIsicA.classifyFishing'
);

FLUSH;
