"""Captured from Kysely migration 20260425140000_seed_open_defence_wave4_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425140000_seed_open_defence_wave4_bpmn_actors"
down_revision = 'r_20260425130000_vertex_gameka_title_avatar_data_uri'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-soc-escalate-state-apt-v1',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'open_cyber_soc_escalate_state_apt',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cyber_soc_escalate_state_apt"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cyber-soc"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_soc_escalate_state_apt" name="国家関与 APT エスカレーション" '
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
                 '              bpmn_process_id:  &quot;open_cyber_soc_escalate_state_apt&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cyberSoc.escalateStateApt&quot;,\n'
                 '              project:          &quot;open-cyber-soc&quot;,\n'
                 '              subject_vid:      aptId,\n'
                 '              action_class:     &quot;cyber.stateApt&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        originCountry,\n'
                 '              confidence:        confidence,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.stateApt">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-cyber-soc.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.stateApt&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: aptId, '
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
                 3046,
                 '00-contracts/bpmn/com/etzhayyim/open-cyber-soc/escalateStateApt.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-soc-escalate-state-apt-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-incident-link-incident-to-treaty-v1',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'open_cyber_incident_link_incident_to_treaty',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cyber_incident_link_incident_to_treaty"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cyber-incident"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_incident_link_incident_to_treaty" name="サイバー事案 → '
                 '条約紐付" isExecutable="true">\n'
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
                 '&quot;open_cyber_incident_link_incident_to_treaty&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cyberIncident.linkIncidentToTreaty&quot;,\n'
                 '              project:          &quot;open-cyber-incident&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;cyber.treatyLink&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              treaty_code:        treatyCode,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.treatyLink">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-cyber-incident.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.treatyLink&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 3052,
                 '00-contracts/bpmn/com/etzhayyim/open-cyber-incident/linkIncidentToTreaty.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-incident-link-incident-to-treaty-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mass-autonomous-ship-flag-weaponized-mass-v1',
                 'did:web:open-mass-autonomous-ship.etzhayyim.com:ops',
                 'open_mass_autonomous_ship_flag_weaponized_mass',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_mass_autonomous_ship_flag_weaponized_mass"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-mass-autonomous-ship"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_mass_autonomous_ship_flag_weaponized_mass" name="武装 '
                 'MASS 検出" isExecutable="true">\n'
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
                 '&quot;open_mass_autonomous_ship_flag_weaponized_mass&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.massAutonomousShip.flagWeaponizedMass&quot;,\n'
                 '              project:          &quot;open-mass-autonomous-ship&quot;,\n'
                 '              subject_vid:      vesselVid,\n'
                 '              action_class:     &quot;mass.weaponized&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_imo:        imo,\n'
                 '              subject_lei:        operatorLei,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit mass.weaponized">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-mass-autonomous-ship.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;mass.weaponized&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: vesselVid, '
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
                 3106,
                 '00-contracts/bpmn/com/etzhayyim/open-mass-autonomous-ship/flagWeaponizedMass.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-mass-autonomous-ship.etzhayyim.com:ops',
                 'did:web:open-mass-autonomous-ship.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mass-autonomous-ship-flag-weaponized-mass-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fusion-energy-flag-icf-weapons-link-v1',
                 'did:web:open-fusion-energy.etzhayyim.com:ops',
                 'open_fusion_energy_flag_icf_weapons_link',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_fusion_energy_flag_icf_weapons_link"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-fusion-energy"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_fusion_energy_flag_icf_weapons_link" name="ICF 核兵器懸念" '
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
                 '&quot;open_fusion_energy_flag_icf_weapons_link&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.fusionEnergy.flagIcfWeaponsLink&quot;,\n'
                 '              project:          &quot;open-fusion-energy&quot;,\n'
                 '              subject_vid:      facilityVid,\n'
                 '              action_class:     &quot;nuclear.icfWeaponsLink&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
                 '              subject_lei:        programLei,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit nuclear.icfWeaponsLink">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-fusion-energy.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;nuclear.icfWeaponsLink&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: facilityVid, '
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
                 3094,
                 '00-contracts/bpmn/com/etzhayyim/open-fusion-energy/flagIcfWeaponsLink.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-fusion-energy.etzhayyim.com:ops',
                 'did:web:open-fusion-energy.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fusion-energy-flag-icf-weapons-link-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-pandemic-treaty-flag-bwc-dual-use-v1',
                 'did:web:open-pandemic-treaty.etzhayyim.com:ops',
                 'open_pandemic_treaty_flag_bwc_dual_use',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_pandemic_treaty_flag_bwc_dual_use"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-pandemic-treaty"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_pandemic_treaty_flag_bwc_dual_use" name="BWC 軍民両用 フラグ" '
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
                 '&quot;open_pandemic_treaty_flag_bwc_dual_use&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.pandemicTreaty.flagBwcDualUse&quot;,\n'
                 '              project:          &quot;open-pandemic-treaty&quot;,\n'
                 '              subject_vid:      labVid,\n'
                 '              action_class:     &quot;treaty.bwcDualUse&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
                 '              treaty_code:        &quot;BWC&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit treaty.bwcDualUse">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-pandemic-treaty.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;treaty.bwcDualUse&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: labVid, '
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
                 3071,
                 '00-contracts/bpmn/com/etzhayyim/open-pandemic-treaty/flagBwcDualUse.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-pandemic-treaty.etzhayyim.com:ops',
                 'did:web:open-pandemic-treaty.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-pandemic-treaty-flag-bwc-dual-use-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyclone-prepo-flag-military-hadr-v1',
                 'did:web:open-cyclone-prepo.etzhayyim.com:ops',
                 'open_cyclone_prepo_flag_military_hadr',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cyclone_prepo_flag_military_hadr"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cyclone-prepo"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyclone_prepo_flag_military_hadr" name="災害派遣 (HA/DR) '
                 '軍事プレゼンス" isExecutable="true">\n'
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
                 '&quot;open_cyclone_prepo_flag_military_hadr&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cyclonePrepo.flagMilitaryHadr&quot;,\n'
                 '              project:          &quot;open-cyclone-prepo&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;hadr.militaryPresence&quot;,\n'
                 '              severity:         &quot;info&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
                 '              subject_lei:        unitLei,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit hadr.militaryPresence">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-cyclone-prepo.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;hadr.militaryPresence&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 3092,
                 '00-contracts/bpmn/com/etzhayyim/open-cyclone-prepo/flagMilitaryHadr.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-cyclone-prepo.etzhayyim.com:ops',
                 'did:web:open-cyclone-prepo.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyclone-prepo-flag-military-hadr-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-naval-flag-freedom-of-navigation-v1',
                 'did:web:open-redsea-naval.etzhayyim.com:ops',
                 'open_redsea_naval_flag_freedom_of_navigation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_redsea_naval_flag_freedom_of_navigation"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-redsea-naval"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_redsea_naval_flag_freedom_of_navigation" name="紅海 航行自由" '
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
                 '&quot;open_redsea_naval_flag_freedom_of_navigation&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.redseaNaval.flagFreedomOfNavigation&quot;,\n'
                 '              project:          &quot;open-redsea-naval&quot;,\n'
                 '              subject_vid:      operationId,\n'
                 '              action_class:     &quot;maritime.fonops&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit maritime.fonops">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-redsea-naval.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;maritime.fonops&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: operationId, '
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
                 3032,
                 '00-contracts/bpmn/com/etzhayyim/open-redsea-naval/flagFreedomOfNavigation.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-redsea-naval.etzhayyim.com:ops',
                 'did:web:open-redsea-naval.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-naval-flag-freedom-of-navigation-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-incident-flag-ship-missile-strike-v1',
                 'did:web:open-redsea-incident.etzhayyim.com:ops',
                 'open_redsea_incident_flag_ship_missile_strike',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_redsea_incident_flag_ship_missile_strike"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-redsea-incident"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_redsea_incident_flag_ship_missile_strike" name="商船 '
                 'ミサイル攻撃" isExecutable="true">\n'
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
                 '&quot;open_redsea_incident_flag_ship_missile_strike&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.redseaIncident.flagShipMissileStrike&quot;,\n'
                 '              project:          &quot;open-redsea-incident&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;maritime.missileStrike&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_imo:        imo,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit maritime.missileStrike">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-redsea-incident.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;maritime.missileStrike&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 3072,
                 '00-contracts/bpmn/com/etzhayyim/open-redsea-incident/flagShipMissileStrike.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-redsea-incident.etzhayyim.com:ops',
                 'did:web:open-redsea-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-incident-flag-ship-missile-strike-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-rerouting-flag-supply-chain-impact-v1',
                 'did:web:open-redsea-rerouting.etzhayyim.com:ops',
                 'open_redsea_rerouting_flag_supply_chain_impact',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_redsea_rerouting_flag_supply_chain_impact"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-redsea-rerouting"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_redsea_rerouting_flag_supply_chain_impact" name="喜望峰迂回 '
                 'sup-chain 影響" isExecutable="true">\n'
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
                 '&quot;open_redsea_rerouting_flag_supply_chain_impact&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.redseaRerouting.flagSupplyChainImpact&quot;,\n'
                 '              project:          &quot;open-redsea-rerouting&quot;,\n'
                 '              subject_vid:      cargoVid,\n'
                 '              action_class:     &quot;supply.redseaReroute&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_lei:        operatorLei,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit supply.redseaReroute">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-redsea-rerouting.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;supply.redseaReroute&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: cargoVid, '
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
                 3074,
                 '00-contracts/bpmn/com/etzhayyim/open-redsea-rerouting/flagSupplyChainImpact.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-redsea-rerouting.etzhayyim.com:ops',
                 'did:web:open-redsea-rerouting.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-rerouting-flag-supply-chain-impact-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-hormuz-darkfleet-flag-iran-spoofing-v1',
                 'did:web:open-hormuz-darkfleet.etzhayyim.com:ops',
                 'open_hormuz_darkfleet_flag_iran_spoofing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_hormuz_darkfleet_flag_iran_spoofing"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-hormuz-darkfleet"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_hormuz_darkfleet_flag_iran_spoofing" name="ホルムズ IRGC '
                 'AIS spoof" isExecutable="true">\n'
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
                 '&quot;open_hormuz_darkfleet_flag_iran_spoofing&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.hormuzDarkfleet.flagIranSpoofing&quot;,\n'
                 '              project:          &quot;open-hormuz-darkfleet&quot;,\n'
                 '              subject_vid:      vesselVid,\n'
                 '              action_class:     &quot;maritime.iranSpoof&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_imo:        imo,\n'
                 '              subject_country:        &quot;IR&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit maritime.iranSpoof">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-hormuz-darkfleet.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;maritime.iranSpoof&quot;" '
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
                 3088,
                 '00-contracts/bpmn/com/etzhayyim/open-hormuz-darkfleet/flagIranSpoofing.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-hormuz-darkfleet.etzhayyim.com:ops',
                 'did:web:open-hormuz-darkfleet.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-hormuz-darkfleet-flag-iran-spoofing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-hormuz-incident-flag-tanker-hijack-v1',
                 'did:web:open-hormuz-incident.etzhayyim.com:ops',
                 'open_hormuz_incident_flag_tanker_hijack',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_hormuz_incident_flag_tanker_hijack"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-hormuz-incident"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_hormuz_incident_flag_tanker_hijack" name="タンカー拿捕" '
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
                 '&quot;open_hormuz_incident_flag_tanker_hijack&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.hormuzIncident.flagTankerHijack&quot;,\n'
                 '              project:          &quot;open-hormuz-incident&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;maritime.tankerHijack&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_imo:        imo,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit maritime.tankerHijack">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-hormuz-incident.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;maritime.tankerHijack&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 3039,
                 '00-contracts/bpmn/com/etzhayyim/open-hormuz-incident/flagTankerHijack.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-hormuz-incident.etzhayyim.com:ops',
                 'did:web:open-hormuz-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-hormuz-incident-flag-tanker-hijack-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-malacca-incident-flag-piracy-escort-v1',
                 'did:web:open-malacca-incident.etzhayyim.com:ops',
                 'open_malacca_incident_flag_piracy_escort',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_malacca_incident_flag_piracy_escort"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-malacca-incident"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_malacca_incident_flag_piracy_escort" name="マラッカ 海賊・護衛" '
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
                 '&quot;open_malacca_incident_flag_piracy_escort&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.malaccaIncident.flagPiracyEscort&quot;,\n'
                 '              project:          &quot;open-malacca-incident&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;maritime.piracyEscort&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_imo:        imo,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit maritime.piracyEscort">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-malacca-incident.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;maritime.piracyEscort&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 '00-contracts/bpmn/com/etzhayyim/open-malacca-incident/flagPiracyEscort.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-malacca-incident.etzhayyim.com:ops',
                 'did:web:open-malacca-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-malacca-incident-flag-piracy-escort-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cell-broadcast-alert-notify-jalert-v1',
                 'did:web:open-cell-broadcast-alert.etzhayyim.com:ops',
                 'open_cell_broadcast_alert_notify_jalert',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_cell_broadcast_alert_notify_jalert"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-cell-broadcast-alert"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cell_broadcast_alert_notify_jalert" name="J-アラート '
                 '(北朝鮮ミサイル)" isExecutable="true">\n'
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
                 '&quot;open_cell_broadcast_alert_notify_jalert&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cellBroadcastAlert.notifyJalert&quot;,\n'
                 '              project:          &quot;open-cell-broadcast-alert&quot;,\n'
                 '              subject_vid:      alertId,\n'
                 '              action_class:     &quot;alert.jalert&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        &quot;KP&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit alert.jalert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-cell-broadcast-alert.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;alert.jalert&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: alertId, '
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
                 3054,
                 '00-contracts/bpmn/com/etzhayyim/open-cell-broadcast-alert/notifyJalert.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-cell-broadcast-alert.etzhayyim.com:ops',
                 'did:web:open-cell-broadcast-alert.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cell-broadcast-alert-notify-jalert-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-internet-shutdown-flag-wartime-shutdown-v1',
                 'did:web:open-internet-shutdown.etzhayyim.com:ops',
                 'open_internet_shutdown_flag_wartime_shutdown',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_internet_shutdown_flag_wartime_shutdown"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-internet-shutdown"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_internet_shutdown_flag_wartime_shutdown" name="戦時通信遮断 '
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
                 '&quot;open_internet_shutdown_flag_wartime_shutdown&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.internetShutdown.flagWartimeShutdown&quot;,\n'
                 '              project:          &quot;open-internet-shutdown&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;info.wartimeShutdown&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit info.wartimeShutdown">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-internet-shutdown.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;info.wartimeShutdown&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 3072,
                 '00-contracts/bpmn/com/etzhayyim/open-internet-shutdown/flagWartimeShutdown.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-internet-shutdown.etzhayyim.com:ops',
                 'did:web:open-internet-shutdown.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-internet-shutdown-flag-wartime-shutdown-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-encryption-debate-flag-backdoor-mandate-v1',
                 'did:web:open-encryption-debate.etzhayyim.com:ops',
                 'open_encryption_debate_flag_backdoor_mandate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_encryption_debate_flag_backdoor_mandate"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-encryption-debate"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_encryption_debate_flag_backdoor_mandate" name="crypto '
                 'backdoor 義務化" isExecutable="true">\n'
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
                 '&quot;open_encryption_debate_flag_backdoor_mandate&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.encryptionDebate.flagBackdoorMandate&quot;,\n'
                 '              project:          &quot;open-encryption-debate&quot;,\n'
                 '              subject_vid:      policyId,\n'
                 '              action_class:     &quot;cyber.backdoorMandate&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.backdoorMandate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-encryption-debate.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.backdoorMandate&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: policyId, '
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
                 3066,
                 '00-contracts/bpmn/com/etzhayyim/open-encryption-debate/flagBackdoorMandate.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-encryption-debate.etzhayyim.com:ops',
                 'did:web:open-encryption-debate.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-encryption-debate-flag-backdoor-mandate-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mining-operation-flag-conflict-mineral-v1',
                 'did:web:open-mining-operation.etzhayyim.com:ops',
                 'open_mining_operation_flag_conflict_mineral',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_mining_operation_flag_conflict_mineral"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-mining-operation"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_mining_operation_flag_conflict_mineral" name="紛争鉱物 '
                 '(3TG)" isExecutable="true">\n'
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
                 '&quot;open_mining_operation_flag_conflict_mineral&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.miningOperation.flagConflictMineral&quot;,\n'
                 '              project:          &quot;open-mining-operation&quot;,\n'
                 '              subject_vid:      mineralCode,\n'
                 '              action_class:     &quot;supply.conflictMineral&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_lei:        supplierLei,\n'
                 '              subject_country:        country,\n'
                 '              commodity_code:        mineralCode,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit supply.conflictMineral">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-mining-operation.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;supply.conflictMineral&quot;" '
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
                 3158,
                 '00-contracts/bpmn/com/etzhayyim/open-mining-operation/flagConflictMineral.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-mining-operation.etzhayyim.com:ops',
                 'did:web:open-mining-operation.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mining-operation-flag-conflict-mineral-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-deep-sea-mining-flag-strategic-seabed-claim-v1',
                 'did:web:open-deep-sea-mining.etzhayyim.com:ops',
                 'open_deep_sea_mining_flag_strategic_seabed_claim',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_deep_sea_mining_flag_strategic_seabed_claim"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-deep-sea-mining"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_deep_sea_mining_flag_strategic_seabed_claim" name="海底鉱物 '
                 '戦略主張" isExecutable="true">\n'
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
                 '&quot;open_deep_sea_mining_flag_strategic_seabed_claim&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.deepSeaMining.flagStrategicSeabedClaim&quot;,\n'
                 '              project:          &quot;open-deep-sea-mining&quot;,\n'
                 '              subject_vid:      claimId,\n'
                 '              action_class:     &quot;maritime.seabedClaim&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit maritime.seabedClaim">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-deep-sea-mining.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;maritime.seabedClaim&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: claimId, '
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
                 3069,
                 '00-contracts/bpmn/com/etzhayyim/open-deep-sea-mining/flagStrategicSeabedClaim.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-deep-sea-mining.etzhayyim.com:ops',
                 'did:web:open-deep-sea-mining.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-deep-sea-mining-flag-strategic-seabed-claim-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-arctic-nsr-flag-arctic-militarization-v1',
                 'did:web:open-arctic-nsr.etzhayyim.com:ops',
                 'open_arctic_nsr_flag_arctic_militarization',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_arctic_nsr_flag_arctic_militarization"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-arctic-nsr"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_arctic_nsr_flag_arctic_militarization" name="NSR 軍事化" '
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
                 '&quot;open_arctic_nsr_flag_arctic_militarization&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.arcticNsr.flagArcticMilitarization&quot;,\n'
                 '              project:          &quot;open-arctic-nsr&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;maritime.arcticMilitary&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit maritime.arcticMilitary">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-arctic-nsr.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;maritime.arcticMilitary&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 3037,
                 '00-contracts/bpmn/com/etzhayyim/open-arctic-nsr/flagArcticMilitarization.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-arctic-nsr.etzhayyim.com:ops',
                 'did:web:open-arctic-nsr.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-arctic-nsr-flag-arctic-militarization-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-antarctic-treaty-flag-antarctic-military-v1',
                 'did:web:open-antarctic-treaty.etzhayyim.com:ops',
                 'open_antarctic_treaty_flag_antarctic_military',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_antarctic_treaty_flag_antarctic_military"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-antarctic-treaty"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_antarctic_treaty_flag_antarctic_military" name="南極条約違反" '
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
                 '&quot;open_antarctic_treaty_flag_antarctic_military&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.antarcticTreaty.flagAntarcticMilitary&quot;,\n'
                 '              project:          &quot;open-antarctic-treaty&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;treaty.antarcticBreach&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
                 '              treaty_code:        &quot;ANTARCTIC&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit treaty.antarcticBreach">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-antarctic-treaty.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;treaty.antarcticBreach&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 3134,
                 '00-contracts/bpmn/com/etzhayyim/open-antarctic-treaty/flagAntarcticMilitary.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-antarctic-treaty.etzhayyim.com:ops',
                 'did:web:open-antarctic-treaty.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-antarctic-treaty-flag-antarctic-military-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-bbnj-highseas-flag-highseas-military-v1',
                 'did:web:open-bbnj-highseas.etzhayyim.com:ops',
                 'open_bbnj_highseas_flag_highseas_military',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_bbnj_highseas_flag_highseas_military"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-bbnj-highseas"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_bbnj_highseas_flag_highseas_military" name="公海 軍事活動 '
                 '(BBNJ)" isExecutable="true">\n'
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
                 '&quot;open_bbnj_highseas_flag_highseas_military&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.bbnjHighseas.flagHighseasMilitary&quot;,\n'
                 '              project:          &quot;open-bbnj-highseas&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;maritime.highseasMilitary&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
                 '              treaty_code:        &quot;BBNJ&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit maritime.highseasMilitary">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-bbnj-highseas.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;maritime.highseasMilitary&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: incidentVid, '
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
                 3113,
                 '00-contracts/bpmn/com/etzhayyim/open-bbnj-highseas/flagHighseasMilitary.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-bbnj-highseas.etzhayyim.com:ops',
                 'did:web:open-bbnj-highseas.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-bbnj-highseas-flag-highseas-military-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-orbital-debris-track-kessler-cascade-v1',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'open_orbital_debris_track_kessler_cascade',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_orbital_debris_track_kessler_cascade"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-orbital-debris"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_orbital_debris_track_kessler_cascade" name="Kessler '
                 'カスケード追跡" isExecutable="true">\n'
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
                 '&quot;open_orbital_debris_track_kessler_cascade&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.orbitalDebris.trackKesslerCascade&quot;,\n'
                 '              project:          &quot;open-orbital-debris&quot;,\n'
                 '              subject_vid:      eventVid,\n'
                 '              action_class:     &quot;space.kesslerCascade&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit space.kesslerCascade">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-orbital-debris.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;space.kesslerCascade&quot;" '
                 'target="action"/>\n'
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
                 3007,
                 '00-contracts/bpmn/com/etzhayyim/open-orbital-debris/trackKesslerCascade.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-orbital-debris-track-kessler-cascade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-space-traffic-track-hostile-rpo-v1',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'open_space_traffic_track_hostile_rpo',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_space_traffic_track_hostile_rpo"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-space-traffic"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_space_traffic_track_hostile_rpo" name="敵対 RPO 追跡" '
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
                 '&quot;open_space_traffic_track_hostile_rpo&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.spaceTraffic.trackHostileRpo&quot;,\n'
                 '              project:          &quot;open-space-traffic&quot;,\n'
                 '              subject_vid:      satelliteVid,\n'
                 '              action_class:     &quot;space.hostileRpo&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              satellite_norad_id:        noradId,\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit space.hostileRpo">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-space-traffic.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;space.hostileRpo&quot;" target="action"/>\n'
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
                 3057,
                 '00-contracts/bpmn/com/etzhayyim/open-space-traffic/trackHostileRpo.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-space-traffic-track-hostile-rpo-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fatf-greylist-flag-sanctions-evasion-v1',
                 'did:web:open-fatf-greylist.etzhayyim.com:ops',
                 'open_fatf_greylist_flag_sanctions_evasion',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_fatf_greylist_flag_sanctions_evasion"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-fatf-greylist"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_fatf_greylist_flag_sanctions_evasion" name="FATF Gray '
                 '制裁迂回" isExecutable="true">\n'
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
                 '&quot;open_fatf_greylist_flag_sanctions_evasion&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.fatfGreylist.flagSanctionsEvasion&quot;,\n'
                 '              project:          &quot;open-fatf-greylist&quot;,\n'
                 '              subject_vid:      entityLei,\n'
                 '              action_class:     &quot;sanctions.fatfEvasion&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_lei:        entityLei,\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit sanctions.fatfEvasion">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-fatf-greylist.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sanctions.fatfEvasion&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: entityLei, '
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
                 3086,
                 '00-contracts/bpmn/com/etzhayyim/open-fatf-greylist/flagSanctionsEvasion.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-fatf-greylist.etzhayyim.com:ops',
                 'did:web:open-fatf-greylist.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fatf-greylist-flag-sanctions-evasion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fatf-travel-rule-flag-crypto-sanctions-evasion-v1',
                 'did:web:open-fatf-travel-rule.etzhayyim.com:ops',
                 'open_fatf_travel_rule_flag_crypto_sanctions_evasion',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_fatf_travel_rule_flag_crypto_sanctions_evasion"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-fatf-travel-rule"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_fatf_travel_rule_flag_crypto_sanctions_evasion" '
                 'name="crypto travel rule 迂回" isExecutable="true">\n'
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
                 '&quot;open_fatf_travel_rule_flag_crypto_sanctions_evasion&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.fatfTravelRule.flagCryptoSanctionsEvasion&quot;,\n'
                 '              project:          &quot;open-fatf-travel-rule&quot;,\n'
                 '              subject_vid:      vaspLei,\n'
                 '              action_class:     &quot;sanctions.cryptoEvasion&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_lei:        vaspLei,\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit sanctions.cryptoEvasion">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-fatf-travel-rule.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sanctions.cryptoEvasion&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: vaspLei, '
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
                 3136,
                 '00-contracts/bpmn/com/etzhayyim/open-fatf-travel-rule/flagCryptoSanctionsEvasion.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-fatf-travel-rule.etzhayyim.com:ops',
                 'did:web:open-fatf-travel-rule.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fatf-travel-rule-flag-crypto-sanctions-evasion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-crypto-mixer-sanction-flag-mixer-use-by-dprk-v1',
                 'did:web:open-crypto-mixer-sanction.etzhayyim.com:ops',
                 'open_crypto_mixer_sanction_flag_mixer_use_by_dprk',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_crypto_mixer_sanction_flag_mixer_use_by_dprk"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-crypto-mixer-sanction"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_crypto_mixer_sanction_flag_mixer_use_by_dprk" '
                 'name="DPRK Lazarus mixer" isExecutable="true">\n'
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
                 '&quot;open_crypto_mixer_sanction_flag_mixer_use_by_dprk&quot;,\n'
                 '              nsid:             '
                 '&quot;com.etzhayyim.apps.cryptoMixerSanction.flagMixerUseByDprk&quot;,\n'
                 '              project:          &quot;open-crypto-mixer-sanction&quot;,\n'
                 '              subject_vid:      mixerLei,\n'
                 '              action_class:     &quot;sanctions.dprkMixer&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_lei:        mixerLei,\n'
                 '              subject_country:        &quot;KP&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit sanctions.dprkMixer">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-crypto-mixer-sanction.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sanctions.dprkMixer&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: mixerLei, '
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
                 3141,
                 '00-contracts/bpmn/com/etzhayyim/open-crypto-mixer-sanction/flagMixerUseByDprk.bpmn',
                 '2026-04-25T14:00:00Z',
                 'did:web:open-crypto-mixer-sanction.etzhayyim.com:ops',
                 'did:web:open-crypto-mixer-sanction.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-crypto-mixer-sanction-flag-mixer-use-by-dprk-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-soc-escalateStateApt-v1',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cyberSoc.escalateStateApt',
                 'open_cyber_soc_escalate_state_apt',
                 20000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-soc-escalateStateApt-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-incident-linkIncidentToTreaty-v1',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cyberIncident.linkIncidentToTreaty',
                 'open_cyber_incident_link_incident_to_treaty',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-incident-linkIncidentToTreaty-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mass-autonomous-ship-flagWeaponizedMass-v1',
                 'did:web:open-mass-autonomous-ship.etzhayyim.com:ops',
                 'com.etzhayyim.apps.massAutonomousShip.flagWeaponizedMass',
                 'open_mass_autonomous_ship_flag_weaponized_mass',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-mass-autonomous-ship.etzhayyim.com:ops',
                 'did:web:open-mass-autonomous-ship.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mass-autonomous-ship-flagWeaponizedMass-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fusion-energy-flagIcfWeaponsLink-v1',
                 'did:web:open-fusion-energy.etzhayyim.com:ops',
                 'com.etzhayyim.apps.fusionEnergy.flagIcfWeaponsLink',
                 'open_fusion_energy_flag_icf_weapons_link',
                 20000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-fusion-energy.etzhayyim.com:ops',
                 'did:web:open-fusion-energy.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fusion-energy-flagIcfWeaponsLink-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-pandemic-treaty-flagBwcDualUse-v1',
                 'did:web:open-pandemic-treaty.etzhayyim.com:ops',
                 'com.etzhayyim.apps.pandemicTreaty.flagBwcDualUse',
                 'open_pandemic_treaty_flag_bwc_dual_use',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-pandemic-treaty.etzhayyim.com:ops',
                 'did:web:open-pandemic-treaty.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-pandemic-treaty-flagBwcDualUse-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyclone-prepo-flagMilitaryHadr-v1',
                 'did:web:open-cyclone-prepo.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cyclonePrepo.flagMilitaryHadr',
                 'open_cyclone_prepo_flag_military_hadr',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-cyclone-prepo.etzhayyim.com:ops',
                 'did:web:open-cyclone-prepo.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyclone-prepo-flagMilitaryHadr-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-naval-flagFreedomOfNavigation-v1',
                 'did:web:open-redsea-naval.etzhayyim.com:ops',
                 'com.etzhayyim.apps.redseaNaval.flagFreedomOfNavigation',
                 'open_redsea_naval_flag_freedom_of_navigation',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-redsea-naval.etzhayyim.com:ops',
                 'did:web:open-redsea-naval.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-naval-flagFreedomOfNavigation-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-incident-flagShipMissileStrike-v1',
                 'did:web:open-redsea-incident.etzhayyim.com:ops',
                 'com.etzhayyim.apps.redseaIncident.flagShipMissileStrike',
                 'open_redsea_incident_flag_ship_missile_strike',
                 20000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-redsea-incident.etzhayyim.com:ops',
                 'did:web:open-redsea-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-incident-flagShipMissileStrike-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-rerouting-flagSupplyChainImpact-v1',
                 'did:web:open-redsea-rerouting.etzhayyim.com:ops',
                 'com.etzhayyim.apps.redseaRerouting.flagSupplyChainImpact',
                 'open_redsea_rerouting_flag_supply_chain_impact',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-redsea-rerouting.etzhayyim.com:ops',
                 'did:web:open-redsea-rerouting.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-rerouting-flagSupplyChainImpact-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-hormuz-darkfleet-flagIranSpoofing-v1',
                 'did:web:open-hormuz-darkfleet.etzhayyim.com:ops',
                 'com.etzhayyim.apps.hormuzDarkfleet.flagIranSpoofing',
                 'open_hormuz_darkfleet_flag_iran_spoofing',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-hormuz-darkfleet.etzhayyim.com:ops',
                 'did:web:open-hormuz-darkfleet.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-hormuz-darkfleet-flagIranSpoofing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-hormuz-incident-flagTankerHijack-v1',
                 'did:web:open-hormuz-incident.etzhayyim.com:ops',
                 'com.etzhayyim.apps.hormuzIncident.flagTankerHijack',
                 'open_hormuz_incident_flag_tanker_hijack',
                 20000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-hormuz-incident.etzhayyim.com:ops',
                 'did:web:open-hormuz-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-hormuz-incident-flagTankerHijack-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-malacca-incident-flagPiracyEscort-v1',
                 'did:web:open-malacca-incident.etzhayyim.com:ops',
                 'com.etzhayyim.apps.malaccaIncident.flagPiracyEscort',
                 'open_malacca_incident_flag_piracy_escort',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-malacca-incident.etzhayyim.com:ops',
                 'did:web:open-malacca-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-malacca-incident-flagPiracyEscort-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cell-broadcast-alert-notifyJalert-v1',
                 'did:web:open-cell-broadcast-alert.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cellBroadcastAlert.notifyJalert',
                 'open_cell_broadcast_alert_notify_jalert',
                 10000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-cell-broadcast-alert.etzhayyim.com:ops',
                 'did:web:open-cell-broadcast-alert.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cell-broadcast-alert-notifyJalert-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-internet-shutdown-flagWartimeShutdown-v1',
                 'did:web:open-internet-shutdown.etzhayyim.com:ops',
                 'com.etzhayyim.apps.internetShutdown.flagWartimeShutdown',
                 'open_internet_shutdown_flag_wartime_shutdown',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-internet-shutdown.etzhayyim.com:ops',
                 'did:web:open-internet-shutdown.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-internet-shutdown-flagWartimeShutdown-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-encryption-debate-flagBackdoorMandate-v1',
                 'did:web:open-encryption-debate.etzhayyim.com:ops',
                 'com.etzhayyim.apps.encryptionDebate.flagBackdoorMandate',
                 'open_encryption_debate_flag_backdoor_mandate',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-encryption-debate.etzhayyim.com:ops',
                 'did:web:open-encryption-debate.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-encryption-debate-flagBackdoorMandate-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mining-operation-flagConflictMineral-v1',
                 'did:web:open-mining-operation.etzhayyim.com:ops',
                 'com.etzhayyim.apps.miningOperation.flagConflictMineral',
                 'open_mining_operation_flag_conflict_mineral',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-mining-operation.etzhayyim.com:ops',
                 'did:web:open-mining-operation.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mining-operation-flagConflictMineral-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-deep-sea-mining-flagStrategicSeabedClaim-v1',
                 'did:web:open-deep-sea-mining.etzhayyim.com:ops',
                 'com.etzhayyim.apps.deepSeaMining.flagStrategicSeabedClaim',
                 'open_deep_sea_mining_flag_strategic_seabed_claim',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-deep-sea-mining.etzhayyim.com:ops',
                 'did:web:open-deep-sea-mining.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-deep-sea-mining-flagStrategicSeabedClaim-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-arctic-nsr-flagArcticMilitarization-v1',
                 'did:web:open-arctic-nsr.etzhayyim.com:ops',
                 'com.etzhayyim.apps.arcticNsr.flagArcticMilitarization',
                 'open_arctic_nsr_flag_arctic_militarization',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-arctic-nsr.etzhayyim.com:ops',
                 'did:web:open-arctic-nsr.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-arctic-nsr-flagArcticMilitarization-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-antarctic-treaty-flagAntarcticMilitary-v1',
                 'did:web:open-antarctic-treaty.etzhayyim.com:ops',
                 'com.etzhayyim.apps.antarcticTreaty.flagAntarcticMilitary',
                 'open_antarctic_treaty_flag_antarctic_military',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-antarctic-treaty.etzhayyim.com:ops',
                 'did:web:open-antarctic-treaty.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-antarctic-treaty-flagAntarcticMilitary-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-bbnj-highseas-flagHighseasMilitary-v1',
                 'did:web:open-bbnj-highseas.etzhayyim.com:ops',
                 'com.etzhayyim.apps.bbnjHighseas.flagHighseasMilitary',
                 'open_bbnj_highseas_flag_highseas_military',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-bbnj-highseas.etzhayyim.com:ops',
                 'did:web:open-bbnj-highseas.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-bbnj-highseas-flagHighseasMilitary-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-orbital-debris-trackKesslerCascade-v1',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'com.etzhayyim.apps.orbitalDebris.trackKesslerCascade',
                 'open_orbital_debris_track_kessler_cascade',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'did:web:open-orbital-debris.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-orbital-debris-trackKesslerCascade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-space-traffic-trackHostileRpo-v1',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'com.etzhayyim.apps.spaceTraffic.trackHostileRpo',
                 'open_space_traffic_track_hostile_rpo',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'did:web:open-space-traffic.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-space-traffic-trackHostileRpo-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fatf-greylist-flagSanctionsEvasion-v1',
                 'did:web:open-fatf-greylist.etzhayyim.com:ops',
                 'com.etzhayyim.apps.fatfGreylist.flagSanctionsEvasion',
                 'open_fatf_greylist_flag_sanctions_evasion',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-fatf-greylist.etzhayyim.com:ops',
                 'did:web:open-fatf-greylist.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fatf-greylist-flagSanctionsEvasion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fatf-travel-rule-flagCryptoSanctionsEvasion-v1',
                 'did:web:open-fatf-travel-rule.etzhayyim.com:ops',
                 'com.etzhayyim.apps.fatfTravelRule.flagCryptoSanctionsEvasion',
                 'open_fatf_travel_rule_flag_crypto_sanctions_evasion',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-fatf-travel-rule.etzhayyim.com:ops',
                 'did:web:open-fatf-travel-rule.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fatf-travel-rule-flagCryptoSanctionsEvasion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-crypto-mixer-sanction-flagMixerUseByDprk-v1',
                 'did:web:open-crypto-mixer-sanction.etzhayyim.com:ops',
                 'com.etzhayyim.apps.cryptoMixerSanction.flagMixerUseByDprk',
                 'open_crypto_mixer_sanction_flag_mixer_use_by_dprk',
                 15000,
                 '2026-04-25T14:00:00Z',
                 'did:web:open-crypto-mixer-sanction.etzhayyim.com:ops',
                 'did:web:open-crypto-mixer-sanction.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w4',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-crypto-mixer-sanction-flagMixerUseByDprk-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-soc-escalateStateApt-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyber-incident-linkIncidentToTreaty-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mass-autonomous-ship-flagWeaponizedMass-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fusion-energy-flagIcfWeaponsLink-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-pandemic-treaty-flagBwcDualUse-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cyclone-prepo-flagMilitaryHadr-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-naval-flagFreedomOfNavigation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-incident-flagShipMissileStrike-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-redsea-rerouting-flagSupplyChainImpact-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-hormuz-darkfleet-flagIranSpoofing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-hormuz-incident-flagTankerHijack-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-malacca-incident-flagPiracyEscort-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-cell-broadcast-alert-notifyJalert-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-internet-shutdown-flagWartimeShutdown-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-encryption-debate-flagBackdoorMandate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-mining-operation-flagConflictMineral-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-deep-sea-mining-flagStrategicSeabedClaim-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-arctic-nsr-flagArcticMilitarization-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-antarctic-treaty-flagAntarcticMilitary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-bbnj-highseas-flagHighseasMilitary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-orbital-debris-trackKesslerCascade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-space-traffic-trackHostileRpo-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fatf-greylist-flagSanctionsEvasion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-fatf-travel-rule-flagCryptoSanctionsEvasion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-crypto-mixer-sanction-flagMixerUseByDprk-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-soc-escalate-state-apt-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyber-incident-link-incident-to-treaty-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mass-autonomous-ship-flag-weaponized-mass-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fusion-energy-flag-icf-weapons-link-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-pandemic-treaty-flag-bwc-dual-use-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cyclone-prepo-flag-military-hadr-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-naval-flag-freedom-of-navigation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-incident-flag-ship-missile-strike-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-redsea-rerouting-flag-supply-chain-impact-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-hormuz-darkfleet-flag-iran-spoofing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-hormuz-incident-flag-tanker-hijack-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-malacca-incident-flag-piracy-escort-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-cell-broadcast-alert-notify-jalert-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-internet-shutdown-flag-wartime-shutdown-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-encryption-debate-flag-backdoor-mandate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-mining-operation-flag-conflict-mineral-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-deep-sea-mining-flag-strategic-seabed-claim-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-arctic-nsr-flag-arctic-militarization-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-antarctic-treaty-flag-antarctic-military-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-bbnj-highseas-flag-highseas-military-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-orbital-debris-track-kessler-cascade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-space-traffic-track-hostile-rpo-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fatf-greylist-flag-sanctions-evasion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-fatf-travel-rule-flag-crypto-sanctions-evasion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-crypto-mixer-sanction-flag-mixer-use-by-dprk-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
