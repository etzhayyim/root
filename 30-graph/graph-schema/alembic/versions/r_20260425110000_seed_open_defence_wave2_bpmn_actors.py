"""Captured from Kysely migration 20260425110000_seed_open_defence_wave2_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425110000_seed_open_defence_wave2_bpmn_actors"
down_revision = 'r_20260425102500_seed_patent_bulk_ingest_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-threat-assess-threat-actor-v1',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'open_cyber_threat_assess_threat_actor',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cyber_threat_assess_threat_actor"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cyber-threat"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_threat_assess_threat_actor" name="脅威アクター 評価" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_cyber_threat_assess_threat_actor&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cyberThreat.assessThreatActor&quot;,\n'
                 '              project:          &quot;open-cyber-threat&quot;,\n'
                 '              subject_vid:      threatActorVid,\n'
                 '              action_class:     &quot;cyber.threatActor&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.threatActor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-cyber-threat.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.threatActor&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: threatActorVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2976,
                 '00-contracts/bpmn/com/etzhayyim/open-cyber-threat/assessThreatActor.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-threat-assess-threat-actor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-link-exploit-to-actor-v1',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'open_cyber_vuln_link_exploit_to_actor',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cyber_vuln_link_exploit_to_actor"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cyber-vuln"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_vuln_link_exploit_to_actor" name="エクスプロイト→アクター '
                 '紐付" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_cyber_vuln_link_exploit_to_actor&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cyberVuln.linkExploitToActor&quot;,\n'
                 '              project:          &quot;open-cyber-vuln&quot;,\n'
                 '              subject_vid:      cveId,\n'
                 '              action_class:     &quot;cyber.exploitLink&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.exploitLink">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-cyber-vuln.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.exploitLink&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: cveId, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2969,
                 '00-contracts/bpmn/com/etzhayyim/open-cyber-vuln/linkExploitToActor.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-link-exploit-to-actor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-zero-day-broker-flag-zero-day-trade-v1',
                 'did:web:open-zero-day-broker.etzhayyim.com:ops',
                 'open_zero_day_broker_flag_zero_day_trade',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_zero_day_broker_flag_zero_day_trade"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-zero-day-broker"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_zero_day_broker_flag_zero_day_trade" name="ゼロデイ取引 フラグ" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_zero_day_broker_flag_zero_day_trade&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.zeroDayBroker.flagZeroDayTrade&quot;,\n'
                 '              project:          &quot;open-zero-day-broker&quot;,\n'
                 '              subject_vid:      brokerLei,\n'
                 '              action_class:     &quot;cyber.zeroDayTrade&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.zeroDayTrade">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-zero-day-broker.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.zeroDayTrade&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: brokerLei, '
                 'severity: &quot;critical&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2999,
                 '00-contracts/bpmn/com/etzhayyim/open-zero-day-broker/flagZeroDayTrade.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-zero-day-broker.etzhayyim.com:ops',
                 'did:web:open-zero-day-broker.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-zero-day-broker-flag-zero-day-trade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-weaponized-cve-v1',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'open_cve_cna_flag_weaponized_cve',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cve_cna_flag_weaponized_cve"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cve-cna"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cve_cna_flag_weaponized_cve" name="武器化 CVE フラグ" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  &quot;open_cve_cna_flag_weaponized_cve&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cveCna.flagWeaponizedCve&quot;,\n'
                 '              project:          &quot;open-cve-cna&quot;,\n'
                 '              subject_vid:      cveId,\n'
                 '              action_class:     &quot;cyber.weaponizedCve&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.weaponizedCve">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-cve-cna.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.weaponizedCve&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: cveId, '
                 'severity: &quot;critical&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2935,
                 '00-contracts/bpmn/com/etzhayyim/open-cve-cna/flagWeaponizedCve.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-weaponized-cve-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ransomware-pay-screen-ransom-sanctions-v1',
                 'did:web:open-ransomware-pay.etzhayyim.com:ops',
                 'open_ransomware_pay_screen_ransom_sanctions',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_ransomware_pay_screen_ransom_sanctions"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-ransomware-pay"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_ransomware_pay_screen_ransom_sanctions" name="ランサム支払 '
                 '制裁照合" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_ransomware_pay_screen_ransom_sanctions&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.ransomwarePay.screenRansomSanctions&quot;,\n'
                 '              project:          &quot;open-ransomware-pay&quot;,\n'
                 '              subject_vid:      payerLei,\n'
                 '              action_class:     &quot;sanctions.ransomPay&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit sanctions.ransomPay">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-ransomware-pay.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sanctions.ransomPay&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: payerLei, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3006,
                 '00-contracts/bpmn/com/etzhayyim/open-ransomware-pay/screenRansomSanctions.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-ransomware-pay.etzhayyim.com:ops',
                 'did:web:open-ransomware-pay.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ransomware-pay-screen-ransom-sanctions-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ofac-sanctions-sdn-match-sdn-entity-v1',
                 'did:web:open-ofac-sanctions-sdn.etzhayyim.com:ops',
                 'open_ofac_sanctions_sdn_match_sdn_entity',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_ofac_sanctions_sdn_match_sdn_entity"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-ofac-sanctions-sdn"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_ofac_sanctions_sdn_match_sdn_entity" name="OFAC SDN 一致" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_ofac_sanctions_sdn_match_sdn_entity&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.ofacSanctionsSdn.matchSdnEntity&quot;,\n'
                 '              project:          &quot;open-ofac-sanctions-sdn&quot;,\n'
                 '              subject_vid:      targetLei,\n'
                 '              action_class:     &quot;sanctions.sdnMatch&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit sanctions.sdnMatch">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-ofac-sanctions-sdn.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sanctions.sdnMatch&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: targetLei, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2988,
                 '00-contracts/bpmn/com/etzhayyim/open-ofac-sanctions-sdn/matchSdnEntity.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-ofac-sanctions-sdn.etzhayyim.com:ops',
                 'did:web:open-ofac-sanctions-sdn.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ofac-sanctions-sdn-match-sdn-entity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-bis-triennial-classify-eccn-control-v1',
                 'did:web:open-bis-triennial.etzhayyim.com:ops',
                 'open_bis_triennial_classify_eccn_control',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_bis_triennial_classify_eccn_control"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-bis-triennial"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_bis_triennial_classify_eccn_control" name="ECCN 分類" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_bis_triennial_classify_eccn_control&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.bisTriennial.classifyEccnControl&quot;,\n'
                 '              project:          &quot;open-bis-triennial&quot;,\n'
                 '              subject_vid:      commodityVid,\n'
                 '              action_class:     &quot;export.eccn&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit export.eccn">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-bis-triennial.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;export.eccn&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: commodityVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2955,
                 '00-contracts/bpmn/com/etzhayyim/open-bis-triennial/classifyEccnControl.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-bis-triennial.etzhayyim.com:ops',
                 'did:web:open-bis-triennial.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-bis-triennial-classify-eccn-control-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mofcom-export-control-flag-prc-export-v1',
                 'did:web:open-mofcom-export-control.etzhayyim.com:ops',
                 'open_mofcom_export_control_flag_prc_export',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_mofcom_export_control_flag_prc_export"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-mofcom-export-control"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_mofcom_export_control_flag_prc_export" name="中商务部 輸出管理" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_mofcom_export_control_flag_prc_export&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.mofcomExportControl.flagPrcExport&quot;,\n'
                 '              project:          &quot;open-mofcom-export-control&quot;,\n'
                 '              subject_vid:      commodityVid,\n'
                 '              action_class:     &quot;export.prcMofcom&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit export.prcMofcom">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-mofcom-export-control.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;export.prcMofcom&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: commodityVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3015,
                 '00-contracts/bpmn/com/etzhayyim/open-mofcom-export-control/flagPrcExport.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-mofcom-export-control.etzhayyim.com:ops',
                 'did:web:open-mofcom-export-control.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mofcom-export-control-flag-prc-export-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-uflpa-enforcement-flag-uflpa-supplier-v1',
                 'did:web:open-uflpa-enforcement.etzhayyim.com:ops',
                 'open_uflpa_enforcement_flag_uflpa_supplier',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_uflpa_enforcement_flag_uflpa_supplier"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-uflpa-enforcement"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_uflpa_enforcement_flag_uflpa_supplier" name="UFLPA '
                 'サプライヤ フラグ" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_uflpa_enforcement_flag_uflpa_supplier&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.uflpaEnforcement.flagUflpaSupplier&quot;,\n'
                 '              project:          &quot;open-uflpa-enforcement&quot;,\n'
                 '              subject_vid:      supplierLei,\n'
                 '              action_class:     &quot;sanctions.uflpa&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit sanctions.uflpa">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-uflpa-enforcement.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sanctions.uflpa&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: supplierLei, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3005,
                 '00-contracts/bpmn/com/etzhayyim/open-uflpa-enforcement/flagUflpaSupplier.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-uflpa-enforcement.etzhayyim.com:ops',
                 'did:web:open-uflpa-enforcement.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-uflpa-enforcement-flag-uflpa-supplier-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-spyware-export-flag-spyware-trade-v1',
                 'did:web:open-spyware-export.etzhayyim.com:ops',
                 'open_spyware_export_flag_spyware_trade',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_spyware_export_flag_spyware_trade"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-spyware-export"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_spyware_export_flag_spyware_trade" name="スパイウェア輸出 フラグ" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_spyware_export_flag_spyware_trade&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.spywareExport.flagSpywareTrade&quot;,\n'
                 '              project:          &quot;open-spyware-export&quot;,\n'
                 '              subject_vid:      vendorLei,\n'
                 '              action_class:     &quot;export.spyware&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit export.spyware">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-spyware-export.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;export.spyware&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: vendorLei, '
                 'severity: &quot;critical&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2984,
                 '00-contracts/bpmn/com/etzhayyim/open-spyware-export/flagSpywareTrade.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-spyware-export.etzhayyim.com:ops',
                 'did:web:open-spyware-export.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-spyware-export-flag-spyware-trade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ais-dark-vessel-flag-ais-manipulation-v1',
                 'did:web:open-ais-dark-vessel.etzhayyim.com:ops',
                 'open_ais_dark_vessel_flag_ais_manipulation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_ais_dark_vessel_flag_ais_manipulation"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-ais-dark-vessel"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_ais_dark_vessel_flag_ais_manipulation" name="AIS 改竄 '
                 'フラグ" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_ais_dark_vessel_flag_ais_manipulation&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.aisDarkVessel.flagAisManipulation&quot;,\n'
                 '              project:          &quot;open-ais-dark-vessel&quot;,\n'
                 '              subject_vid:      vesselVid,\n'
                 '              action_class:     &quot;vessel.aisManip&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit vessel.aisManip">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-ais-dark-vessel.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;vessel.aisManip&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: vesselVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2983,
                 '00-contracts/bpmn/com/etzhayyim/open-ais-dark-vessel/flagAisManipulation.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-ais-dark-vessel.etzhayyim.com:ops',
                 'did:web:open-ais-dark-vessel.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ais-dark-vessel-flag-ais-manipulation-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-shadow-fleet-insurance-flag-pi-club-bypass-v1',
                 'did:web:open-shadow-fleet-insurance.etzhayyim.com:ops',
                 'open_shadow_fleet_insurance_flag_pi_club_bypass',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_shadow_fleet_insurance_flag_pi_club_bypass"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-shadow-fleet-insurance"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_shadow_fleet_insurance_flag_pi_club_bypass" '
                 'name="P&amp;I 迂回 フラグ" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_shadow_fleet_insurance_flag_pi_club_bypass&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.shadowFleetInsurance.flagPiClubBypass&quot;,\n'
                 '              project:          &quot;open-shadow-fleet-insurance&quot;,\n'
                 '              subject_vid:      vesselVid,\n'
                 '              action_class:     &quot;vessel.shadowInsurance&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit vessel.shadowInsurance">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-shadow-fleet-insurance.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;vessel.shadowInsurance&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: vesselVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3048,
                 '00-contracts/bpmn/com/etzhayyim/open-shadow-fleet-insurance/flagPiClubBypass.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-shadow-fleet-insurance.etzhayyim.com:ops',
                 'did:web:open-shadow-fleet-insurance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-shadow-fleet-insurance-flag-pi-club-bypass-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cable-repair-fleet-flag-subsea-cable-tamper-v1',
                 'did:web:open-cable-repair-fleet.etzhayyim.com:ops',
                 'open_cable_repair_fleet_flag_subsea_cable_tamper',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cable_repair_fleet_flag_subsea_cable_tamper"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cable-repair-fleet"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cable_repair_fleet_flag_subsea_cable_tamper" '
                 'name="海底ケーブル妨害 フラグ" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_cable_repair_fleet_flag_subsea_cable_tamper&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cableRepairFleet.flagSubseaCableTamper&quot;,\n'
                 '              project:          &quot;open-cable-repair-fleet&quot;,\n'
                 '              subject_vid:      cableVid,\n'
                 '              action_class:     &quot;subsea.cableTamper&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit subsea.cableTamper">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-cable-repair-fleet.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;subsea.cableTamper&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: cableVid, '
                 'severity: &quot;critical&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3044,
                 '00-contracts/bpmn/com/etzhayyim/open-cable-repair-fleet/flagSubseaCableTamper.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-cable-repair-fleet.etzhayyim.com:ops',
                 'did:web:open-cable-repair-fleet.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cable-repair-fleet-flag-subsea-cable-tamper-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-critical-minerals-flag-supply-concentration-v1',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'open_critical_minerals_flag_supply_concentration',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_critical_minerals_flag_supply_concentration"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-critical-minerals"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_critical_minerals_flag_supply_concentration" name="重要鉱物 '
                 '集中度 フラグ" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_critical_minerals_flag_supply_concentration&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.criticalMinerals.flagSupplyConcentration&quot;,\n'
                 '              project:          &quot;open-critical-minerals&quot;,\n'
                 '              subject_vid:      mineralCode,\n'
                 '              action_class:     &quot;supply.criticalMineral&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit supply.criticalMineral">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-critical-minerals.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;supply.criticalMineral&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: mineralCode, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3051,
                 '00-contracts/bpmn/com/etzhayyim/open-critical-minerals/flagSupplyConcentration.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-critical-minerals-flag-supply-concentration-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-semiconductor-fab-flag-fab-export-control-v1',
                 'did:web:open-semiconductor-fab.etzhayyim.com:ops',
                 'open_semiconductor_fab_flag_fab_export_control',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_semiconductor_fab_flag_fab_export_control"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-semiconductor-fab"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_semiconductor_fab_flag_fab_export_control" name="半導体 '
                 'fab 輸出管理" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_semiconductor_fab_flag_fab_export_control&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.semiconductorFab.flagFabExportControl&quot;,\n'
                 '              project:          &quot;open-semiconductor-fab&quot;,\n'
                 '              subject_vid:      fabLei,\n'
                 '              action_class:     &quot;export.semiconductorFab&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit export.semiconductorFab">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-semiconductor-fab.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;export.semiconductorFab&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: fabLei, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3029,
                 '00-contracts/bpmn/com/etzhayyim/open-semiconductor-fab/flagFabExportControl.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-semiconductor-fab.etzhayyim.com:ops',
                 'did:web:open-semiconductor-fab.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-semiconductor-fab-flag-fab-export-control-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-semi-ip-licensing-flag-dual-use-licensing-v1',
                 'did:web:open-semi-ip-licensing.etzhayyim.com:ops',
                 'open_semi_ip_licensing_flag_dual_use_licensing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_semi_ip_licensing_flag_dual_use_licensing"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-semi-ip-licensing"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_semi_ip_licensing_flag_dual_use_licensing" name="半導体 IP '
                 '軍民両用 ライセンス" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_semi_ip_licensing_flag_dual_use_licensing&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.semiIpLicensing.flagDualUseLicensing&quot;,\n'
                 '              project:          &quot;open-semi-ip-licensing&quot;,\n'
                 '              subject_vid:      licensorLei,\n'
                 '              action_class:     &quot;export.semiIpLicense&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit export.semiIpLicense">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-semi-ip-licensing.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;export.semiIpLicense&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: licensorLei, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3044,
                 '00-contracts/bpmn/com/etzhayyim/open-semi-ip-licensing/flagDualUseLicensing.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-semi-ip-licensing.etzhayyim.com:ops',
                 'did:web:open-semi-ip-licensing.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-semi-ip-licensing-flag-dual-use-licensing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-space-traffic-flag-adversarial-maneuver-v1',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'open_space_traffic_flag_adversarial_maneuver',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_space_traffic_flag_adversarial_maneuver"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-space-traffic"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_space_traffic_flag_adversarial_maneuver" name="敵対的軌道機動 '
                 'フラグ" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_space_traffic_flag_adversarial_maneuver&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.spaceTraffic.flagAdversarialManeuver&quot;,\n'
                 '              project:          &quot;open-space-traffic&quot;,\n'
                 '              subject_vid:      satelliteVid,\n'
                 '              action_class:     &quot;space.adversarialManeuver&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit space.adversarialManeuver">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-space-traffic.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;space.adversarialManeuver&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: satelliteVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3033,
                 '00-contracts/bpmn/com/etzhayyim/open-space-traffic/flagAdversarialManeuver.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-space-traffic-flag-adversarial-maneuver-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-orbital-debris-flag-asat-debris-v1',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'open_orbital_debris_flag_asat_debris',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_orbital_debris_flag_asat_debris"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-orbital-debris"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_orbital_debris_flag_asat_debris" name="ASAT デブリ フラグ" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_orbital_debris_flag_asat_debris&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.orbitalDebris.flagAsatDebris&quot;,\n'
                 '              project:          &quot;open-orbital-debris&quot;,\n'
                 '              subject_vid:      eventVid,\n'
                 '              action_class:     &quot;space.asatDebris&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit space.asatDebris">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-orbital-debris.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;space.asatDebris&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: eventVid, '
                 'severity: &quot;critical&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2970,
                 '00-contracts/bpmn/com/etzhayyim/open-orbital-debris/flagAsatDebris.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-orbital-debris-flag-asat-debris-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-social-media-influence-op-flag-state-influence-op-v1',
                 'did:web:open-social-media-influence-op.etzhayyim.com:ops',
                 'open_social_media_influence_op_flag_state_influence_op',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_social_media_influence_op_flag_state_influence_op"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-social-media-influence-op"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_social_media_influence_op_flag_state_influence_op" '
                 'name="国家工作 情報戦 フラグ" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_social_media_influence_op_flag_state_influence_op&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.socialMediaInfluenceOp.flagStateInfluenceOp&quot;,\n'
                 '              project:          &quot;open-social-media-influence-op&quot;,\n'
                 '              subject_vid:      campaignVid,\n'
                 '              action_class:     &quot;info.stateInfluenceOp&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit info.stateInfluenceOp">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-social-media-influence-op.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;info.stateInfluenceOp&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: campaignVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3093,
                 '00-contracts/bpmn/com/etzhayyim/open-social-media-influence-op/flagStateInfluenceOp.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-social-media-influence-op.etzhayyim.com:ops',
                 'did:web:open-social-media-influence-op.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-social-media-influence-op-flag-state-influence-op-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-deepfake-takedown-flag-state-sponsored-deepfake-v1',
                 'did:web:open-deepfake-takedown.etzhayyim.com:ops',
                 'open_deepfake_takedown_flag_state_sponsored_deepfake',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_deepfake_takedown_flag_state_sponsored_deepfake"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-deepfake-takedown"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_deepfake_takedown_flag_state_sponsored_deepfake" '
                 'name="国家関与 deepfake フラグ" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_deepfake_takedown_flag_state_sponsored_deepfake&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.deepfakeTakedown.flagStateSponsoredDeepfake&quot;,\n'
                 '              project:          &quot;open-deepfake-takedown&quot;,\n'
                 '              subject_vid:      contentVid,\n'
                 '              action_class:     &quot;info.stateDeepfake&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit info.stateDeepfake">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-deepfake-takedown.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;info.stateDeepfake&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: contentVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3051,
                 '00-contracts/bpmn/com/etzhayyim/open-deepfake-takedown/flagStateSponsoredDeepfake.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-deepfake-takedown.etzhayyim.com:ops',
                 'did:web:open-deepfake-takedown.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-deepfake-takedown-flag-state-sponsored-deepfake-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-jpn-gov-register-atla-contract-v1',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'open_jpn_gov_register_atla_contract',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_jpn_gov_register_atla_contract"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-jpn-gov"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_jpn_gov_register_atla_contract" name="防衛装備庁 契約登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  '
                 '&quot;open_jpn_gov_register_atla_contract&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.openJpnGov.registerAtlaContract&quot;,\n'
                 '              project:          &quot;open-jpn-gov&quot;,\n'
                 '              subject_vid:      contractId,\n'
                 '              action_class:     &quot;boeiSho.atlaContract&quot;,\n'
                 '              severity:         &quot;info&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit boeiSho.atlaContract">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-jpn-gov.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;boeiSho.atlaContract&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: contractId, '
                 'severity: &quot;info&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2961,
                 '00-contracts/bpmn/com/etzhayyim/open-jpn-gov/registerAtlaContract.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-jpn-gov-register-atla-contract-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-jpn-gov-notify-jsdf-jcg-alert-v1',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'open_jpn_gov_notify_jsdf_jcg_alert',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_jpn_gov_notify_jsdf_jcg_alert"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-jpn-gov"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_jpn_gov_notify_jsdf_jcg_alert" name="自衛隊・海保 共有アラート" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="defence event 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_defence_event&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              owner_did:        callerDid,\n'
                 '              bpmn_process_id:  &quot;open_jpn_gov_notify_jsdf_jcg_alert&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.openJpnGov.notifyJsdfJcgAlert&quot;,\n'
                 '              project:          &quot;open-jpn-gov&quot;,\n'
                 '              subject_vid:      alertVid,\n'
                 '              action_class:     &quot;boeiSho.jsdfJcgAlert&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-defence&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit boeiSho.jsdfJcgAlert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-jpn-gov.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;boeiSho.jsdfJcgAlert&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: alertVid, '
                 'severity: &quot;high&quot;}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2961,
                 '00-contracts/bpmn/com/etzhayyim/open-jpn-gov/notifyJsdfJcgAlert.bpmn',
                 '2026-04-25T11:00:00Z',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-jpn-gov-notify-jsdf-jcg-alert-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-threat-assessThreatActor-v1',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cyberThreat.assessThreatActor',
                 'open_cyber_threat_assess_threat_actor',
                 20000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-threat-assessThreatActor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-vuln-linkExploitToActor-v1',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cyberVuln.linkExploitToActor',
                 'open_cyber_vuln_link_exploit_to_actor',
                 20000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-vuln-linkExploitToActor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-zero-day-broker-flagZeroDayTrade-v1',
                 'did:web:open-zero-day-broker.etzhayyim.com:ops',
                 'com.etzhayyim.apps.zeroDayBroker.flagZeroDayTrade',
                 'open_zero_day_broker_flag_zero_day_trade',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-zero-day-broker.etzhayyim.com:ops',
                 'did:web:open-zero-day-broker.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-zero-day-broker-flagZeroDayTrade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cve-cna-flagWeaponizedCve-v1',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cveCna.flagWeaponizedCve',
                 'open_cve_cna_flag_weaponized_cve',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cve-cna-flagWeaponizedCve-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ransomware-pay-screenRansomSanctions-v1',
                 'did:web:open-ransomware-pay.etzhayyim.com:ops',
                 'com.etzhayyim.apps.ransomwarePay.screenRansomSanctions',
                 'open_ransomware_pay_screen_ransom_sanctions',
                 20000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-ransomware-pay.etzhayyim.com:ops',
                 'did:web:open-ransomware-pay.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ransomware-pay-screenRansomSanctions-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ofac-sanctions-sdn-matchSdnEntity-v1',
                 'did:web:open-ofac-sanctions-sdn.etzhayyim.com:ops',
                 'com.etzhayyim.apps.ofacSanctionsSdn.matchSdnEntity',
                 'open_ofac_sanctions_sdn_match_sdn_entity',
                 20000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-ofac-sanctions-sdn.etzhayyim.com:ops',
                 'did:web:open-ofac-sanctions-sdn.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ofac-sanctions-sdn-matchSdnEntity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-bis-triennial-classifyEccnControl-v1',
                 'did:web:open-bis-triennial.etzhayyim.com:ops',
                 'com.etzhayyim.apps.bisTriennial.classifyEccnControl',
                 'open_bis_triennial_classify_eccn_control',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-bis-triennial.etzhayyim.com:ops',
                 'did:web:open-bis-triennial.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-bis-triennial-classifyEccnControl-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mofcom-export-control-flagPrcExport-v1',
                 'did:web:open-mofcom-export-control.etzhayyim.com:ops',
                 'com.etzhayyim.apps.mofcomExportControl.flagPrcExport',
                 'open_mofcom_export_control_flag_prc_export',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-mofcom-export-control.etzhayyim.com:ops',
                 'did:web:open-mofcom-export-control.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mofcom-export-control-flagPrcExport-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-uflpa-enforcement-flagUflpaSupplier-v1',
                 'did:web:open-uflpa-enforcement.etzhayyim.com:ops',
                 'com.etzhayyim.apps.uflpaEnforcement.flagUflpaSupplier',
                 'open_uflpa_enforcement_flag_uflpa_supplier',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-uflpa-enforcement.etzhayyim.com:ops',
                 'did:web:open-uflpa-enforcement.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-uflpa-enforcement-flagUflpaSupplier-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-spyware-export-flagSpywareTrade-v1',
                 'did:web:open-spyware-export.etzhayyim.com:ops',
                 'com.etzhayyim.apps.spywareExport.flagSpywareTrade',
                 'open_spyware_export_flag_spyware_trade',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-spyware-export.etzhayyim.com:ops',
                 'did:web:open-spyware-export.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-spyware-export-flagSpywareTrade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ais-dark-vessel-flagAisManipulation-v1',
                 'did:web:open-ais-dark-vessel.etzhayyim.com:ops',
                 'com.etzhayyim.apps.aisDarkVessel.flagAisManipulation',
                 'open_ais_dark_vessel_flag_ais_manipulation',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-ais-dark-vessel.etzhayyim.com:ops',
                 'did:web:open-ais-dark-vessel.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ais-dark-vessel-flagAisManipulation-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-shadow-fleet-insurance-flagPiClubBypass-v1',
                 'did:web:open-shadow-fleet-insurance.etzhayyim.com:ops',
                 'com.etzhayyim.apps.shadowFleetInsurance.flagPiClubBypass',
                 'open_shadow_fleet_insurance_flag_pi_club_bypass',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-shadow-fleet-insurance.etzhayyim.com:ops',
                 'did:web:open-shadow-fleet-insurance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-shadow-fleet-insurance-flagPiClubBypass-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cable-repair-fleet-flagSubseaCableTamper-v1',
                 'did:web:open-cable-repair-fleet.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cableRepairFleet.flagSubseaCableTamper',
                 'open_cable_repair_fleet_flag_subsea_cable_tamper',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-cable-repair-fleet.etzhayyim.com:ops',
                 'did:web:open-cable-repair-fleet.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cable-repair-fleet-flagSubseaCableTamper-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-critical-minerals-flagSupplyConcentration-v1',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'com.etzhayyim.apps.criticalMinerals.flagSupplyConcentration',
                 'open_critical_minerals_flag_supply_concentration',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-critical-minerals-flagSupplyConcentration-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-semiconductor-fab-flagFabExportControl-v1',
                 'did:web:open-semiconductor-fab.etzhayyim.com:ops',
                 'com.etzhayyim.apps.semiconductorFab.flagFabExportControl',
                 'open_semiconductor_fab_flag_fab_export_control',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-semiconductor-fab.etzhayyim.com:ops',
                 'did:web:open-semiconductor-fab.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-semiconductor-fab-flagFabExportControl-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-semi-ip-licensing-flagDualUseLicensing-v1',
                 'did:web:open-semi-ip-licensing.etzhayyim.com:ops',
                 'com.etzhayyim.apps.semiIpLicensing.flagDualUseLicensing',
                 'open_semi_ip_licensing_flag_dual_use_licensing',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-semi-ip-licensing.etzhayyim.com:ops',
                 'did:web:open-semi-ip-licensing.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-semi-ip-licensing-flagDualUseLicensing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-space-traffic-flagAdversarialManeuver-v1',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'com.etzhayyim.apps.spaceTraffic.flagAdversarialManeuver',
                 'open_space_traffic_flag_adversarial_maneuver',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-space-traffic-flagAdversarialManeuver-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-orbital-debris-flagAsatDebris-v1',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'com.etzhayyim.apps.orbitalDebris.flagAsatDebris',
                 'open_orbital_debris_flag_asat_debris',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-orbital-debris-flagAsatDebris-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-social-media-influence-op-flagStateInfluenceOp-v1',
                 'did:web:open-social-media-influence-op.etzhayyim.com:ops',
                 'com.etzhayyim.apps.socialMediaInfluenceOp.flagStateInfluenceOp',
                 'open_social_media_influence_op_flag_state_influence_op',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-social-media-influence-op.etzhayyim.com:ops',
                 'did:web:open-social-media-influence-op.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-social-media-influence-op-flagStateInfluenceOp-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-deepfake-takedown-flagStateSponsoredDeepfake-v1',
                 'did:web:open-deepfake-takedown.etzhayyim.com:ops',
                 'com.etzhayyim.apps.deepfakeTakedown.flagStateSponsoredDeepfake',
                 'open_deepfake_takedown_flag_state_sponsored_deepfake',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-deepfake-takedown.etzhayyim.com:ops',
                 'did:web:open-deepfake-takedown.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-deepfake-takedown-flagStateSponsoredDeepfake-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-jpn-gov-registerAtlaContract-v1',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'com.etzhayyim.apps.openJpnGov.registerAtlaContract',
                 'open_jpn_gov_register_atla_contract',
                 20000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-jpn-gov-registerAtlaContract-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-jpn-gov-notifyJsdfJcgAlert-v1',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'com.etzhayyim.apps.openJpnGov.notifyJsdfJcgAlert',
                 'open_jpn_gov_notify_jsdf_jcg_alert',
                 15000,
                 '2026-04-25T11:00:00Z',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w2',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-jpn-gov-notifyJsdfJcgAlert-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-threat-assessThreatActor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-vuln-linkExploitToActor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-zero-day-broker-flagZeroDayTrade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cve-cna-flagWeaponizedCve-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ransomware-pay-screenRansomSanctions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ofac-sanctions-sdn-matchSdnEntity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-bis-triennial-classifyEccnControl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mofcom-export-control-flagPrcExport-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-uflpa-enforcement-flagUflpaSupplier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-spyware-export-flagSpywareTrade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-ais-dark-vessel-flagAisManipulation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-shadow-fleet-insurance-flagPiClubBypass-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cable-repair-fleet-flagSubseaCableTamper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-critical-minerals-flagSupplyConcentration-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-semiconductor-fab-flagFabExportControl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-semi-ip-licensing-flagDualUseLicensing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-space-traffic-flagAdversarialManeuver-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-orbital-debris-flagAsatDebris-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-social-media-influence-op-flagStateInfluenceOp-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-deepfake-takedown-flagStateSponsoredDeepfake-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-jpn-gov-registerAtlaContract-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-jpn-gov-notifyJsdfJcgAlert-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-threat-assess-threat-actor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-link-exploit-to-actor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-zero-day-broker-flag-zero-day-trade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-weaponized-cve-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ransomware-pay-screen-ransom-sanctions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ofac-sanctions-sdn-match-sdn-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-bis-triennial-classify-eccn-control-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mofcom-export-control-flag-prc-export-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-uflpa-enforcement-flag-uflpa-supplier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-spyware-export-flag-spyware-trade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ais-dark-vessel-flag-ais-manipulation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-shadow-fleet-insurance-flag-pi-club-bypass-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cable-repair-fleet-flag-subsea-cable-tamper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-critical-minerals-flag-supply-concentration-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-semiconductor-fab-flag-fab-export-control-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-semi-ip-licensing-flag-dual-use-licensing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-space-traffic-flag-adversarial-maneuver-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-orbital-debris-flag-asat-debris-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-social-media-influence-op-flag-state-influence-op-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-deepfake-takedown-flag-state-sponsored-deepfake-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-jpn-gov-register-atla-contract-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-jpn-gov-notify-jsdf-jcg-alert-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
