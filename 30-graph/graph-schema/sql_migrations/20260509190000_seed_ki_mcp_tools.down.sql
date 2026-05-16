DELETE FROM vertex_mcp_tool_def WHERE vertex_id IN (
  'at://did:web:ki.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-ki-absorb',
  'at://did:web:ki.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-ki-synthesize',
  'at://did:web:ki.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-ki-bloom',
  'at://did:web:ki.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-ki-ring'
);

FLUSH;
