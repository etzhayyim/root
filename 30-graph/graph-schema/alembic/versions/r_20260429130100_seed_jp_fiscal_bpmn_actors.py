"""Captured from Kysely migration 20260429130100_seed_jp_fiscal_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429130100_seed_jp_fiscal_bpmn_actors"
down_revision = 'r_20260429120100_seed_handotai_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/jp-fiscal-edinet-daily-v1',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'jp_fiscal_edinet_daily',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — EDINET 大量保有報告書 daily ingest (ADR-0035 T2 migration).\n'
                 '\n'
                 '  Pipeline:\n'
                 "    1. jpFiscal.ingest.edinet     — fetch EDINET v2 documents.json for today's "
                 'date,\n'
                 '                                    filter docTypeCode 140/350/4xx (大量保有報告書 '
                 'family),\n'
                 '                                    write to vertex_jp_fiscal_beneficial_owner.\n'
                 '    2. generic.audit.emit         — OCEL event with aggregate write counts.\n'
                 '\n'
                 '  Cadence: R/P1D (daily at midnight UTC approx — Zeebe timer-start).\n'
                 '\n'
                 '  NSID: ai.gftd.apps.jpFiscal.fiscalEdinetDaily\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/jp-fiscal-edinet-daily-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jp_fiscal_edinet_daily"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/jp-fiscal"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="jp_fiscal_edinet_daily" name="JP Fiscal EDINET daily" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.jpFiscal.fiscalEdinetDaily", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="daily">\n'
                 '      <bpmn:outgoing>Flow_ToIngest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P1D">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_ToIngest_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest"        sourceRef="Start_Timer"   '
                 'targetRef="Task_Ingest"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest_Manual" sourceRef="Start_Manual"  '
                 'targetRef="Task_Ingest"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit"         sourceRef="Task_Ingest"   '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End"             sourceRef="Task_Audit"    '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <!-- Step 1: Ingest EDINET 大量保有報告書 for today (default date). limit=500. -->\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest EDINET 大量保有報告書">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="jpFiscal.ingest.edinet"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=500"  target="limit"/>\n'
                 '          <zeebe:output source="=written" target="edinetWritten"/>\n'
                 '          <zeebe:output source="=total"   target="edinetTotal"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 2: Emit OCEL audit event. -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit EDINET ingest audit event">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.jpFiscal.fiscalEdinetDaily&quot;"  '
                 'target="event_type"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:jp-fiscal.etzhayyim.com&quot;"                 '
                 'target="actor_did"/>\n'
                 '          <zeebe:input source="={ edinetWritten: edinetWritten, edinetTotal: '
                 'edinetTotal }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3435,
                 '00-contracts/bpmn/ai/gftd/jp-fiscal/fiscalEdinetDaily.bpmn',
                 '2026-04-29T13:01:00Z',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'sys.bpmn.seed.jp-fiscal',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/jp-fiscal-edinet-daily-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/jp-fiscal-edinet-daily-v1',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'ai.gftd.apps.jpFiscal.fiscalEdinetDaily',
                 'jp_fiscal_edinet_daily',
                 300000,
                 '2026-04-29T13:01:00Z',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'sys.bpmn.seed.jp-fiscal',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/jp-fiscal-edinet-daily-v1']},
 {'sql': '\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/jp-fiscal-contract-weekly-v1',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'jp_fiscal_contract_weekly',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — e-GOV 省庁契約公表 weekly ingest (ADR-0035 T2 migration).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. jpFiscal.ingest.egovContracts — fetch contract CSV for 5 ministries\n'
                 '                                       (mof/mlit/meti/mext/mhlw),\n'
                 '                                       write to vertex_jp_fiscal_contract.\n'
                 '    2. generic.audit.emit            — OCEL event with aggregate write counts.\n'
                 '\n'
                 '  Cadence: R/P7D (weekly; Zeebe timer-start fires once per 7 days).\n'
                 '\n'
                 '  NSID: ai.gftd.apps.jpFiscal.fiscalContractWeekly\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/jp-fiscal-contract-weekly-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_jp_fiscal_contract_weekly"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/jp-fiscal"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="jp_fiscal_contract_weekly" name="JP Fiscal contract weekly" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.jpFiscal.fiscalContractWeekly", "version": 1, '
                 '"resultTimeoutMs": 600000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="weekly">\n'
                 '      <bpmn:outgoing>Flow_ToIngest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P7D">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_ToIngest_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest"        sourceRef="Start_Timer"   '
                 'targetRef="Task_Ingest"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest_Manual" sourceRef="Start_Manual"  '
                 'targetRef="Task_Ingest"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit"         sourceRef="Task_Ingest"   '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End"             sourceRef="Task_Audit"    '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <!-- Step 1: Ingest e-GOV contracts for all 5 ministries '
                 '(mof/mlit/meti/mext/mhlw). limit=50 per ministry. -->\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest e-GOV 省庁契約公表 CSV (5 '
                 'ministries)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="jpFiscal.ingest.egovContracts"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=50"   target="limit"/>\n'
                 '          <zeebe:output source="=written"   target="contractWritten"/>\n'
                 '          <zeebe:output source="=errors"    target="contractErrors"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 2: Emit OCEL audit event. -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit contract ingest audit event">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.jpFiscal.fiscalContractWeekly&quot;"  '
                 'target="event_type"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:jp-fiscal.etzhayyim.com&quot;"                    '
                 'target="actor_did"/>\n'
                 '          <zeebe:input source="={ contractWritten: contractWritten, '
                 'contractErrors: contractErrors }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3473,
                 '00-contracts/bpmn/ai/gftd/jp-fiscal/fiscalContractWeekly.bpmn',
                 '2026-04-29T13:01:00Z',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'sys.bpmn.seed.jp-fiscal',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/jp-fiscal-contract-weekly-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/jp-fiscal-contract-weekly-v1',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'ai.gftd.apps.jpFiscal.fiscalContractWeekly',
                 'jp_fiscal_contract_weekly',
                 600000,
                 '2026-04-29T13:01:00Z',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'did:web:jp-fiscal.etzhayyim.com',
                 'sys.bpmn.seed.jp-fiscal',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/jp-fiscal-contract-weekly-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/jp-fiscal-edinet-daily-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/jp-fiscal-edinet-daily-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/jp-fiscal-contract-weekly-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/jp-fiscal-contract-weekly-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
