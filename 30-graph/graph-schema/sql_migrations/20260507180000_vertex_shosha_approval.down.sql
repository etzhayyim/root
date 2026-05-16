REVOKE ALL ON vertex_shosha_approval FROM kaisya_app;

REVOKE ALL ON vertex_shosha_approval FROM root;

DROP MATERIALIZED VIEW IF EXISTS mv_shosha_approval_summary;

DROP TABLE IF EXISTS vertex_shosha_approval;
