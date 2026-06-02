-- P16-b of ADR-2605141200 — rollback the 7 compose_character_vrm tool rows.

DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'com.etzhayyim.apps.mangaka.tools.loadCharacterProfile',
  'com.etzhayyim.apps.mangaka.tools.generateMultiviewAnime',
  'com.etzhayyim.apps.mangaka.tools.reconstructMesh',
  'com.etzhayyim.apps.mangaka.tools.extractFacialBlendshapes',
  'com.etzhayyim.apps.mangaka.tools.autoRigHumanoid',
  'com.etzhayyim.apps.mangaka.tools.bindVrm',
  'com.etzhayyim.apps.mangaka.tools.validateVrm'
);

FLUSH;
