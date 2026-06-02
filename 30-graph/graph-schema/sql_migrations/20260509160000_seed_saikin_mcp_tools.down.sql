DELETE FROM vertex_mcp_tool_def WHERE vertex_id IN (
  'at://did:web:saikin.gftd.ai/com.etzhayyim.mcp.toolDef/ai-gftd-apps-saikin-probeEnvironment',
  'at://did:web:saikin.gftd.ai/com.etzhayyim.mcp.toolDef/ai-gftd-apps-saikin-transferSignal',
  'at://did:web:saikin.gftd.ai/com.etzhayyim.mcp.toolDef/ai-gftd-apps-saikin-formColony',
  'at://did:web:saikin.gftd.ai/com.etzhayyim.mcp.toolDef/ai-gftd-apps-saikin-handoffToKi',
  'at://did:web:saikin.gftd.ai/com.etzhayyim.mcp.toolDef/ai-gftd-apps-saikin-lyse'
);

FLUSH;
