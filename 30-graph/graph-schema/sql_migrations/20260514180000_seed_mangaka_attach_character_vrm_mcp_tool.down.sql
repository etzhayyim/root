-- P13 of ADR-2605141200 — rollback the attachCharacterVrm registration.

DELETE FROM vertex_mcp_tool_def
WHERE nsid = 'ai.gftd.apps.mangaka.tools.attachCharacterVrm';

FLUSH;
