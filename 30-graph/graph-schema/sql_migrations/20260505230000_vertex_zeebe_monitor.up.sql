CREATE MATERIALIZED VIEW IF NOT EXISTS mv_zeebe_instance_summary AS
    SELECT
      bpmn_process_id,
      SUM(CASE WHEN intent = 'ELEMENT_ACTIVATING'  THEN 1 ELSE 0 END) AS started_count,
      SUM(CASE WHEN intent = 'ELEMENT_COMPLETED'   THEN 1 ELSE 0 END) AS completed_count,
      SUM(CASE WHEN intent = 'ELEMENT_TERMINATED'  THEN 1 ELSE 0 END) AS terminated_count
    FROM vertex_zeebe_instance
    WHERE bpmn_element_type = 'PROCESS'
    GROUP BY bpmn_process_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_zeebe_incident_summary AS
    SELECT
      bpmn_process_id,
      SUM(CASE WHEN intent = 'CREATED'  THEN 1 ELSE 0 END) AS created_count,
      SUM(CASE WHEN intent = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_count
    FROM vertex_zeebe_incident
    GROUP BY bpmn_process_id;
