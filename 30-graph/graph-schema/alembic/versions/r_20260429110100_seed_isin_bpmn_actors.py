"""Captured from Kysely migration 20260429110100_seed_isin_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429110100_seed_isin_bpmn_actors"
down_revision = 'r_20260429110000_vertex_isin_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isin-collect-v1',
                 'did:web:isin.etzhayyim.com',
                 'isin_collect',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — ISIN securities collection (US + JP, every 6 hours).\n'
                 '\n'
                 '  Pipeline:\n'
                 '\n'
                 '    1. isin.collect.usSecurities  — fetch EDGAR company_tickers.json, batch via\n'
                 '                                    OpenFIGI (100/req), write to '
                 'vertex_isin_security.\n'
                 '    2. isin.collect.jpSecurities  — OpenFIGI JP ticker range 1000-9999 (10/req '
                 'free\n'
                 '                                    tier), write to vertex_isin_security.\n'
                 '    3. generic.audit.emit         — OCEL event with aggregate write counts.\n'
                 '\n'
                 '  Cadence: R/PT6H. One BPMN instance every 6 hours.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.isin.isinCollect\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isin-collect-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_isin_collect"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/isin"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="isin_collect" name="isin collect" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.isin.isinCollect", "version": 1, '
                 '"resultTimeoutMs": 600000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 6 hours">\n'
                 '      <bpmn:outgoing>Flow_ToCollectUS</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT6H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT6H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_ToCollectUS_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCollectUS"        '
                 'sourceRef="Start_Timer"          targetRef="Task_CollectUS"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCollectUS_Manual" '
                 'sourceRef="Start_Manual"          targetRef="Task_CollectUS"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCollectJP"        '
                 'sourceRef="Task_CollectUS"        targetRef="Task_CollectJP"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit"            '
                 'sourceRef="Task_CollectJP"        targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End"                '
                 'sourceRef="Task_Audit"            targetRef="End"/>\n'
                 '\n'
                 '    <!-- Step 1: Collect US securities from EDGAR + OpenFIGI (offset=0 '
                 'limit=200, enrichFigi=true). -->\n'
                 '    <bpmn:serviceTask id="Task_CollectUS" name="collect US securities (EDGAR + '
                 'OpenFIGI)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="isin.collect.usSecurities"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=0"    target="offset"/>\n'
                 '          <zeebe:input source="=200"  target="limit"/>\n'
                 '          <zeebe:input source="=true" target="enrichFigi"/>\n'
                 '          <zeebe:output source="=written" target="usWritten"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 2: Collect JP securities from OpenFIGI ticker range 1000-9999 '
                 '(fromTicker=1000 count=25). -->\n'
                 '    <bpmn:serviceTask id="Task_CollectJP" name="collect JP securities (OpenFIGI '
                 'ticker range)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="isin.collect.jpSecurities"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=1000" target="fromTicker"/>\n'
                 '          <zeebe:input source="=25"   target="count"/>\n'
                 '          <zeebe:output source="=written" target="jpWritten"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 3: Emit OCEL audit event with aggregate write counts. -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit collect audit event">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;com.etzhayyim.apps.isin.isinCollect&quot;" '
                 'target="event_type"/>\n'
                 '          <zeebe:input source="=&quot;did:web:isin.etzhayyim.com&quot;"          '
                 'target="actor_did"/>\n'
                 '          <zeebe:input source="={ usWritten: usWritten, jpWritten: jpWritten }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4224,
                 '00-contracts/bpmn/com/etzhayyim/isin/isinCollect.bpmn',
                 '2026-04-29T11:01:00Z',
                 'did:web:isin.etzhayyim.com',
                 'did:web:isin.etzhayyim.com',
                 'sys.bpmn.seed.isin',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isin-collect-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isin-collect-v1',
                 'did:web:isin.etzhayyim.com',
                 'com.etzhayyim.apps.isin.isinCollect',
                 'isin_collect',
                 600000,
                 '2026-04-29T11:01:00Z',
                 'did:web:isin.etzhayyim.com',
                 'did:web:isin.etzhayyim.com',
                 'sys.bpmn.seed.isin',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isin-collect-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isin-collect-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isin-collect-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
