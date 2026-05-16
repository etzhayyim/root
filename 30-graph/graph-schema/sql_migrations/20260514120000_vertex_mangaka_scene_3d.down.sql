-- ADR-2605141200 — rollback.

DROP INDEX IF EXISTS idx_mangaka_scene_3d_parent;
DROP INDEX IF EXISTS idx_mangaka_scene_3d_status;
DROP INDEX IF EXISTS idx_mangaka_scene_3d_work;
DROP INDEX IF EXISTS idx_mangaka_scene_3d_panel;
DROP TABLE IF EXISTS vertex_mangaka_scene_3d;
