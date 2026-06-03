DELETE FROM vertex_mcp_tool_def WHERE vertex_id IN (
  'at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-probeEnvironment',
  'at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-transferSignal',
  'at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-formColony',
  'at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-handoffToKi',
  'at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-lyse'
);

FLUSH;
