"""Captured from Kysely migration 20260430700100_seed_ir_scrape_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430700100_seed_ir_scrape_bpmn"
down_revision = 'r_20260430700000_vertex_ir_company'
branch_labels = None
depends_on = None

UP = [{'sql': 'INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, '
         'status,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer),\n'
         "             $6, 'active', $7, 100,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ir-scrape-queue-seeds-v1',
                 'did:web:news.gftd.ai',
                 'ir_scrape_queue_seeds',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — seeds IR company registry and queues scrape runs every 6 '
                 'hours.\n'
                 '  Task handler: irScrape.queueSeeds (pymagatama ir_scrape.py)\n'
                 '  NSID: ai.gftd.apps.irScrape.queueSeeds\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ir-scrape-queue-seeds-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_ir_scrape_queue_seeds"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/irScrape"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="ir_scrape_queue_seeds" name="IR Scrape: Queue Seeds" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.irScrape.queueSeeds", "version": 1, '
                 '"resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 6 hours">\n'
                 '      <bpmn:outgoing>Flow_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT6H">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT6H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer"  sourceRef="Start_Timer"  '
                 'targetRef="Task_Queue"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Queue"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Queue" name="seed companies + queue runs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="irScrape.queueSeeds" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if maxSeeds = null then 200 else maxSeeds" '
                 'target="maxSeeds"/>\n'
                 '          <zeebe:output source="=queued"         target="queued"/>\n'
                 '          <zeebe:output source="=skipped"        target="skipped"/>\n'
                 '          <zeebe:output source="=companiesAdded" target="companiesAdded"/>\n'
                 '          <zeebe:output source="=ok"             target="queueOk"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Timer</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Queue" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit irScrape.queueSeeds OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.irScrape.queueSeeds.completed&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;queued&quot;: queued, '
                 '&quot;skipped&quot;: skipped, &quot;companiesAdded&quot;: companiesAdded, '
                 '&quot;ok&quot;: queueOk }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_3</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_3</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3311,
                 '00-contracts/bpmn/ai/gftd/irScrape/queueSeeds.bpmn',
                 '2026-04-30T21:00:00+09:00',
                 'did:web:news.gftd.ai',
                 'did:web:news.gftd.ai',
                 'sys.bpmn.seed.irScrape',
                 'did:web:news.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ir-scrape-queue-seeds-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '       write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '       actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         '             CAST($5 AS integer), $6,\n'
         "             'active', $7, 100,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ir-scrape-queue-seeds-v1',
                 'did:web:news.gftd.ai',
                 'ai.gftd.apps.irScrape.queueSeeds',
                 'ir_scrape_queue_seeds',
                 120000,
                 'vertex_ir_company,vertex_ir_scraper_run',
                 '2026-04-30T21:00:00+09:00',
                 'did:web:news.gftd.ai',
                 'did:web:news.gftd.ai',
                 'sys.bpmn.seed.irScrape',
                 'did:web:news.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ir-scrape-queue-seeds-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, '
         'status,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer),\n'
         "             $6, 'active', $7, 100,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ir-scrape-process-queue-v1',
                 'did:web:news.gftd.ai',
                 'ir_scrape_process_queue',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — picks queued IR scraper runs, fetches company IR pages,\n'
                 '  extracts press releases, writes vertex_ir_pressrelease.\n'
                 '  Task handler: irScrape.processQueue (pymagatama ir_scrape.py)\n'
                 '  NSID: ai.gftd.apps.irScrape.processQueue\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ir-scrape-process-queue-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_ir_scrape_process_queue"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/irScrape"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="ir_scrape_process_queue" name="IR Scrape: Process Queue" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.irScrape.processQueue", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 1 hour">\n'
                 '      <bpmn:outgoing>Flow_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT1H">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer"  sourceRef="Start_Timer"  '
                 'targetRef="Task_Process"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Process"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Process" name="fetch IR pages + extract press '
                 'releases">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="irScrape.processQueue" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if maxRuns = null then 5 else '
                 'maxRuns"             target="maxRuns"/>\n'
                 '          <zeebe:input source="=if fetchTimeoutSec = null then 30 else '
                 'fetchTimeoutSec" target="fetchTimeoutSec"/>\n'
                 '          <zeebe:output source="=processed" target="processed"/>\n'
                 '          <zeebe:output source="=inserted"  target="inserted"/>\n'
                 '          <zeebe:output source="=errors"    target="errors"/>\n'
                 '          <zeebe:output source="=ok"        target="processOk"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Timer</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Process" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit irScrape.processQueue OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.irScrape.processQueue.completed&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;processed&quot;: processed, '
                 '&quot;inserted&quot;: inserted, &quot;errors&quot;: errors, &quot;ok&quot;: '
                 'processOk }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_3</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_3</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3494,
                 '00-contracts/bpmn/ai/gftd/irScrape/processQueue.bpmn',
                 '2026-04-30T21:00:00+09:00',
                 'did:web:news.gftd.ai',
                 'did:web:news.gftd.ai',
                 'sys.bpmn.seed.irScrape',
                 'did:web:news.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ir-scrape-process-queue-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '       write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '       actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         '             CAST($5 AS integer), $6,\n'
         "             'active', $7, 100,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ir-scrape-process-queue-v1',
                 'did:web:news.gftd.ai',
                 'ai.gftd.apps.irScrape.processQueue',
                 'ir_scrape_process_queue',
                 300000,
                 'vertex_ir_scraper_run,vertex_ir_pressrelease',
                 '2026-04-30T21:00:00+09:00',
                 'did:web:news.gftd.ai',
                 'did:web:news.gftd.ai',
                 'sys.bpmn.seed.irScrape',
                 'did:web:news.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ir-scrape-process-queue-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ir-scrape-queue-seeds-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ir-scrape-queue-seeds-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ir-scrape-process-queue-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ir-scrape-process-queue-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
