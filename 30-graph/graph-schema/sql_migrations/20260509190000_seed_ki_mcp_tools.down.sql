DELETE FROM vertex_mcp_tool_def WHERE vertex_id IN (
  'at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-ki-absorb',
  'at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-ki-synthesize',
  'at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-ki-bloom',
  'at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-ki-ring'
);

FLUSH;
