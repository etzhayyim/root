-- Rollback for 20260514150000_seed_mangaka_compose_scene_3d_refinement_dmn.up.sql.

DELETE FROM vertex_dmn_model
WHERE decision_key = 'ai.gftd.policies.mangaka.composeScene3dRefinement'
  AND version = 1;
