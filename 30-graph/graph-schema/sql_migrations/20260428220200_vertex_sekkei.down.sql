DROP MATERIALIZED VIEW IF EXISTS mv_sekkei_stale_reviews;

DROP INDEX IF EXISTS idx_sekkei_release_product;

DROP INDEX IF EXISTS idx_sekkei_release_drawing;

DROP TABLE IF EXISTS vertex_sekkei_release;

DROP INDEX IF EXISTS idx_sekkei_bom_child;

DROP INDEX IF EXISTS idx_sekkei_bom_parent;

DROP TABLE IF EXISTS vertex_sekkei_bom_line;

DROP INDEX IF EXISTS idx_sekkei_approval_decision;

DROP INDEX IF EXISTS idx_sekkei_approval_drawing;

DROP TABLE IF EXISTS vertex_sekkei_approval;

DROP INDEX IF EXISTS idx_sekkei_revision_status;

DROP INDEX IF EXISTS idx_sekkei_revision_drawing;

DROP TABLE IF EXISTS vertex_sekkei_revision;

DROP INDEX IF EXISTS idx_sekkei_drawing_linked;

DROP INDEX IF EXISTS idx_sekkei_drawing_project;

DROP INDEX IF EXISTS idx_sekkei_drawing_status;

DROP INDEX IF EXISTS idx_sekkei_drawing_owner;

DROP TABLE IF EXISTS vertex_sekkei_drawing;

FLUSH;
