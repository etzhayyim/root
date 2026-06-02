-- P8 of ADR-2605141200 — rollback the 6 mangaka tool registrations.

DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'com.etzhayyim.apps.mangaka.tools.loadPanelPlan',
  'com.etzhayyim.apps.mangaka.tools.resolveAssets',
  'com.etzhayyim.apps.mangaka.tools.placeScene',
  'com.etzhayyim.apps.mangaka.tools.simulateCharacter',
  'com.etzhayyim.apps.mangaka.tools.renderKeyframes',
  'com.etzhayyim.apps.mangaka.tools.persistScene3d'
);

FLUSH;
