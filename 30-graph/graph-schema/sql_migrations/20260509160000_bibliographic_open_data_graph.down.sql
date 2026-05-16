DELETE FROM vertex_langgraph_deployment
WHERE vertex_id = 'langgraph.builtin.biblio_open_data_ingest';

DELETE FROM vertex_langgraph_assistant
WHERE vertex_id = 'biblio_open_data_ingest';

DROP TABLE IF EXISTS vertex_biblio_ingest_run;
DROP TABLE IF EXISTS vertex_biblio_ingest_cursor;
DROP TABLE IF EXISTS edge_biblio_relation;
DROP TABLE IF EXISTS vertex_biblio_identifier;
DROP TABLE IF EXISTS vertex_biblio_entity;
DROP TABLE IF EXISTS vertex_biblio_raw_record;
DROP TABLE IF EXISTS vertex_biblio_source;
