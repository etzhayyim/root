-- P10.2b of ADR-2605141200 — rollback the aggregateCritique registration.

DELETE FROM vertex_mcp_tool_def
WHERE nsid = 'com.etzhayyim.apps.mangaka.tools.aggregateCritique';

FLUSH;
