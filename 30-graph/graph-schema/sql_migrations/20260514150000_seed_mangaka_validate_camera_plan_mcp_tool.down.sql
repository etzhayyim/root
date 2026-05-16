-- P10.2 of ADR-2605141200 — rollback the validateCameraPlan registration.

DELETE FROM vertex_mcp_tool_def
WHERE nsid = 'ai.gftd.apps.mangaka.tools.validateCameraPlan';

FLUSH;
