REVOKE ALL ON vertex_shosha_reaction        FROM kaisya_app;

REVOKE ALL ON vertex_shosha_reaction        FROM root;

REVOKE ALL ON vertex_shosha_consumer_cursor FROM kaisya_app;

REVOKE ALL ON vertex_shosha_consumer_cursor FROM root;

DROP MATERIALIZED VIEW IF EXISTS mv_shosha_reaction_count_by_upstream;

DROP TABLE IF EXISTS vertex_shosha_reaction;

DROP TABLE IF EXISTS vertex_shosha_consumer_cursor;
