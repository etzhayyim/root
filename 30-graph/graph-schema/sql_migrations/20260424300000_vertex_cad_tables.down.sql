DROP INDEX IF EXISTS idx_edge_cad_derives_from_src;

FLUSH;

DROP TABLE IF EXISTS edge_cad_derives_from;

FLUSH;

DROP INDEX IF EXISTS idx_edge_cad_commented_on_dst;

FLUSH;

DROP INDEX IF EXISTS idx_edge_cad_commented_on_src;

FLUSH;

DROP TABLE IF EXISTS edge_cad_commented_on;

FLUSH;

DROP INDEX IF EXISTS idx_edge_cad_has_feature_src;

FLUSH;

DROP TABLE IF EXISTS edge_cad_has_feature;

FLUSH;

DROP INDEX IF EXISTS idx_edge_cad_has_revision_src;

FLUSH;

DROP TABLE IF EXISTS edge_cad_has_revision;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_export_job_status;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_export_job_revision;

FLUSH;

DROP TABLE IF EXISTS vertex_cad_export_job;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_comment_part;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_comment_revision;

FLUSH;

DROP TABLE IF EXISTS vertex_cad_comment;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_feature_type;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_feature_revision;

FLUSH;

DROP TABLE IF EXISTS vertex_cad_feature;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_revision_status;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_revision_model;

FLUSH;

DROP TABLE IF EXISTS vertex_cad_revision;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_cad_model_workspace;

FLUSH;

DROP TABLE IF EXISTS vertex_cad_model;

FLUSH;
