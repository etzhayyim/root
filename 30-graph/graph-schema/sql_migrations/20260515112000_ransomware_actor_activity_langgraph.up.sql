DELETE FROM vertex_langgraph_deployment
 WHERE assistant_id = 'ransomware_actor_activity';

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'ransomware_actor_activity';

INSERT INTO vertex_langgraph_assistant (
  vertex_id, _seq, sensitivity_ord, assistant_id, version, kind,
  factory_path, description, created_at
) VALUES (
  'ransomware_actor_activity', 0, 300, 'ransomware_actor_activity', 1,
  'py_factory',
  'pymagatama.langgraph_graphs.ransomware_actor_activity',
  'Passive ransomware actor activity ingest from public CTI feeds and existing onion crawl metadata; publishes sanitized Yabai risk intelligence.',
  '2026-05-15T11:20:00Z'
);

INSERT INTO vertex_langgraph_deployment (
  vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version,
  status, replicas, updated_at
) VALUES (
  'langgraph.builtin.ransomware_actor_activity', 0, 300,
  'langgraph.builtin.ransomware_actor_activity',
  'ransomware_actor_activity', 1, 'active', 1,
  '2026-05-15T11:20:00Z'
);
