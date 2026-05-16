REVOKE ALL ON vertex_shosha_sanctions_list FROM kaisya_app;

REVOKE ALL ON vertex_shosha_sanctions_list FROM root;

DROP MATERIALIZED VIEW IF EXISTS mv_shosha_sanctions_count_by_source;

DROP TABLE IF EXISTS vertex_shosha_sanctions_list;
