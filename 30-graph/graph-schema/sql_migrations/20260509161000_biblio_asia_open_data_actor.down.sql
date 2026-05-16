DELETE FROM vertex_langgraph_deployment
WHERE vertex_id = 'langgraph.builtin.biblio_asia_open_data_actor';

DELETE FROM vertex_langgraph_assistant
WHERE vertex_id = 'biblio_asia_open_data_actor';
