"""Captured from Kysely migration 20260503100000_seed_common_crawl_extract_entities_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260503100000_seed_common_crawl_extract_entities_bpmn"
down_revision = 'r_20260503000000_seed_common_crawl_extract_entities_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord,\n'
         '      org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 100, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:commoncrawl.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/common-crawl-extract-entities-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'common_crawl_extract_entities',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"\n'
                 '  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"\n'
                 '  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '  id="Definitions_commonCrawlExtractEntities"\n'
                 '  targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '  exporter="Camunda Modeler"\n'
                 '  exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="common_crawl_extract_entities" '
                 'name="app.etzhayyim.apps.commonCrawl.extractEntities" isExecutable="true">\n'
                 '\n'
                 '    <!-- none-start: triggered by CF Worker XRPC extractEntities call via '
                 'proxyToBpmn() -->\n'
                 '    <bpmn:startEvent id="Start_Manual" name="extract triggered">\n'
                 '      <bpmn:outgoing>Flow_manual_to_extract</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <!-- timer-start: autonomous R/PT1H cadence — runs all 4 domains -->\n'
                 '    <bpmn:startEvent id="Start_Timer" name="hourly tick">\n'
                 '      <bpmn:outgoing>Flow_timer_to_extract</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_Hourly">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ExtractEntities" name="Extract entities from '
                 'pages">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="commonCrawl.entities.extract" retries="2" '
                 '/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=domain"    target="domain" />\n'
                 '          <zeebe:input source="=limit"     target="limit" />\n'
                 '          <zeebe:output source="=processed"  target="processed" />\n'
                 '          <zeebe:output source="=extracted"  target="extracted" />\n'
                 '          <zeebe:output source="=status"     target="extract_status" />\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_manual_to_extract</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_timer_to_extract</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_extract_to_audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="Emit audit event">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="2" />\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;commonCrawl.extractEntities&quot;"   '
                 'target="event_type" />\n'
                 '          <zeebe:input source="=domain"                                      '
                 'target="subject_id" />\n'
                 '          <zeebe:input source="=&quot;app.etzhayyim.apps.commonCrawl&quot;"        '
                 'target="actor" />\n'
                 '          <zeebe:input source="=extract_status"                              '
                 'target="result" />\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_extract_to_audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_audit_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End_Extracted" name="entities extracted">\n'
                 '      <bpmn:incoming>Flow_audit_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_manual_to_extract" sourceRef="Start_Manual"    '
                 'targetRef="Task_ExtractEntities" />\n'
                 '    <bpmn:sequenceFlow id="Flow_timer_to_extract"  sourceRef="Start_Timer"     '
                 'targetRef="Task_ExtractEntities" />\n'
                 '    <bpmn:sequenceFlow id="Flow_extract_to_audit"  '
                 'sourceRef="Task_ExtractEntities" targetRef="Task_Audit" />\n'
                 '    <bpmn:sequenceFlow id="Flow_audit_to_end"      sourceRef="Task_Audit"      '
                 'targetRef="End_Extracted" />\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '\n'
                 '</bpmn:definitions>\n',
                 3450,
                 '00-contracts/bpmn/ai/gftd/common-crawl/extractEntities.bpmn',
                 '2026-05-03T10:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:commoncrawl.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:commoncrawl.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/common-crawl-extract-entities-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id,\n'
         '      status, created_at, sensitivity_ord,\n'
         '      org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4,\n'
         "      'active', $5, 100,\n"
         "      $6, $7, $8, $9, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:commoncrawl.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/common-crawl-extract-entities-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'app.etzhayyim.apps.commonCrawl.extractEntities',
                 'common_crawl_extract_entities',
                 '2026-05-03T10:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:commoncrawl.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:commoncrawl.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/common-crawl-extract-entities-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:commoncrawl.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/common-crawl-extract-entities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:commoncrawl.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/common-crawl-extract-entities-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
