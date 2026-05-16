-- P16-b of ADR-2605141200 — rollback the 7 compose_character_vrm tool rows.

DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'ai.gftd.apps.mangaka.tools.loadCharacterProfile',
  'ai.gftd.apps.mangaka.tools.generateMultiviewAnime',
  'ai.gftd.apps.mangaka.tools.reconstructMesh',
  'ai.gftd.apps.mangaka.tools.extractFacialBlendshapes',
  'ai.gftd.apps.mangaka.tools.autoRigHumanoid',
  'ai.gftd.apps.mangaka.tools.bindVrm',
  'ai.gftd.apps.mangaka.tools.validateVrm'
);

FLUSH;
