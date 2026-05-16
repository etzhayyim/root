-- P10.2b of ADR-2605141200 — rollback the aggregateCritique registration.

DELETE FROM vertex_mcp_tool_def
WHERE nsid = 'ai.gftd.apps.mangaka.tools.aggregateCritique';

FLUSH;
