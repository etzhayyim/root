-- P8 of ADR-2605141200 — rollback the 6 mangaka tool registrations.

DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'ai.gftd.apps.mangaka.tools.loadPanelPlan',
  'ai.gftd.apps.mangaka.tools.resolveAssets',
  'ai.gftd.apps.mangaka.tools.placeScene',
  'ai.gftd.apps.mangaka.tools.simulateCharacter',
  'ai.gftd.apps.mangaka.tools.renderKeyframes',
  'ai.gftd.apps.mangaka.tools.persistScene3d'
);

FLUSH;
