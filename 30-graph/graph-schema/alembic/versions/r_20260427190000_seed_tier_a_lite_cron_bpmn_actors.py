"""Captured from Kysely migration 20260427190000_seed_tier_a_lite_cron_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427190000_seed_tier_a_lite_cron_bpmn_actors"
down_revision = 'r_20260427180100_seed_telecom_5gcore_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.tier_a_lite_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/atproto-cron-tick-v1',
                 'did:web:atproto.etzhayyim.com',
                 'atproto_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — atproto cron tick (every 5 min).\n'
                 '  Replaces CF cron trigger per ADR-2604251801 §4-A and ADR-0056.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.atproto.cronTick\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/atproto-cron-tick-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_atproto_cron_tick"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/atproto"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="atproto_cron_tick" name="atproto cron tick (R/PT5M)" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.atproto.cronTick", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 5 min">\n'
                 '      <bpmn:outgoing>Flow_1</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Tick"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Tick" name="cronTick dispatch">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;com.etzhayyim.apps.atproto.cronTick&quot;" '
                 'target="type"/>\n'
                 '          <zeebe:input source="={}"                                        '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=status" target="tickStatus"/>\n'
                 '          <zeebe:output source="=body"   target="tickResult"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Tick" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit atproto.cron.tick OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;com.etzhayyim.apps.atproto.cron.tick&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;status&quot;: tickStatus, '
                 '&quot;ok&quot;: tickResult.ok }" target="attributes"/>\n'
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
                 2795,
                 '00-contracts/bpmn/com/etzhayyim/atproto/cronTick.bpmn',
                 '2026-04-27T19:00:00Z',
                 'did:web:atproto.etzhayyim.com',
                 'did:web:atproto.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/atproto-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.tier_a_lite_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/claim-cron-tick-v1',
                 'did:web:claim-consumer.etzhayyim.com',
                 'claim_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — claim cron tick (every 1 min).\n'
                 '  Replaces CF cron trigger per ADR-2604251801 §4-A and ADR-0056.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.claim.cronTick\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/claim-cron-tick-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_claim_cron_tick"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/claim"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="claim_cron_tick" name="claim cron tick (R/PT1M)" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.claim.cronTick", "version": 1, "resultTimeoutMs": '
                 '60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 1 min">\n'
                 '      <bpmn:outgoing>Flow_1</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT1M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Tick"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Tick" name="cronTick XRPC">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://claim-consumer.etzhayyim.com/xrpc/com.etzhayyim.apps.claim.cronTick&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="=&quot;POST&quot;"             target="method"/>\n'
                 '          <zeebe:input source="=&quot;application/json&quot;" '
                 'target="contentType"/>\n'
                 '          <zeebe:input source="={}"                           target="body"/>\n'
                 '          <zeebe:input source="=45000"                        '
                 'target="timeoutMs"/>\n'
                 '          <zeebe:output source="=status"   target="tickStatus"/>\n'
                 '          <zeebe:output source="=bodyJson" target="tickResult"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Tick" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit claim.cron.tick OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;com.etzhayyim.apps.claim.cron.tick&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;status&quot;: tickStatus, '
                 '&quot;ok&quot;: tickResult.ok }" target="attributes"/>\n'
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
                 3038,
                 '00-contracts/bpmn/com/etzhayyim/claim/cronTick.bpmn',
                 '2026-04-27T19:00:00Z',
                 'did:web:claim-consumer.etzhayyim.com',
                 'did:web:claim-consumer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/claim-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.tier_a_lite_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/murakumo-cron-tick-v1',
                 'did:web:murakumo.etzhayyim.com',
                 'murakumo_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — murakumo cron tick (every 5 min).\n'
                 '  Replaces CF cron trigger per ADR-2604251801 §4-A and ADR-0056.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.murakumo.cronTick\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/murakumo-cron-tick-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_murakumo_cron_tick"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/murakumo"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="murakumo_cron_tick" name="murakumo cron tick (R/PT5M)" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.murakumo.cronTick", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 5 min">\n'
                 '      <bpmn:outgoing>Flow_1</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Tick"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Tick" name="cronTick XRPC">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://murakumo.etzhayyim.com/xrpc/com.etzhayyim.apps.murakumo.cronTick&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="=&quot;POST&quot;"             target="method"/>\n'
                 '          <zeebe:input source="=&quot;application/json&quot;" '
                 'target="contentType"/>\n'
                 '          <zeebe:input source="={}"                           target="body"/>\n'
                 '          <zeebe:input source="=45000"                        '
                 'target="timeoutMs"/>\n'
                 '          <zeebe:output source="=status"   target="tickStatus"/>\n'
                 '          <zeebe:output source="=bodyJson" target="tickResult"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Tick" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit murakumo.cron.tick OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;com.etzhayyim.apps.murakumo.cron.tick&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;status&quot;: tickStatus, '
                 '&quot;ok&quot;: tickResult.ok }" target="attributes"/>\n'
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
                 3065,
                 '00-contracts/bpmn/com/etzhayyim/murakumo/cronTick.bpmn',
                 '2026-04-27T19:00:00Z',
                 'did:web:murakumo.etzhayyim.com',
                 'did:web:murakumo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/murakumo-cron-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.tier_a_lite_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/atproto-cronTick-v1',
                 'did:web:atproto.etzhayyim.com',
                 'com.etzhayyim.apps.atproto.cronTick',
                 'atproto_cron_tick',
                 60000,
                 '2026-04-27T19:00:00Z',
                 'did:web:atproto.etzhayyim.com',
                 'did:web:atproto.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/atproto-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.tier_a_lite_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/claim-cronTick-v1',
                 'did:web:claim-consumer.etzhayyim.com',
                 'com.etzhayyim.apps.claim.cronTick',
                 'claim_cron_tick',
                 60000,
                 '2026-04-27T19:00:00Z',
                 'did:web:claim-consumer.etzhayyim.com',
                 'did:web:claim-consumer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/claim-cronTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.tier_a_lite_cron'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/murakumo-cronTick-v1',
                 'did:web:murakumo.etzhayyim.com',
                 'com.etzhayyim.apps.murakumo.cronTick',
                 'murakumo_cron_tick',
                 60000,
                 '2026-04-27T19:00:00Z',
                 'did:web:murakumo.etzhayyim.com',
                 'did:web:murakumo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/murakumo-cronTick-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/atproto-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/claim-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/murakumo-cronTick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/atproto-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/claim-cron-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/murakumo-cron-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
