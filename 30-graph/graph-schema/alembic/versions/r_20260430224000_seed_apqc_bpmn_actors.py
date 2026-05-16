"""Captured from Kysely migration 20260430224000_seed_apqc_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430224000_seed_apqc_bpmn_actors"
down_revision = 'r_20260430223000_vertex_risingwave_operation'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-materialize-subprocesses-v1',
                 'did:web:kyber-projector.gftd.ai',
                 'apqc_materialize_subprocesses',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_apqc_materialize_subprocesses"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/apqc"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="apqc_materialize_subprocesses" name="APQC subprocess '
                 'materialization" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Run</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Run" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="apqc materialize subprocesses">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="apqc.materializeSubprocesses"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if apqcCode != null then apqcCode else '
                 '&quot;&quot;" target="apqcCode"/>\n'
                 '          <zeebe:input source="=if subprocessCode != null then subprocessCode '
                 'else &quot;&quot;" target="subprocessCode"/>\n'
                 '          <zeebe:input source="=if callerDid != null then callerDid else '
                 '&quot;&quot;" target="callerDid"/>\n'
                 '          <zeebe:input source="=if dryRun != null then dryRun else false" '
                 'target="dryRun"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Run</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1594,
                 '00-contracts/bpmn/ai/gftd/apqc/materializeSubprocesses.bpmn',
                 '2026-04-30T22:40:00Z',
                 'did:web:kyber-projector.gftd.ai',
                 'did:web:kyber-projector.gftd.ai',
                 'sys.bpmn.seed.apqc',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-materialize-subprocesses-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-emit-event-v1',
                 'did:web:kyber-projector.gftd.ai',
                 'apqc_emit_event',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_apqc_emit_event"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/apqc"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="apqc_emit_event" name="APQC OCEL event emit" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Run</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Run" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="apqc emit event">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="apqc.emitEvent"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if apqcCode != null then apqcCode else '
                 '&quot;&quot;" target="apqcCode"/>\n'
                 '          <zeebe:input source="=if eventType != null then eventType else '
                 '&quot;apqc.activity&quot;" target="eventType"/>\n'
                 '          <zeebe:input source="=if taskId != null then taskId else &quot;&quot;" '
                 'target="taskId"/>\n'
                 '          <zeebe:input source="=if caseId != null then caseId else &quot;&quot;" '
                 'target="caseId"/>\n'
                 '          <zeebe:input source="=if objects != null then objects else []" '
                 'target="objects"/>\n'
                 '          <zeebe:input source="=if attributes != null then attributes else {}" '
                 'target="attributes"/>\n'
                 '          <zeebe:input source="=if actorDid != null then actorDid else '
                 '&quot;&quot;" target="actorDid"/>\n'
                 '          <zeebe:input source="=if callerDid != null then callerDid else '
                 '&quot;&quot;" target="callerDid"/>\n'
                 '          <zeebe:input source="=if dryRun != null then dryRun else false" '
                 'target="dryRun"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Run</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2021,
                 '00-contracts/bpmn/ai/gftd/apqc/emitEvent.bpmn',
                 '2026-04-30T22:40:00Z',
                 'did:web:kyber-projector.gftd.ai',
                 'did:web:kyber-projector.gftd.ai',
                 'sys.bpmn.seed.apqc',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-emit-event-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-coverage-snapshot-v1',
                 'did:web:kyber-projector.gftd.ai',
                 'apqc_coverage_snapshot',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_apqc_coverage_snapshot"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/apqc"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="apqc_coverage_snapshot" name="APQC coverage snapshot" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Run</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Run" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="apqc coverage snapshot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="apqc.coverageSnapshot"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Run</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1076,
                 '00-contracts/bpmn/ai/gftd/apqc/coverageSnapshot.bpmn',
                 '2026-04-30T22:40:00Z',
                 'did:web:kyber-projector.gftd.ai',
                 'did:web:kyber-projector.gftd.ai',
                 'sys.bpmn.seed.apqc',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-coverage-snapshot-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-materializeSubprocesses-v1',
                 'did:web:kyber-projector.gftd.ai',
                 'ai.gftd.apps.apqc.materializeSubprocesses',
                 'apqc_materialize_subprocesses',
                 60000,
                 '2026-04-30T22:40:00Z',
                 'did:web:kyber-projector.gftd.ai',
                 'did:web:kyber-projector.gftd.ai',
                 'sys.bpmn.seed.apqc',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-materializeSubprocesses-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-emitEvent-v1',
                 'did:web:kyber-projector.gftd.ai',
                 'ai.gftd.apps.apqc.emitEvent',
                 'apqc_emit_event',
                 60000,
                 '2026-04-30T22:40:00Z',
                 'did:web:kyber-projector.gftd.ai',
                 'did:web:kyber-projector.gftd.ai',
                 'sys.bpmn.seed.apqc',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-emitEvent-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-coverageSnapshot-v1',
                 'did:web:kyber-projector.gftd.ai',
                 'ai.gftd.apps.apqc.coverageSnapshot',
                 'apqc_coverage_snapshot',
                 30000,
                 '2026-04-30T22:40:00Z',
                 'did:web:kyber-projector.gftd.ai',
                 'did:web:kyber-projector.gftd.ai',
                 'sys.bpmn.seed.apqc',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-coverageSnapshot-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-materializeSubprocesses-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-emitEvent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apqc-coverageSnapshot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-materialize-subprocesses-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-emit-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apqc-coverage-snapshot-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
