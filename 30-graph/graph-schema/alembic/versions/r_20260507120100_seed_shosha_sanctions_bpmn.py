"""Captured from Kysely migration 20260507120100_seed_shosha_sanctions_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507120100_seed_shosha_sanctions_bpmn"
down_revision = 'r_20260507120000_vertex_shosha_sanctions_list'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-refresh-sanctions-list-v1',
                 'did:web:shosha.etzhayyim.com',
                 'shosha_refresh_sanctions_list',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  shosha.etzhayyim.com — sanctions list refresh (autonomous, cron 0 0 1 * * ? = 01:00 '
                 'UTC).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. shosha.sanctions.refreshOfac    Fetch OFAC SDN.CSV (US Treasury), parse,\n'
                 '                                        upsert into '
                 'vertex_shosha_sanctions_list.\n'
                 '                                        Phase 2b: OFAC only. EU/UN/JP-MOFA in\n'
                 '                                        Phase 2b-extended.\n'
                 '    2. generic.audit.emit              OCEL trail.\n'
                 '\n'
                 '  Cron 01:00 UTC chosen so refresh completes before US East Coast business\n'
                 "  hours and well before any TZ's typical daily report fire.\n"
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_shosha_refresh_sanctions_list"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/shosha"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="shosha_refresh_sanctions_list" name="shosha refresh '
                 'sanctions list (daily 01 UTC)" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="daily 01:00 UTC">\n'
                 '      <bpmn:outgoing>Flow_ToOfac</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 1 * * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ofac" name="refresh OFAC SDN list">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="shosha.sanctions.refreshOfac"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=rows" target="ofacRows"/>\n'
                 '          <zeebe:output source="=inserted" target="ofacInserted"/>\n'
                 '          <zeebe:output source="=updated" target="ofacUpdated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToOfac</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToUn</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToOfac" sourceRef="StartTimer" '
                 'targetRef="Task_Ofac"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Un" name="refresh UN 1267 list">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="shosha.sanctions.refreshUn"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=rows" target="unRows"/>\n'
                 '          <zeebe:output source="=inserted" target="unInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToUn</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToUn" sourceRef="Task_Ofac" '
                 'targetRef="Task_Un"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:shosha.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;app.etzhayyim.apps.shosha.refreshSanctionsList&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;ofacRows&quot;: ofacRows, '
                 '&quot;ofacInserted&quot;: ofacInserted, &quot;ofacUpdated&quot;: ofacUpdated, '
                 '&quot;unRows&quot;: unRows, &quot;unInserted&quot;: unInserted }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Un" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3711,
                 '00-contracts/bpmn/ai/gftd/shosha/refreshSanctionsList.bpmn',
                 '2026-05-07T12:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase2b',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-refresh-sanctions-list-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-refresh-sanctions-list-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
