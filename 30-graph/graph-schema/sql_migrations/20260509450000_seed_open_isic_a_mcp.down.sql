DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'com.etzhayyim.apps.openIsicA.classifyCrop',
  'com.etzhayyim.apps.openIsicA.classifyLivestock',
  'com.etzhayyim.apps.openIsicA.classifyForestry',
  'com.etzhayyim.apps.openIsicA.classifyFishing'
);

FLUSH;
