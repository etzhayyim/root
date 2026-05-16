INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, assistant_id,
   version, kind, factory_path, description, created_at)
VALUES
  ('biblio_asia_open_data_actor', 0, DATE '2026-05-09', 2, 'did:web:biblio.gftd.ai',
   'biblio_asia_open_data_actor', 1, 'py_factory',
   'pymagatama.langgraph_graphs.biblio_asia_open_data_actor',
   'India, China, and Korea bibliographic open-data ingest actor',
   '2026-05-09T16:10:00Z');

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, nsid,
   assistant_id, version, status, replicas, updated_at)
VALUES
  ('langgraph.builtin.biblio_asia_open_data_actor', 0, DATE '2026-05-09', 2,
   'did:web:biblio.gftd.ai', 'langgraph.builtin.biblio_asia_open_data_actor',
   'biblio_asia_open_data_actor', 1, 'active', 1, '2026-05-09T16:10:00Z');
