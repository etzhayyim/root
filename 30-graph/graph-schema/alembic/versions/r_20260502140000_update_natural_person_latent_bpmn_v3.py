"""Captured from Kysely migration 20260502140000_update_natural_person_latent_bpmn_v3."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260502140000_update_natural_person_latent_bpmn_v3"
down_revision = 'r_20260502130000_seed_training_export_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': 'UPDATE vertex_bpmn_process_def SET "version" = 3 WHERE bpmn_process_id = $1',
  'parameters': ['natural_person_materialize_all_latent_entities_v1']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET "xml" = $1 WHERE bpmn_process_id = $2',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  naturalPerson.materializeAllLatentEntities\n'
                 '\n'
                 '  Timer:\n'
                 '    R/PT1M. Every minute, materialize a bounded batch of individual latent\n'
                 '    vertices from natural-person cohort estimated counts. Progress is tracked\n'
                 '    in vertex_natural_person_latent_materialization_cursor, so the job is\n'
                 '    idempotent and resumable.\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.naturalPerson.materializeAllLatentEntities\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="naturalPersonMaterializeAllLatentEntities"\n'
                 '    targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '    exporter="Camunda Modeler"\n'
                 '    exporterVersion="3.0">\n'
                 '\n'
                 '  <bpmn:process id="natural_person_materialize_all_latent_entities_v1" '
                 'name="naturalPerson.materializeAllLatentEntities" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/PT1M timer">\n'
                 '      <bpmn:outgoing>Flow_timer_to_ensure_cursors</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_1M">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="XRPC trigger">\n'
                 '      <bpmn:outgoing>Flow_manual_to_ensure_cursors</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EnsureCursors" name="Ensure cohort '
                 'materialization cursors">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;INSERT INTO '
                 'vertex_natural_person_latent_materialization_cursor (vertex_id, _seq, '
                 'sensitivity_ord, owner_did, actor_did, org_did, created_at, updated_at, '
                 'cohort_vid, cohort_hash, target_count, next_ordinal, materialized_count, '
                 'batch_size, status) SELECT '
                 "'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.latentCursor/' "
                 "|| c.cohort_hash, 1, 300, 'did:web:natural-person.etzhayyim.com', "
                 "'did:web:natural-person.etzhayyim.com', 'did:web:natural-person.etzhayyim.com', NOW(), "
                 'NOW(), c.vertex_id, c.cohort_hash, GREATEST(COALESCE(c.intel_estimated_count, '
                 '0), 0), 1, 0, 1000000, CASE WHEN GREATEST(COALESCE(c.intel_estimated_count, 0), '
                 "0) &gt; 0 THEN 'active' ELSE 'complete' END FROM "
                 'vertex_natural_person_cohort_person c WHERE c.cohort_hash IS NOT NULL AND '
                 "c.cohort_hash &lt;&gt; '' AND NOT EXISTS (SELECT 1 FROM "
                 'vertex_natural_person_latent_materialization_cursor x WHERE x.cohort_hash = '
                 'c.cohort_hash)&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=300000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=updated" target="cursorsInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_timer_to_ensure_cursors</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_manual_to_ensure_cursors</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ensure_to_read_work</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ReadWork" name="Read next cursor batch">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, cohort_vid, cohort_hash, '
                 'target_count, next_ordinal, batch_size, LEAST(next_ordinal + batch_size - 1, '
                 'target_count) AS end_ordinal, LEAST(batch_size, target_count - next_ordinal + 1) '
                 'AS planned_individuals FROM vertex_natural_person_latent_materialization_cursor '
                 "WHERE status = 'active' AND next_ordinal &lt;= target_count ORDER BY updated_at "
                 'ASC NULLS FIRST, cohort_hash LIMIT 1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=60000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rows[1]" target="latentBatch"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ensure_to_read_work</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_read_to_insert_vertices</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_InsertVertices" name="Insert individual latent '
                 'vertices">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;INSERT INTO vertex_latent_entity '
                 '(vertex_id, _seq, sensitivity_ord, owner_did, actor_did, org_did, created_at, '
                 'entity_kind, canonical_label, existence_probability, k_evidence_count, '
                 'viewpoint_consensus, fission_eligible, status, primary_topic_vid, '
                 'individual_did) SELECT '
                 "'at://did:web:coverage.etzhayyim.com/app.etzhayyim.apps.coverage.latentEntity/natural-person-individual-' "
                 "|| w.cohort_hash || '-' || LPAD(g.i::VARCHAR, 12, '0'), g.i, 300, "
                 "'did:web:coverage.etzhayyim.com', 'did:web:coverage.etzhayyim.com', "
                 "'did:web:coverage.etzhayyim.com', NOW(), 'natural_person_individual_latent', 'natural "
                 "person latent: ' || w.cohort_hash || ' #' || g.i::VARCHAR, 0.50, 1, 1, false, "
                 "'active', w.cohort_vid, 'did:web:natural-person.etzhayyim.com:latent:' || "
                 "w.cohort_hash || ':' || g.i::VARCHAR FROM (SELECT vertex_id, cohort_vid, "
                 'cohort_hash, target_count, next_ordinal, LEAST(next_ordinal + batch_size - 1, '
                 'target_count) AS end_ordinal FROM '
                 "vertex_natural_person_latent_materialization_cursor WHERE status = 'active' AND "
                 'next_ordinal &lt;= target_count ORDER BY updated_at ASC NULLS FIRST, cohort_hash '
                 'LIMIT 1) w, generate_series(w.next_ordinal, w.end_ordinal) AS g(i)&quot;" '
                 'target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=600000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=updated" target="insertedIndividuals"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_read_to_insert_vertices</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_insert_to_advance_cursor</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AdvanceCursor" name="Advance cursor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;UPDATE '
                 'vertex_natural_person_latent_materialization_cursor SET next_ordinal = '
                 'LEAST(target_count + 1, next_ordinal + batch_size), materialized_count = '
                 'LEAST(target_count, materialized_count + batch_size), status = CASE WHEN '
                 "next_ordinal + batch_size &gt; target_count THEN 'complete' ELSE 'active' END, "
                 'updated_at = NOW() WHERE vertex_id = (SELECT vertex_id FROM '
                 "vertex_natural_person_latent_materialization_cursor WHERE status = 'active' AND "
                 'next_ordinal &lt;= target_count ORDER BY updated_at ASC NULLS FIRST, cohort_hash '
                 'LIMIT 1)&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=60000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=updated" target="advancedCursors"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_insert_to_advance_cursor</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_advance_to_verify</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Verify" name="Verify materialization totals">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT COALESCE(SUM(GREATEST(target_count '
                 '- next_ordinal + 1, 0)), 0)::bigint AS remaining_individuals FROM '
                 'vertex_natural_person_latent_materialization_cursor WHERE status = '
                 '\'active\'&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=60000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rows[1]" target="materializationVerify"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_advance_to_verify</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_verify_to_audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="OCEL audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:natural-person.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;naturalPerson.materializeAllLatentEntities.complete&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '              &quot;cursorsInserted&quot;: cursorsInserted,\n'
                 '              &quot;plannedIndividuals&quot;: latentBatch.planned_individuals,\n'
                 '              &quot;insertedIndividuals&quot;: insertedIndividuals,\n'
                 '              &quot;advancedCursors&quot;: advancedCursors,\n'
                 '              &quot;remainingIndividuals&quot;: '
                 'materializationVerify.remaining_individuals\n'
                 '          }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_verify_to_audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_audit_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="Done">\n'
                 '      <bpmn:incoming>Flow_audit_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_timer_to_ensure_cursors" sourceRef="Start_Timer" '
                 'targetRef="Task_EnsureCursors"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_manual_to_ensure_cursors" '
                 'sourceRef="Start_Manual" targetRef="Task_EnsureCursors"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ensure_to_read_work" '
                 'sourceRef="Task_EnsureCursors" targetRef="Task_ReadWork"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_read_to_insert_vertices" '
                 'sourceRef="Task_ReadWork" targetRef="Task_InsertVertices"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_insert_to_advance_cursor" '
                 'sourceRef="Task_InsertVertices" targetRef="Task_AdvanceCursor"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_advance_to_verify" '
                 'sourceRef="Task_AdvanceCursor" targetRef="Task_Verify"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_verify_to_audit" sourceRef="Task_Verify" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_audit_to_end" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 'natural_person_materialize_all_latent_entities_v1']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET xml_byte_size = $1 WHERE bpmn_process_id = $2',
  'parameters': [9976, 'natural_person_materialize_all_latent_entities_v1']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET deployed_at = $1 WHERE bpmn_process_id = $2',
  'parameters': ['2026-05-08T00:43:24.631Z', 'natural_person_materialize_all_latent_entities_v1']},
 {'sql': 'UPDATE vertex_natural_person_latent_materialization_cursor SET batch_size = 1000000 '
         "WHERE status = 'active'",
  'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
