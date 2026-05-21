"""Captured from Kysely migration 20260425120000_seed_open_defence_wave3_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425120000_seed_open_defence_wave3_bpmn_actors"
down_revision = 'r_20260425120000_seed_gameka_merge_specs'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-critical-minerals-flag-rare-earth-chokepoint-v1',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'open_critical_minerals_flag_rare_earth_chokepoint',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_critical_minerals_flag_rare_earth_chokepoint"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-critical-minerals"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_critical_minerals_flag_rare_earth_chokepoint" name="希土類 '
                 'ボトルネック" isExecutable="true">\n'
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
                 '&quot;open_critical_minerals_flag_rare_earth_chokepoint&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.criticalMinerals.flagRareEarthChokepoint&quot;,\n'
                 '              project:          &quot;open-critical-minerals&quot;,\n'
                 '              subject_vid:      element,\n'
                 '              action_class:     &quot;supply.rareEarthChoke&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit supply.rareEarthChoke">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-critical-minerals.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;supply.rareEarthChoke&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: element, '
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
                 3047,
                 '00-contracts/bpmn/ai/gftd/open-critical-minerals/flagRareEarthChokepoint.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-critical-minerals-flag-rare-earth-chokepoint-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-critical-minerals-track-arms-grade-metal-v1',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'open_critical_minerals_track_arms_grade_metal',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_critical_minerals_track_arms_grade_metal"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-critical-minerals"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_critical_minerals_track_arms_grade_metal" name="武器級金属 '
                 'トレース" isExecutable="true">\n'
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
                 '&quot;open_critical_minerals_track_arms_grade_metal&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.criticalMinerals.trackArmsGradeMetal&quot;,\n'
                 '              project:          &quot;open-critical-minerals&quot;,\n'
                 '              subject_vid:      metalCode,\n'
                 '              action_class:     &quot;supply.armsGradeMetal&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit supply.armsGradeMetal">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-critical-minerals.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;supply.armsGradeMetal&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: metalCode, '
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
                 3027,
                 '00-contracts/bpmn/ai/gftd/open-critical-minerals/trackArmsGradeMetal.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-critical-minerals-track-arms-grade-metal-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-isic-classify-arms-manufacturing-v1',
                 'did:web:open-isic.etzhayyim.com:ops',
                 'open_isic_classify_arms_manufacturing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_isic_classify_arms_manufacturing"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-isic"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_isic_classify_arms_manufacturing" name="武器・弾薬製造 (ISIC '
                 '2520)" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveEvent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveEvent" name="openIsic classify arms '
                 'manufacturing">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openIsic.classifyArmsManufacturing"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_SaveEvent" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit industry.armsManufacture">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-isic.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;industry.armsManufacture&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: entityVid, '
                 'isicCode: isicCode, severity: &quot;high&quot;}" target="payload"/>\n'
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
                 1989,
                 '00-contracts/bpmn/ai/gftd/open-isic/classifyArmsManufacturing.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-isic.etzhayyim.com:ops',
                 'did:web:open-isic.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-isic-classify-arms-manufacturing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-unispsc-flag-arms-commodity-v1',
                 'did:web:open-unispsc.etzhayyim.com:ops',
                 'open_unispsc_flag_arms_commodity',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_unispsc_flag_arms_commodity"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-unispsc"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_unispsc_flag_arms_commodity" name="武器物資 (UNSPSC 46)" '
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
                 '              bpmn_process_id:  &quot;open_unispsc_flag_arms_commodity&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.openUnispsc.flagArmsCommodity&quot;,\n'
                 '              project:          &quot;open-unispsc&quot;,\n'
                 '              subject_vid:      commodityVid,\n'
                 '              action_class:     &quot;commodity.arms&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit commodity.arms">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-unispsc.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;commodity.arms&quot;" target="action"/>\n'
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
                 2932,
                 '00-contracts/bpmn/ai/gftd/open-unispsc/flagArmsCommodity.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-unispsc.etzhayyim.com:ops',
                 'did:web:open-unispsc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-unispsc-flag-arms-commodity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-export-credit-agency-track-arms-export-finance-v1',
                 'did:web:open-export-credit-agency.etzhayyim.com:ops',
                 'open_export_credit_agency_track_arms_export_finance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_export_credit_agency_track_arms_export_finance"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-export-credit-agency"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_export_credit_agency_track_arms_export_finance" '
                 'name="武器輸出 ECA 与信" isExecutable="true">\n'
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
                 '&quot;open_export_credit_agency_track_arms_export_finance&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.exportCreditAgency.trackArmsExportFinance&quot;,\n'
                 '              project:          &quot;open-export-credit-agency&quot;,\n'
                 '              subject_vid:      ecaLei,\n'
                 '              action_class:     &quot;finance.armsExport&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit finance.armsExport">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-export-credit-agency.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;finance.armsExport&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: ecaLei, '
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
                 3039,
                 '00-contracts/bpmn/ai/gftd/open-export-credit-agency/trackArmsExportFinance.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-export-credit-agency.etzhayyim.com:ops',
                 'did:web:open-export-credit-agency.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-export-credit-agency-track-arms-export-finance-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ai-supply-chain-flag-ai-weaponized-component-v1',
                 'did:web:open-ai-supply-chain.etzhayyim.com:ops',
                 'open_ai_supply_chain_flag_ai_weaponized_component',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_ai_supply_chain_flag_ai_weaponized_component"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-ai-supply-chain"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_ai_supply_chain_flag_ai_weaponized_component" name="AI '
                 '武器化部品 フラグ" isExecutable="true">\n'
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
                 '&quot;open_ai_supply_chain_flag_ai_weaponized_component&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.aiSupplyChain.flagAiWeaponizedComponent&quot;,\n'
                 '              project:          &quot;open-ai-supply-chain&quot;,\n'
                 '              subject_vid:      componentVid,\n'
                 '              action_class:     &quot;cyber.aiWeaponized&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.aiWeaponized">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-ai-supply-chain.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.aiWeaponized&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: componentVid, '
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
                 3041,
                 '00-contracts/bpmn/ai/gftd/open-ai-supply-chain/flagAiWeaponizedComponent.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-ai-supply-chain.etzhayyim.com:ops',
                 'did:web:open-ai-supply-chain.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ai-supply-chain-flag-ai-weaponized-component-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-aviation-safety-notify-military-notam-v1',
                 'did:web:open-aviation-safety.etzhayyim.com:ops',
                 'open_aviation_safety_notify_military_notam',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_aviation_safety_notify_military_notam"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-aviation-safety"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_aviation_safety_notify_military_notam" name="軍事 NOTAM '
                 '通知" isExecutable="true">\n'
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
                 '&quot;open_aviation_safety_notify_military_notam&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.aviationSafety.notifyMilitaryNotam&quot;,\n'
                 '              project:          &quot;open-aviation-safety&quot;,\n'
                 '              subject_vid:      notamId,\n'
                 '              action_class:     &quot;airspace.militaryNotam&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit airspace.militaryNotam">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-aviation-safety.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;airspace.militaryNotam&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: notamId, '
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
                 3000,
                 '00-contracts/bpmn/ai/gftd/open-aviation-safety/notifyMilitaryNotam.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-aviation-safety.etzhayyim.com:ops',
                 'did:web:open-aviation-safety.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-aviation-safety-notify-military-notam-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airport-narita-ops-flag-arms-cargo-customs-v1',
                 'did:web:open-airport-narita-ops.etzhayyim.com:ops',
                 'open_airport_narita_ops_flag_arms_cargo_customs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_airport_narita_ops_flag_arms_cargo_customs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-airport-narita-ops"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_airport_narita_ops_flag_arms_cargo_customs" name="成田 '
                 '武器貨物 通関" isExecutable="true">\n'
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
                 '&quot;open_airport_narita_ops_flag_arms_cargo_customs&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.airportNaritaOps.flagArmsCargoCustoms&quot;,\n'
                 '              project:          &quot;open-airport-narita-ops&quot;,\n'
                 '              subject_vid:      cargoVid,\n'
                 '              action_class:     &quot;customs.armsCargo&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit customs.armsCargo">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-airport-narita-ops.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;customs.armsCargo&quot;" '
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
                 3021,
                 '00-contracts/bpmn/ai/gftd/open-airport-narita-ops/flagArmsCargoCustoms.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-airport-narita-ops.etzhayyim.com:ops',
                 'did:web:open-airport-narita-ops.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airport-narita-ops-flag-arms-cargo-customs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airline-jal-ops-flag-cargo-arms-transit-v1',
                 'did:web:open-airline-jal-ops.etzhayyim.com:ops',
                 'open_airline_jal_ops_flag_cargo_arms_transit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_airline_jal_ops_flag_cargo_arms_transit"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-airline-jal-ops"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_airline_jal_ops_flag_cargo_arms_transit" name="JAL 貨物 '
                 '武器輸送" isExecutable="true">\n'
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
                 '&quot;open_airline_jal_ops_flag_cargo_arms_transit&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.airlineJalOps.flagCargoArmsTransit&quot;,\n'
                 '              project:          &quot;open-airline-jal-ops&quot;,\n'
                 '              subject_vid:      wayBillId,\n'
                 '              action_class:     &quot;cargo.armsTransit&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cargo.armsTransit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-airline-jal-ops.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cargo.armsTransit&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: wayBillId, '
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
                 2999,
                 '00-contracts/bpmn/ai/gftd/open-airline-jal-ops/flagCargoArmsTransit.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-airline-jal-ops.etzhayyim.com:ops',
                 'did:web:open-airline-jal-ops.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airline-jal-ops-flag-cargo-arms-transit-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-uas-traffic-management-flag-weaponized-drone-v1',
                 'did:web:open-uas-traffic-management.etzhayyim.com:ops',
                 'open_uas_traffic_management_flag_weaponized_drone',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_uas_traffic_management_flag_weaponized_drone"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-uas-traffic-management"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_uas_traffic_management_flag_weaponized_drone" '
                 'name="武装ドローン フラグ" isExecutable="true">\n'
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
                 '&quot;open_uas_traffic_management_flag_weaponized_drone&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.uasTrafficManagement.flagWeaponizedDrone&quot;,\n'
                 '              project:          &quot;open-uas-traffic-management&quot;,\n'
                 '              subject_vid:      droneVid,\n'
                 '              action_class:     &quot;uas.weaponized&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit uas.weaponized">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-uas-traffic-management.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;uas.weaponized&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: droneVid, '
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
                 3043,
                 '00-contracts/bpmn/ai/gftd/open-uas-traffic-management/flagWeaponizedDrone.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-uas-traffic-management.etzhayyim.com:ops',
                 'did:web:open-uas-traffic-management.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-uas-traffic-management-flag-weaponized-drone-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-artemis-lunar-flag-outer-space-treaty-violation-v1',
                 'did:web:open-artemis-lunar.etzhayyim.com:ops',
                 'open_artemis_lunar_flag_outer_space_treaty_violation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_artemis_lunar_flag_outer_space_treaty_violation"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-artemis-lunar"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_artemis_lunar_flag_outer_space_treaty_violation" '
                 'name="外気圏宇宙条約 違反" isExecutable="true">\n'
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
                 '&quot;open_artemis_lunar_flag_outer_space_treaty_violation&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.artemisLunar.flagOuterSpaceTreatyViolation&quot;,\n'
                 '              project:          &quot;open-artemis-lunar&quot;,\n'
                 '              subject_vid:      missionVid,\n'
                 '              action_class:     &quot;space.ostBreach&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit space.ostBreach">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-artemis-lunar.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;space.ostBreach&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: missionVid, '
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
                 3034,
                 '00-contracts/bpmn/ai/gftd/open-artemis-lunar/flagOuterSpaceTreatyViolation.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-artemis-lunar.etzhayyim.com:ops',
                 'did:web:open-artemis-lunar.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-artemis-lunar-flag-outer-space-treaty-violation-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-iaea-safeguards-flag-nuclear-weapon-diversion-v1',
                 'did:web:open-iaea-safeguards.etzhayyim.com:ops',
                 'open_iaea_safeguards_flag_nuclear_weapon_diversion',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_iaea_safeguards_flag_nuclear_weapon_diversion"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-iaea-safeguards"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_iaea_safeguards_flag_nuclear_weapon_diversion" '
                 'name="核物質 軍事転用 フラグ" isExecutable="true">\n'
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
                 '&quot;open_iaea_safeguards_flag_nuclear_weapon_diversion&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.iaeaSafeguards.flagNuclearWeaponDiversion&quot;,\n'
                 '              project:          &quot;open-iaea-safeguards&quot;,\n'
                 '              subject_vid:      facilityVid,\n'
                 '              action_class:     &quot;nuclear.diversion&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit nuclear.diversion">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-iaea-safeguards.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;nuclear.diversion&quot;" '
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
                 3045,
                 '00-contracts/bpmn/ai/gftd/open-iaea-safeguards/flagNuclearWeaponDiversion.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-iaea-safeguards.etzhayyim.com:ops',
                 'did:web:open-iaea-safeguards.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-iaea-safeguards-flag-nuclear-weapon-diversion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-disarmament-treaties-flag-treaty-breach-v1',
                 'did:web:open-disarmament-treaties.etzhayyim.com:ops',
                 'open_disarmament_treaties_flag_treaty_breach',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_disarmament_treaties_flag_treaty_breach"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-disarmament-treaties"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_disarmament_treaties_flag_treaty_breach" name="軍縮条約 違反 '
                 '(NPT/CTBT/BWC/CWC)" isExecutable="true">\n'
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
                 '&quot;open_disarmament_treaties_flag_treaty_breach&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.disarmamentTreaties.flagTreatyBreach&quot;,\n'
                 '              project:          &quot;open-disarmament-treaties&quot;,\n'
                 '              subject_vid:      partyCountry,\n'
                 '              action_class:     &quot;treaty.disarmamentBreach&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit treaty.disarmamentBreach">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-disarmament-treaties.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;treaty.disarmamentBreach&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: partyCountry, '
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
                 3066,
                 '00-contracts/bpmn/ai/gftd/open-disarmament-treaties/flagTreatyBreach.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-disarmament-treaties.etzhayyim.com:ops',
                 'did:web:open-disarmament-treaties.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-disarmament-treaties-flag-treaty-breach-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-jpn-gov-register-fms-case-v1',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'open_jpn_gov_register_fms_case',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_jpn_gov_register_fms_case"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-jpn-gov"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_jpn_gov_register_fms_case" name="FMS 案件登録 (米→日)" '
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
                 '              bpmn_process_id:  &quot;open_jpn_gov_register_fms_case&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.openJpnGov.registerFmsCase&quot;,\n'
                 '              project:          &quot;open-jpn-gov&quot;,\n'
                 '              subject_vid:      fmsCaseId,\n'
                 '              action_class:     &quot;boeiSho.fmsCase&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit boeiSho.fmsCase">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-jpn-gov.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;boeiSho.fmsCase&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: fmsCaseId, '
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
                 2924,
                 '00-contracts/bpmn/ai/gftd/open-jpn-gov/registerFmsCase.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-jpn-gov-register-fms-case-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-jpn-gov-register-kokusan-weapons-export-v1',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'open_jpn_gov_register_kokusan_weapons_export',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_jpn_gov_register_kokusan_weapons_export"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-jpn-gov"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_jpn_gov_register_kokusan_weapons_export" name="国産武器輸出 '
                 '(防衛装備移転三原則)" isExecutable="true">\n'
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
                 '&quot;open_jpn_gov_register_kokusan_weapons_export&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.openJpnGov.registerKokusanWeaponsExport&quot;,\n'
                 '              project:          &quot;open-jpn-gov&quot;,\n'
                 '              subject_vid:      exportPermitId,\n'
                 '              action_class:     &quot;boeiSho.armsExport&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit boeiSho.armsExport">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-jpn-gov.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;boeiSho.armsExport&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: exportPermitId, '
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
                 3018,
                 '00-contracts/bpmn/ai/gftd/open-jpn-gov/registerKokusanWeaponsExport.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-jpn-gov-register-kokusan-weapons-export-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ocds-procurement-flag-defence-procurement-v1',
                 'did:web:open-ocds-procurement.etzhayyim.com:ops',
                 'open_ocds_procurement_flag_defence_procurement',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_ocds_procurement_flag_defence_procurement"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-ocds-procurement"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_ocds_procurement_flag_defence_procurement" name="OCDS '
                 '防衛調達 フラグ" isExecutable="true">\n'
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
                 '&quot;open_ocds_procurement_flag_defence_procurement&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.ocdsProcurement.flagDefenceProcurement&quot;,\n'
                 '              project:          &quot;open-ocds-procurement&quot;,\n'
                 '              subject_vid:      tenderId,\n'
                 '              action_class:     &quot;procurement.defence&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit procurement.defence">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-ocds-procurement.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;procurement.defence&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: tenderId, '
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
                 3020,
                 '00-contracts/bpmn/ai/gftd/open-ocds-procurement/flagDefenceProcurement.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-ocds-procurement.etzhayyim.com:ops',
                 'did:web:open-ocds-procurement.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ocds-procurement-flag-defence-procurement-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-debarment-list-flag-arms-debarment-v1',
                 'did:web:open-debarment-list.etzhayyim.com:ops',
                 'open_debarment_list_flag_arms_debarment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_debarment_list_flag_arms_debarment"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-debarment-list"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_debarment_list_flag_arms_debarment" name="武器供給者 排除リスト" '
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
                 '&quot;open_debarment_list_flag_arms_debarment&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.debarmentList.flagArmsDebarment&quot;,\n'
                 '              project:          &quot;open-debarment-list&quot;,\n'
                 '              subject_vid:      supplierLei,\n'
                 '              action_class:     &quot;sanctions.armsDebarment&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit sanctions.armsDebarment">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-debarment-list.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sanctions.armsDebarment&quot;" '
                 'target="action"/>\n'
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
                 3008,
                 '00-contracts/bpmn/ai/gftd/open-debarment-list/flagArmsDebarment.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-debarment-list.etzhayyim.com:ops',
                 'did:web:open-debarment-list.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-debarment-list-flag-arms-debarment-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-laws-autonomous-weapons-flag-laws-deployment-v1',
                 'did:web:open-laws-autonomous-weapons.etzhayyim.com:ops',
                 'open_laws_autonomous_weapons_flag_laws_deployment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_laws_autonomous_weapons_flag_laws_deployment"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-laws-autonomous-weapons"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_laws_autonomous_weapons_flag_laws_deployment" '
                 'name="LAWS 配備 フラグ" isExecutable="true">\n'
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
                 '&quot;open_laws_autonomous_weapons_flag_laws_deployment&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.lawsAutonomousWeapons.flagLawsDeployment&quot;,\n'
                 '              project:          &quot;open-laws-autonomous-weapons&quot;,\n'
                 '              subject_vid:      systemVid,\n'
                 '              action_class:     &quot;laws.deployment&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit laws.deployment">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-laws-autonomous-weapons.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;laws.deployment&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: systemVid, '
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
                 '00-contracts/bpmn/ai/gftd/open-laws-autonomous-weapons/flagLawsDeployment.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-laws-autonomous-weapons.etzhayyim.com:ops',
                 'did:web:open-laws-autonomous-weapons.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-laws-autonomous-weapons-flag-laws-deployment-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-genocide-convention-flag-atrocity-arms-v1',
                 'did:web:open-genocide-convention.etzhayyim.com:ops',
                 'open_genocide_convention_flag_atrocity_arms',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_genocide_convention_flag_atrocity_arms"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-genocide-convention"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_genocide_convention_flag_atrocity_arms" name="ジェノサイド条約 '
                 '武器関与" isExecutable="true">\n'
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
                 '&quot;open_genocide_convention_flag_atrocity_arms&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.genocideConvention.flagAtrocityArms&quot;,\n'
                 '              project:          &quot;open-genocide-convention&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;atrocity.armsLink&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit atrocity.armsLink">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-genocide-convention.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;atrocity.armsLink&quot;" '
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
                 3035,
                 '00-contracts/bpmn/ai/gftd/open-genocide-convention/flagAtrocityArms.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-genocide-convention.etzhayyim.com:ops',
                 'did:web:open-genocide-convention.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-genocide-convention-flag-atrocity-arms-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-poc-ihl-flag-ihl-breach-arms-v1',
                 'did:web:open-poc-ihl.etzhayyim.com:ops',
                 'open_poc_ihl_flag_ihl_breach_arms',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_poc_ihl_flag_ihl_breach_arms"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-poc-ihl"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_poc_ihl_flag_ihl_breach_arms" name="国際人道法 違反 (武器)" '
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
                 '              bpmn_process_id:  &quot;open_poc_ihl_flag_ihl_breach_arms&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.pocIhl.flagIhlBreachArms&quot;,\n'
                 '              project:          &quot;open-poc-ihl&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;ihl.armsBreach&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit ihl.armsBreach">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-poc-ihl.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ihl.armsBreach&quot;" target="action"/>\n'
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
                 2943,
                 '00-contracts/bpmn/ai/gftd/open-poc-ihl/flagIhlBreachArms.bpmn',
                 '2026-04-25T12:00:00Z',
                 'did:web:open-poc-ihl.etzhayyim.com:ops',
                 'did:web:open-poc-ihl.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-poc-ihl-flag-ihl-breach-arms-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-critical-minerals-flagRareEarthChokepoint-v1',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'ai.gftd.apps.criticalMinerals.flagRareEarthChokepoint',
                 'open_critical_minerals_flag_rare_earth_chokepoint',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-critical-minerals-flagRareEarthChokepoint-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-critical-minerals-trackArmsGradeMetal-v1',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'ai.gftd.apps.criticalMinerals.trackArmsGradeMetal',
                 'open_critical_minerals_track_arms_grade_metal',
                 20000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'did:web:open-critical-minerals.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-critical-minerals-trackArmsGradeMetal-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-isic-classifyArmsManufacturing-v1',
                 'did:web:open-isic.etzhayyim.com:ops',
                 'ai.gftd.apps.openIsic.classifyArmsManufacturing',
                 'open_isic_classify_arms_manufacturing',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-isic.etzhayyim.com:ops',
                 'did:web:open-isic.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-isic-classifyArmsManufacturing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-unispsc-flagArmsCommodity-v1',
                 'did:web:open-unispsc.etzhayyim.com:ops',
                 'ai.gftd.apps.openUnispsc.flagArmsCommodity',
                 'open_unispsc_flag_arms_commodity',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-unispsc.etzhayyim.com:ops',
                 'did:web:open-unispsc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-unispsc-flagArmsCommodity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-export-credit-agency-trackArmsExportFinance-v1',
                 'did:web:open-export-credit-agency.etzhayyim.com:ops',
                 'ai.gftd.apps.exportCreditAgency.trackArmsExportFinance',
                 'open_export_credit_agency_track_arms_export_finance',
                 20000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-export-credit-agency.etzhayyim.com:ops',
                 'did:web:open-export-credit-agency.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-export-credit-agency-trackArmsExportFinance-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ai-supply-chain-flagAiWeaponizedComponent-v1',
                 'did:web:open-ai-supply-chain.etzhayyim.com:ops',
                 'ai.gftd.apps.aiSupplyChain.flagAiWeaponizedComponent',
                 'open_ai_supply_chain_flag_ai_weaponized_component',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-ai-supply-chain.etzhayyim.com:ops',
                 'did:web:open-ai-supply-chain.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ai-supply-chain-flagAiWeaponizedComponent-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-aviation-safety-notifyMilitaryNotam-v1',
                 'did:web:open-aviation-safety.etzhayyim.com:ops',
                 'ai.gftd.apps.aviationSafety.notifyMilitaryNotam',
                 'open_aviation_safety_notify_military_notam',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-aviation-safety.etzhayyim.com:ops',
                 'did:web:open-aviation-safety.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-aviation-safety-notifyMilitaryNotam-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airport-narita-ops-flagArmsCargoCustoms-v1',
                 'did:web:open-airport-narita-ops.etzhayyim.com:ops',
                 'ai.gftd.apps.airportNaritaOps.flagArmsCargoCustoms',
                 'open_airport_narita_ops_flag_arms_cargo_customs',
                 20000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-airport-narita-ops.etzhayyim.com:ops',
                 'did:web:open-airport-narita-ops.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airport-narita-ops-flagArmsCargoCustoms-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airline-jal-ops-flagCargoArmsTransit-v1',
                 'did:web:open-airline-jal-ops.etzhayyim.com:ops',
                 'ai.gftd.apps.airlineJalOps.flagCargoArmsTransit',
                 'open_airline_jal_ops_flag_cargo_arms_transit',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-airline-jal-ops.etzhayyim.com:ops',
                 'did:web:open-airline-jal-ops.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airline-jal-ops-flagCargoArmsTransit-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-uas-traffic-management-flagWeaponizedDrone-v1',
                 'did:web:open-uas-traffic-management.etzhayyim.com:ops',
                 'ai.gftd.apps.uasTrafficManagement.flagWeaponizedDrone',
                 'open_uas_traffic_management_flag_weaponized_drone',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-uas-traffic-management.etzhayyim.com:ops',
                 'did:web:open-uas-traffic-management.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-uas-traffic-management-flagWeaponizedDrone-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-artemis-lunar-flagOuterSpaceTreatyViolation-v1',
                 'did:web:open-artemis-lunar.etzhayyim.com:ops',
                 'ai.gftd.apps.artemisLunar.flagOuterSpaceTreatyViolation',
                 'open_artemis_lunar_flag_outer_space_treaty_violation',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-artemis-lunar.etzhayyim.com:ops',
                 'did:web:open-artemis-lunar.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-artemis-lunar-flagOuterSpaceTreatyViolation-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-iaea-safeguards-flagNuclearWeaponDiversion-v1',
                 'did:web:open-iaea-safeguards.etzhayyim.com:ops',
                 'ai.gftd.apps.iaeaSafeguards.flagNuclearWeaponDiversion',
                 'open_iaea_safeguards_flag_nuclear_weapon_diversion',
                 20000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-iaea-safeguards.etzhayyim.com:ops',
                 'did:web:open-iaea-safeguards.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-iaea-safeguards-flagNuclearWeaponDiversion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-disarmament-treaties-flagTreatyBreach-v1',
                 'did:web:open-disarmament-treaties.etzhayyim.com:ops',
                 'ai.gftd.apps.disarmamentTreaties.flagTreatyBreach',
                 'open_disarmament_treaties_flag_treaty_breach',
                 20000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-disarmament-treaties.etzhayyim.com:ops',
                 'did:web:open-disarmament-treaties.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-disarmament-treaties-flagTreatyBreach-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-jpn-gov-registerFmsCase-v1',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'ai.gftd.apps.openJpnGov.registerFmsCase',
                 'open_jpn_gov_register_fms_case',
                 20000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-jpn-gov-registerFmsCase-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-jpn-gov-registerKokusanWeaponsExport-v1',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'ai.gftd.apps.openJpnGov.registerKokusanWeaponsExport',
                 'open_jpn_gov_register_kokusan_weapons_export',
                 20000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'did:web:open-jpn-gov.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-jpn-gov-registerKokusanWeaponsExport-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ocds-procurement-flagDefenceProcurement-v1',
                 'did:web:open-ocds-procurement.etzhayyim.com:ops',
                 'ai.gftd.apps.ocdsProcurement.flagDefenceProcurement',
                 'open_ocds_procurement_flag_defence_procurement',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-ocds-procurement.etzhayyim.com:ops',
                 'did:web:open-ocds-procurement.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ocds-procurement-flagDefenceProcurement-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-debarment-list-flagArmsDebarment-v1',
                 'did:web:open-debarment-list.etzhayyim.com:ops',
                 'ai.gftd.apps.debarmentList.flagArmsDebarment',
                 'open_debarment_list_flag_arms_debarment',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-debarment-list.etzhayyim.com:ops',
                 'did:web:open-debarment-list.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-debarment-list-flagArmsDebarment-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-laws-autonomous-weapons-flagLawsDeployment-v1',
                 'did:web:open-laws-autonomous-weapons.etzhayyim.com:ops',
                 'ai.gftd.apps.lawsAutonomousWeapons.flagLawsDeployment',
                 'open_laws_autonomous_weapons_flag_laws_deployment',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-laws-autonomous-weapons.etzhayyim.com:ops',
                 'did:web:open-laws-autonomous-weapons.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-laws-autonomous-weapons-flagLawsDeployment-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-genocide-convention-flagAtrocityArms-v1',
                 'did:web:open-genocide-convention.etzhayyim.com:ops',
                 'ai.gftd.apps.genocideConvention.flagAtrocityArms',
                 'open_genocide_convention_flag_atrocity_arms',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-genocide-convention.etzhayyim.com:ops',
                 'did:web:open-genocide-convention.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-genocide-convention-flagAtrocityArms-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-poc-ihl-flagIhlBreachArms-v1',
                 'did:web:open-poc-ihl.etzhayyim.com:ops',
                 'ai.gftd.apps.pocIhl.flagIhlBreachArms',
                 'open_poc_ihl_flag_ihl_breach_arms',
                 15000,
                 '2026-04-25T12:00:00Z',
                 'did:web:open-poc-ihl.etzhayyim.com:ops',
                 'did:web:open-poc-ihl.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-poc-ihl-flagIhlBreachArms-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-critical-minerals-flagRareEarthChokepoint-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-critical-minerals-trackArmsGradeMetal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-isic-classifyArmsManufacturing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-unispsc-flagArmsCommodity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-export-credit-agency-trackArmsExportFinance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ai-supply-chain-flagAiWeaponizedComponent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-aviation-safety-notifyMilitaryNotam-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airport-narita-ops-flagArmsCargoCustoms-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airline-jal-ops-flagCargoArmsTransit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-uas-traffic-management-flagWeaponizedDrone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-artemis-lunar-flagOuterSpaceTreatyViolation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-iaea-safeguards-flagNuclearWeaponDiversion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-disarmament-treaties-flagTreatyBreach-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-jpn-gov-registerFmsCase-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-jpn-gov-registerKokusanWeaponsExport-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ocds-procurement-flagDefenceProcurement-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-debarment-list-flagArmsDebarment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-laws-autonomous-weapons-flagLawsDeployment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-genocide-convention-flagAtrocityArms-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-poc-ihl-flagIhlBreachArms-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-critical-minerals-flag-rare-earth-chokepoint-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-critical-minerals-track-arms-grade-metal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-isic-classify-arms-manufacturing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-unispsc-flag-arms-commodity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-export-credit-agency-track-arms-export-finance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ai-supply-chain-flag-ai-weaponized-component-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-aviation-safety-notify-military-notam-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airport-narita-ops-flag-arms-cargo-customs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airline-jal-ops-flag-cargo-arms-transit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-uas-traffic-management-flag-weaponized-drone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-artemis-lunar-flag-outer-space-treaty-violation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-iaea-safeguards-flag-nuclear-weapon-diversion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-disarmament-treaties-flag-treaty-breach-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-jpn-gov-register-fms-case-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-jpn-gov-register-kokusan-weapons-export-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ocds-procurement-flag-defence-procurement-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-debarment-list-flag-arms-debarment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-laws-autonomous-weapons-flag-laws-deployment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-genocide-convention-flag-atrocity-arms-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-poc-ihl-flag-ihl-breach-arms-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
