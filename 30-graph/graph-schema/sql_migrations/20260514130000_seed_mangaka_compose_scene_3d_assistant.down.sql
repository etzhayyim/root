-- ADR-2605141200 — rollback Phase A registration.

DELETE FROM vertex_langgraph_deployment
WHERE nsid = 'com.etzhayyim.apps.mangaka.composeScene3d';

DELETE FROM vertex_langgraph_assistant
WHERE assistant_id = 'com.etzhayyim.apps.mangaka.composeScene3d'
  AND version = 1;
