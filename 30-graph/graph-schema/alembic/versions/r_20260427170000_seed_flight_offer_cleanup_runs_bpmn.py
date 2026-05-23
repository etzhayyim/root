"""Captured from Kysely migration 20260427170000_seed_flight_offer_cleanup_runs_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427170000_seed_flight_offer_cleanup_runs_bpmn"
down_revision = 'r_20260427160200_seed_flight_offer_source_health_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'flight_offer_cleanup_runs',\n"
         "           1, $3, CAST($4 AS integer), $5, 'active',\n"
         '           $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-cleanup-runs-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — daily cleanup of vertex_flight_offer_source_run.\n'
                 '  Default retention 90d. Also addressable via XRPC '
                 'ai.gftd.apps.flightOffer.cleanupRuns\n'
                 '  for ad-hoc / manual purges.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_cleanup_runs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_cleanup_runs" name="cleanupRuns" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.flightOffer.cleanupRuns", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 24 hours">\n'
                 '      <bpmn:outgoing>Flow_Health_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT24H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_Health_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_Timer" sourceRef="Start_Timer" '
                 'targetRef="Task_Health"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="rw.health.probe"/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Health_Timer</bpmn:incoming><bpmn:incoming>Flow_Health_Manual</bpmn:incoming><bpmn:outgoing>Flow_Cleanup</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Cleanup" sourceRef="Task_Health" '
                 'targetRef="Task_Cleanup"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Cleanup" name="delete old source-run rows">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.cleanupRuns"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if retentionDays != null then retentionDays else '
                 '90" target="retentionDays"/>\n'
                 '          <zeebe:output source="=deleted" target="deleted"/>\n'
                 '          <zeebe:output source="=cutoffAt" target="cutoffAt"/>\n'
                 '          <zeebe:output source="=retentionDays" target="retentionDaysOut"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Cleanup</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Cleanup" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cleanup">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:flight-offer.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;flight.offer.cleanupRuns&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={deleted: deleted, cutoffAt: cutoffAt, '
                 'retentionDays: retentionDaysOut}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3520,
                 '00-contracts/bpmn/ai/gftd/flight-offer/cleanupRuns.bpmn',
                 '2026-04-27T17:00:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-cleanup-runs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'ai.gftd.apps.flightOffer.cleanupRuns',\n"
         "           'flight_offer_cleanup_runs', 1, CAST(300000 AS integer), 'active',\n"
         '           $3, 1, $4, $5, $6\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $7)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-cleanup-runs-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 '2026-04-27T17:00:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-cleanup-runs-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-cleanup-runs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-cleanup-runs-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
