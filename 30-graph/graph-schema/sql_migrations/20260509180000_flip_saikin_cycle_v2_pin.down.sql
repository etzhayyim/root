-- Roll back the pin: point langgraph.builtin.saikin.cycle.v1 at saikin.cycle.v1.
INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at)
VALUES
  ('langgraph.builtin.saikin.cycle.v1', 0, 0,
   'langgraph.builtin.saikin.cycle.v1', 'saikin.cycle.v1', 1, 'active', 1,
   '2026-05-09T00:00:00Z');

FLUSH;
