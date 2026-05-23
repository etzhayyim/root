"""Captured from Kysely migration 20260425150000_seed_open_defence_wave5_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425150000_seed_open_defence_wave5_bpmn_actors"
down_revision = 'r_20260425140000_seed_open_defence_wave4_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-flag-bwc-breach-v1',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'open_biosecurity_flag_bwc_breach',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_biosecurity_flag_bwc_breach"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-biosecurity"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_biosecurity_flag_bwc_breach" name="BWC 違反 (生物兵器)" '
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
                 '              bpmn_process_id:  &quot;open_biosecurity_flag_bwc_breach&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.biosecurity.flagBwcBreach&quot;,\n'
                 '              project:          &quot;open-biosecurity&quot;,\n'
                 '              subject_vid:      labVid,\n'
                 '              action_class:     &quot;bio.bwcBreach&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit bio.bwcBreach">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-biosecurity.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;bio.bwcBreach&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: labVid, '
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
                 3032,
                 '00-contracts/bpmn/ai/gftd/open-biosecurity/flagBwcBreach.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-flag-bwc-breach-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-flag-dual-use-gof-v1',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'open_biosecurity_flag_dual_use_gof',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_biosecurity_flag_dual_use_gof"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-biosecurity"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_biosecurity_flag_dual_use_gof" name="機能獲得 (GoF) 軍民両用" '
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
                 '              bpmn_process_id:  &quot;open_biosecurity_flag_dual_use_gof&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.biosecurity.flagDualUseGof&quot;,\n'
                 '              project:          &quot;open-biosecurity&quot;,\n'
                 '              subject_vid:      researchVid,\n'
                 '              action_class:     &quot;bio.gofDualUse&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit bio.gofDualUse">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-biosecurity.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;bio.gofDualUse&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: researchVid, '
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
                 3053,
                 '00-contracts/bpmn/ai/gftd/open-biosecurity/flagDualUseGof.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-flag-dual-use-gof-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-certification-track-bsl-export-control-v1',
                 'did:web:open-biosecurity-certification.etzhayyim.com:ops',
                 'open_biosecurity_certification_track_bsl_export_control',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_biosecurity_certification_track_bsl_export_control"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-biosecurity-certification"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_biosecurity_certification_track_bsl_export_control" '
                 'name="BSL 設備 輸出管理" isExecutable="true">\n'
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
                 '&quot;open_biosecurity_certification_track_bsl_export_control&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.biosecurityCertification.trackBslExportControl&quot;,\n'
                 '              project:          &quot;open-biosecurity-certification&quot;,\n'
                 '              subject_vid:      equipmentVid,\n'
                 '              action_class:     &quot;bio.bslExport&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_lei:        supplierLei,\n'
                 '              subject_country:        destination,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit bio.bslExport">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-biosecurity-certification.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;bio.bslExport&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: equipmentVid, '
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
                 3166,
                 '00-contracts/bpmn/ai/gftd/open-biosecurity-certification/trackBslExportControl.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-biosecurity-certification.etzhayyim.com:ops',
                 'did:web:open-biosecurity-certification.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-certification-track-bsl-export-control-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-amr-surveillance-flag-bioweapon-signal-v1',
                 'did:web:open-amr-surveillance.etzhayyim.com:ops',
                 'open_amr_surveillance_flag_bioweapon_signal',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_amr_surveillance_flag_bioweapon_signal"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-amr-surveillance"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_amr_surveillance_flag_bioweapon_signal" name="薬剤耐性 → '
                 '兵器化兆候" isExecutable="true">\n'
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
                 '&quot;open_amr_surveillance_flag_bioweapon_signal&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.amrSurveillance.flagBioweaponSignal&quot;,\n'
                 '              project:          &quot;open-amr-surveillance&quot;,\n'
                 '              subject_vid:      pathogen,\n'
                 '              action_class:     &quot;bio.amrWeaponSignal&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit bio.amrWeaponSignal">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-amr-surveillance.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;bio.amrWeaponSignal&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: pathogen, '
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
                 3068,
                 '00-contracts/bpmn/ai/gftd/open-amr-surveillance/flagBioweaponSignal.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-amr-surveillance.etzhayyim.com:ops',
                 'did:web:open-amr-surveillance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-amr-surveillance-flag-bioweapon-signal-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-flag-countermeasure-gap-v1',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'open_pharma_supply_flag_countermeasure_gap',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_pharma_supply_flag_countermeasure_gap"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-pharma-supply"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_pharma_supply_flag_countermeasure_gap" name="医療対抗手段 '
                 'ギャップ" isExecutable="true">\n'
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
                 '&quot;open_pharma_supply_flag_countermeasure_gap&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.pharmaSupply.flagCountermeasureGap&quot;,\n'
                 '              project:          &quot;open-pharma-supply&quot;,\n'
                 '              subject_vid:      drugCode,\n'
                 '              action_class:     &quot;pharma.countermeasureGap&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
                 '              subject_lei:        supplierLei,\n'
                 '              commodity_code:        drugCode,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit pharma.countermeasureGap">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-pharma-supply.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;pharma.countermeasureGap&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: drugCode, '
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
                 3155,
                 '00-contracts/bpmn/ai/gftd/open-pharma-supply/flagCountermeasureGap.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-flag-countermeasure-gap-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-mrna-vaccine-hub-flag-strategic-reserve-breach-v1',
                 'did:web:open-mrna-vaccine-hub.etzhayyim.com:ops',
                 'open_mrna_vaccine_hub_flag_strategic_reserve_breach',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_mrna_vaccine_hub_flag_strategic_reserve_breach"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-mrna-vaccine-hub"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_mrna_vaccine_hub_flag_strategic_reserve_breach" '
                 'name="戦略 mRNA リザーブ侵害" isExecutable="true">\n'
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
                 '&quot;open_mrna_vaccine_hub_flag_strategic_reserve_breach&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.mrnaVaccineHub.flagStrategicReserveBreach&quot;,\n'
                 '              project:          &quot;open-mrna-vaccine-hub&quot;,\n'
                 '              subject_vid:      hubVid,\n'
                 '              action_class:     &quot;pharma.mrnaReserveBreach&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit pharma.mrnaReserveBreach">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-mrna-vaccine-hub.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;pharma.mrnaReserveBreach&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: hubVid, '
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
                 3107,
                 '00-contracts/bpmn/ai/gftd/open-mrna-vaccine-hub/flagStrategicReserveBreach.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-mrna-vaccine-hub.etzhayyim.com:ops',
                 'did:web:open-mrna-vaccine-hub.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-mrna-vaccine-hub-flag-strategic-reserve-breach-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-agri-food-security-flag-food-weaponization-v1',
                 'did:web:open-agri-food-security.etzhayyim.com:ops',
                 'open_agri_food_security_flag_food_weaponization',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_agri_food_security_flag_food_weaponization"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-agri-food-security"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_agri_food_security_flag_food_weaponization" name="食料 '
                 '兵器化 フラグ" isExecutable="true">\n'
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
                 '&quot;open_agri_food_security_flag_food_weaponization&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.agriFoodSecurity.flagFoodWeaponization&quot;,\n'
                 '              project:          &quot;open-agri-food-security&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;bio.foodWeaponization&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit bio.foodWeaponization">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-agri-food-security.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;bio.foodWeaponization&quot;" '
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
                 3095,
                 '00-contracts/bpmn/ai/gftd/open-agri-food-security/flagFoodWeaponization.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-agri-food-security.etzhayyim.com:ops',
                 'did:web:open-agri-food-security.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-agri-food-security-flag-food-weaponization-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-feed-provenance-flag-agroterrorism-v1',
                 'did:web:open-feed-provenance.etzhayyim.com:ops',
                 'open_feed_provenance_flag_agroterrorism',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_feed_provenance_flag_agroterrorism"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-feed-provenance"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_feed_provenance_flag_agroterrorism" name="農業テロ フラグ" '
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
                 '&quot;open_feed_provenance_flag_agroterrorism&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.feedProvenance.flagAgroterrorism&quot;,\n'
                 '              project:          &quot;open-feed-provenance&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;bio.agroterrorism&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit bio.agroterrorism">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-feed-provenance.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;bio.agroterrorism&quot;" '
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
                 3040,
                 '00-contracts/bpmn/ai/gftd/open-feed-provenance/flagAgroterrorism.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-feed-provenance.etzhayyim.com:ops',
                 'did:web:open-feed-provenance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-feed-provenance-flag-agroterrorism-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pandemic-prep-flag-bio-military-stockpile-v1',
                 'did:web:open-pandemic-prep.etzhayyim.com:ops',
                 'open_pandemic_prep_flag_bio_military_stockpile',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_pandemic_prep_flag_bio_military_stockpile"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-pandemic-prep"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_pandemic_prep_flag_bio_military_stockpile" name="軍事系 '
                 '生物備蓄 フラグ" isExecutable="true">\n'
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
                 '&quot;open_pandemic_prep_flag_bio_military_stockpile&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.pandemicPrep.flagBioMilitaryStockpile&quot;,\n'
                 '              project:          &quot;open-pandemic-prep&quot;,\n'
                 '              subject_vid:      stockpileVid,\n'
                 '              action_class:     &quot;bio.militaryStockpile&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit bio.militaryStockpile">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-pandemic-prep.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;bio.militaryStockpile&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: stockpileVid, '
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
                 3123,
                 '00-contracts/bpmn/ai/gftd/open-pandemic-prep/flagBioMilitaryStockpile.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-pandemic-prep.etzhayyim.com:ops',
                 'did:web:open-pandemic-prep.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pandemic-prep-flag-bio-military-stockpile-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-trusted-flagger-flag-state-mandated-takedown-v1',
                 'did:web:open-trusted-flagger.etzhayyim.com:ops',
                 'open_trusted_flagger_flag_state_mandated_takedown',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_trusted_flagger_flag_state_mandated_takedown"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-trusted-flagger"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_trusted_flagger_flag_state_mandated_takedown" '
                 'name="国家命令 takedown" isExecutable="true">\n'
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
                 '&quot;open_trusted_flagger_flag_state_mandated_takedown&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.trustedFlagger.flagStateMandatedTakedown&quot;,\n'
                 '              project:          &quot;open-trusted-flagger&quot;,\n'
                 '              subject_vid:      takedownId,\n'
                 '              action_class:     &quot;info.stateTakedown&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit info.stateTakedown">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-trusted-flagger.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;info.stateTakedown&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: takedownId, '
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
                 3070,
                 '00-contracts/bpmn/ai/gftd/open-trusted-flagger/flagStateMandatedTakedown.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-trusted-flagger.etzhayyim.com:ops',
                 'did:web:open-trusted-flagger.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-trusted-flagger-flag-state-mandated-takedown-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-content-moderation-appeal-flag-political-censorship-v1',
                 'did:web:open-content-moderation-appeal.etzhayyim.com:ops',
                 'open_content_moderation_appeal_flag_political_censorship',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_content_moderation_appeal_flag_political_censorship"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-content-moderation-appeal"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_content_moderation_appeal_flag_political_censorship" '
                 'name="政治的検閲 フラグ" isExecutable="true">\n'
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
                 '&quot;open_content_moderation_appeal_flag_political_censorship&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.contentModerationAppeal.flagPoliticalCensorship&quot;,\n'
                 '              project:          &quot;open-content-moderation-appeal&quot;,\n'
                 '              subject_vid:      caseId,\n'
                 '              action_class:     &quot;info.politicalCensorship&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit info.politicalCensorship">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-content-moderation-appeal.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;info.politicalCensorship&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: caseId, '
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
                 3142,
                 '00-contracts/bpmn/ai/gftd/open-content-moderation-appeal/flagPoliticalCensorship.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-content-moderation-appeal.etzhayyim.com:ops',
                 'did:web:open-content-moderation-appeal.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-content-moderation-appeal-flag-political-censorship-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-press-finance-coercion-flag-state-media-coercion-v1',
                 'did:web:open-press-finance-coercion.etzhayyim.com:ops',
                 'open_press_finance_coercion_flag_state_media_coercion',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_press_finance_coercion_flag_state_media_coercion"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-press-finance-coercion"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_press_finance_coercion_flag_state_media_coercion" '
                 'name="報道機関 国家強要" isExecutable="true">\n'
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
                 '&quot;open_press_finance_coercion_flag_state_media_coercion&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.pressFinanceCoercion.flagStateMediaCoercion&quot;,\n'
                 '              project:          &quot;open-press-finance-coercion&quot;,\n'
                 '              subject_vid:      outletLei,\n'
                 '              action_class:     &quot;info.pressCoercion&quot;,\n'
                 '              severity:         &quot;high&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_lei:        outletLei,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit info.pressCoercion">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-press-finance-coercion.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;info.pressCoercion&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: outletLei, '
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
                 3153,
                 '00-contracts/bpmn/ai/gftd/open-press-finance-coercion/flagStateMediaCoercion.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-press-finance-coercion.etzhayyim.com:ops',
                 'did:web:open-press-finance-coercion.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-press-finance-coercion-flag-state-media-coercion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-misinformation-observatory-flag-coordinated-campaign-v1',
                 'did:web:open-misinformation-observatory.etzhayyim.com:ops',
                 'open_misinformation_observatory_flag_coordinated_campaign',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_misinformation_observatory_flag_coordinated_campaign"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-misinformation-observatory"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_misinformation_observatory_flag_coordinated_campaign" '
                 'name="情報戦 協調キャンペーン" isExecutable="true">\n'
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
                 '&quot;open_misinformation_observatory_flag_coordinated_campaign&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.misinformationObservatory.flagCoordinatedCampaign&quot;,\n'
                 '              project:          &quot;open-misinformation-observatory&quot;,\n'
                 '              subject_vid:      campaignVid,\n'
                 '              action_class:     &quot;info.coordinatedCampaign&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit info.coordinatedCampaign">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-misinformation-observatory.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;info.coordinatedCampaign&quot;" '
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
                 3122,
                 '00-contracts/bpmn/ai/gftd/open-misinformation-observatory/flagCoordinatedCampaign.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-misinformation-observatory.etzhayyim.com:ops',
                 'did:web:open-misinformation-observatory.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-misinformation-observatory-flag-coordinated-campaign-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-jamming-v1',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'open_itu_spectrum_flag_jamming',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_itu_spectrum_flag_jamming"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-itu-spectrum"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_itu_spectrum_flag_jamming" name="電波妨害 (jamming) フラグ" '
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
                 '              bpmn_process_id:  &quot;open_itu_spectrum_flag_jamming&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.ituSpectrum.flagJamming&quot;,\n'
                 '              project:          &quot;open-itu-spectrum&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;ew.jamming&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit ew.jamming">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-itu-spectrum.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ew.jamming&quot;" target="action"/>\n'
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
                 2976,
                 '00-contracts/bpmn/ai/gftd/open-itu-spectrum/flagJamming.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-jamming-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-gnss-spoofing-v1',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'open_itu_spectrum_flag_gnss_spoofing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_itu_spectrum_flag_gnss_spoofing"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-itu-spectrum"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_itu_spectrum_flag_gnss_spoofing" name="GNSS spoofing '
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
                 '&quot;open_itu_spectrum_flag_gnss_spoofing&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.ituSpectrum.flagGnssSpoofing&quot;,\n'
                 '              project:          &quot;open-itu-spectrum&quot;,\n'
                 '              subject_vid:      incidentVid,\n'
                 '              action_class:     &quot;ew.gnssSpoof&quot;,\n'
                 '              severity:         &quot;critical&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit ew.gnssSpoof">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-itu-spectrum.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ew.gnssSpoof&quot;" target="action"/>\n'
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
                 3004,
                 '00-contracts/bpmn/ai/gftd/open-itu-spectrum/flagGnssSpoofing.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-gnss-spoofing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-satellite-uplink-interference-v1',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'open_itu_spectrum_flag_satellite_uplink_interference',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_itu_spectrum_flag_satellite_uplink_interference"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-itu-spectrum"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_itu_spectrum_flag_satellite_uplink_interference" '
                 'name="衛星 アップリンク妨害" isExecutable="true">\n'
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
                 '&quot;open_itu_spectrum_flag_satellite_uplink_interference&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.ituSpectrum.flagSatelliteUplinkInterference&quot;,\n'
                 '              project:          &quot;open-itu-spectrum&quot;,\n'
                 '              subject_vid:      satelliteVid,\n'
                 '              action_class:     &quot;ew.satUplinkInterference&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit ew.satUplinkInterference">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-itu-spectrum.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ew.satUplinkInterference&quot;" '
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
                 3155,
                 '00-contracts/bpmn/ai/gftd/open-itu-spectrum/flagSatelliteUplinkInterference.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-satellite-uplink-interference-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-quantum-safe-crypto-flag-pqc-migration-lag-v1',
                 'did:web:open-quantum-safe-crypto.etzhayyim.com:ops',
                 'open_quantum_safe_crypto_flag_pqc_migration_lag',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_quantum_safe_crypto_flag_pqc_migration_lag"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-quantum-safe-crypto"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_quantum_safe_crypto_flag_pqc_migration_lag" name="PQC '
                 '移行遅延 (CNSA 2.0)" isExecutable="true">\n'
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
                 '&quot;open_quantum_safe_crypto_flag_pqc_migration_lag&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.quantumSafeCrypto.flagPqcMigrationLag&quot;,\n'
                 '              project:          &quot;open-quantum-safe-crypto&quot;,\n'
                 '              subject_vid:      systemVid,\n'
                 '              action_class:     &quot;cyber.pqcLag&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.pqcLag">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-quantum-safe-crypto.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.pqcLag&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: systemVid, '
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
                 3059,
                 '00-contracts/bpmn/ai/gftd/open-quantum-safe-crypto/flagPqcMigrationLag.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-quantum-safe-crypto.etzhayyim.com:ops',
                 'did:web:open-quantum-safe-crypto.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-quantum-safe-crypto-flag-pqc-migration-lag-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-qkd-quantum-register-military-qkd-link-v1',
                 'did:web:open-qkd-quantum.etzhayyim.com:ops',
                 'open_qkd_quantum_register_military_qkd_link',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_qkd_quantum_register_military_qkd_link"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-qkd-quantum"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_qkd_quantum_register_military_qkd_link" name="軍事 QKD '
                 'リンク登録" isExecutable="true">\n'
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
                 '&quot;open_qkd_quantum_register_military_qkd_link&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.qkdQuantum.registerMilitaryQkdLink&quot;,\n'
                 '              project:          &quot;open-qkd-quantum&quot;,\n'
                 '              subject_vid:      linkVid,\n'
                 '              action_class:     &quot;cyber.militaryQkd&quot;,\n'
                 '              severity:         &quot;info&quot;,\n'
                 '              detected_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              subject_country:        country,\n'
                 '              subject_lei:        nodeLei,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit cyber.militaryQkd">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-qkd-quantum.etzhayyim.com:ops&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;cyber.militaryQkd&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: linkVid, '
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
                 3073,
                 '00-contracts/bpmn/ai/gftd/open-qkd-quantum/registerMilitaryQkdLink.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-qkd-quantum.etzhayyim.com:ops',
                 'did:web:open-qkd-quantum.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-qkd-quantum-register-military-qkd-link-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-c2pa-content-cred-flag-adversarial-deepfake-v1',
                 'did:web:open-c2pa-content-cred.etzhayyim.com:ops',
                 'open_c2pa_content_cred_flag_adversarial_deepfake',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_c2pa_content_cred_flag_adversarial_deepfake"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-c2pa-content-cred"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_c2pa_content_cred_flag_adversarial_deepfake" name="敵対 '
                 'deepfake (C2PA 失敗)" isExecutable="true">\n'
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
                 '&quot;open_c2pa_content_cred_flag_adversarial_deepfake&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.c2paContentCred.flagAdversarialDeepfake&quot;,\n'
                 '              project:          &quot;open-c2pa-content-cred&quot;,\n'
                 '              subject_vid:      contentVid,\n'
                 '              action_class:     &quot;info.c2paFail&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit info.c2paFail">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-c2pa-content-cred.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;info.c2paFail&quot;" target="action"/>\n'
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
                 3018,
                 '00-contracts/bpmn/ai/gftd/open-c2pa-content-cred/flagAdversarialDeepfake.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-c2pa-content-cred.etzhayyim.com:ops',
                 'did:web:open-c2pa-content-cred.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-c2pa-content-cred-flag-adversarial-deepfake-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-spr-flag-strategic-drawdown-v1',
                 'did:web:open-spr.etzhayyim.com:ops',
                 'open_spr_flag_strategic_drawdown',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_spr_flag_strategic_drawdown"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-spr"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_spr_flag_strategic_drawdown" name="戦略石油備蓄 放出 (SPR)" '
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
                 '              bpmn_process_id:  &quot;open_spr_flag_strategic_drawdown&quot;,\n'
                 '              nsid:             '
                 '&quot;ai.gftd.apps.spr.flagStrategicDrawdown&quot;,\n'
                 '              project:          &quot;open-spr&quot;,\n'
                 '              subject_vid:      tranchId,\n'
                 '              action_class:     &quot;energy.sprDrawdown&quot;,\n'
                 '              severity:         &quot;info&quot;,\n'
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
                 '    <bpmn:serviceTask id="Task_Audit" name="audit energy.sprDrawdown">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-spr.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;energy.sprDrawdown&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, subjectVid: tranchId, '
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
                 2974,
                 '00-contracts/bpmn/ai/gftd/open-spr/flagStrategicDrawdown.bpmn',
                 '2026-04-25T15:00:00Z',
                 'did:web:open-spr.etzhayyim.com:ops',
                 'did:web:open-spr.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-spr-flag-strategic-drawdown-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-flagBwcBreach-v1',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'ai.gftd.apps.biosecurity.flagBwcBreach',
                 'open_biosecurity_flag_bwc_breach',
                 20000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-flagBwcBreach-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-flagDualUseGof-v1',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'ai.gftd.apps.biosecurity.flagDualUseGof',
                 'open_biosecurity_flag_dual_use_gof',
                 20000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'did:web:open-biosecurity.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-flagDualUseGof-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-certification-trackBslExportControl-v1',
                 'did:web:open-biosecurity-certification.etzhayyim.com:ops',
                 'ai.gftd.apps.biosecurityCertification.trackBslExportControl',
                 'open_biosecurity_certification_track_bsl_export_control',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-biosecurity-certification.etzhayyim.com:ops',
                 'did:web:open-biosecurity-certification.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-certification-trackBslExportControl-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-amr-surveillance-flagBioweaponSignal-v1',
                 'did:web:open-amr-surveillance.etzhayyim.com:ops',
                 'ai.gftd.apps.amrSurveillance.flagBioweaponSignal',
                 'open_amr_surveillance_flag_bioweapon_signal',
                 20000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-amr-surveillance.etzhayyim.com:ops',
                 'did:web:open-amr-surveillance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-amr-surveillance-flagBioweaponSignal-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-flagCountermeasureGap-v1',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'ai.gftd.apps.pharmaSupply.flagCountermeasureGap',
                 'open_pharma_supply_flag_countermeasure_gap',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-flagCountermeasureGap-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-mrna-vaccine-hub-flagStrategicReserveBreach-v1',
                 'did:web:open-mrna-vaccine-hub.etzhayyim.com:ops',
                 'ai.gftd.apps.mrnaVaccineHub.flagStrategicReserveBreach',
                 'open_mrna_vaccine_hub_flag_strategic_reserve_breach',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-mrna-vaccine-hub.etzhayyim.com:ops',
                 'did:web:open-mrna-vaccine-hub.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-mrna-vaccine-hub-flagStrategicReserveBreach-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-agri-food-security-flagFoodWeaponization-v1',
                 'did:web:open-agri-food-security.etzhayyim.com:ops',
                 'ai.gftd.apps.agriFoodSecurity.flagFoodWeaponization',
                 'open_agri_food_security_flag_food_weaponization',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-agri-food-security.etzhayyim.com:ops',
                 'did:web:open-agri-food-security.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-agri-food-security-flagFoodWeaponization-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-feed-provenance-flagAgroterrorism-v1',
                 'did:web:open-feed-provenance.etzhayyim.com:ops',
                 'ai.gftd.apps.feedProvenance.flagAgroterrorism',
                 'open_feed_provenance_flag_agroterrorism',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-feed-provenance.etzhayyim.com:ops',
                 'did:web:open-feed-provenance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-feed-provenance-flagAgroterrorism-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pandemic-prep-flagBioMilitaryStockpile-v1',
                 'did:web:open-pandemic-prep.etzhayyim.com:ops',
                 'ai.gftd.apps.pandemicPrep.flagBioMilitaryStockpile',
                 'open_pandemic_prep_flag_bio_military_stockpile',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-pandemic-prep.etzhayyim.com:ops',
                 'did:web:open-pandemic-prep.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pandemic-prep-flagBioMilitaryStockpile-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-trusted-flagger-flagStateMandatedTakedown-v1',
                 'did:web:open-trusted-flagger.etzhayyim.com:ops',
                 'ai.gftd.apps.trustedFlagger.flagStateMandatedTakedown',
                 'open_trusted_flagger_flag_state_mandated_takedown',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-trusted-flagger.etzhayyim.com:ops',
                 'did:web:open-trusted-flagger.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-trusted-flagger-flagStateMandatedTakedown-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-content-moderation-appeal-flagPoliticalCensorship-v1',
                 'did:web:open-content-moderation-appeal.etzhayyim.com:ops',
                 'ai.gftd.apps.contentModerationAppeal.flagPoliticalCensorship',
                 'open_content_moderation_appeal_flag_political_censorship',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-content-moderation-appeal.etzhayyim.com:ops',
                 'did:web:open-content-moderation-appeal.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-content-moderation-appeal-flagPoliticalCensorship-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-press-finance-coercion-flagStateMediaCoercion-v1',
                 'did:web:open-press-finance-coercion.etzhayyim.com:ops',
                 'ai.gftd.apps.pressFinanceCoercion.flagStateMediaCoercion',
                 'open_press_finance_coercion_flag_state_media_coercion',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-press-finance-coercion.etzhayyim.com:ops',
                 'did:web:open-press-finance-coercion.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-press-finance-coercion-flagStateMediaCoercion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-misinformation-observatory-flagCoordinatedCampaign-v1',
                 'did:web:open-misinformation-observatory.etzhayyim.com:ops',
                 'ai.gftd.apps.misinformationObservatory.flagCoordinatedCampaign',
                 'open_misinformation_observatory_flag_coordinated_campaign',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-misinformation-observatory.etzhayyim.com:ops',
                 'did:web:open-misinformation-observatory.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-misinformation-observatory-flagCoordinatedCampaign-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagJamming-v1',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'ai.gftd.apps.ituSpectrum.flagJamming',
                 'open_itu_spectrum_flag_jamming',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagJamming-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagGnssSpoofing-v1',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'ai.gftd.apps.ituSpectrum.flagGnssSpoofing',
                 'open_itu_spectrum_flag_gnss_spoofing',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagGnssSpoofing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagSatelliteUplinkInterference-v1',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'ai.gftd.apps.ituSpectrum.flagSatelliteUplinkInterference',
                 'open_itu_spectrum_flag_satellite_uplink_interference',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'did:web:open-itu-spectrum.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagSatelliteUplinkInterference-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-quantum-safe-crypto-flagPqcMigrationLag-v1',
                 'did:web:open-quantum-safe-crypto.etzhayyim.com:ops',
                 'ai.gftd.apps.quantumSafeCrypto.flagPqcMigrationLag',
                 'open_quantum_safe_crypto_flag_pqc_migration_lag',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-quantum-safe-crypto.etzhayyim.com:ops',
                 'did:web:open-quantum-safe-crypto.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-quantum-safe-crypto-flagPqcMigrationLag-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-qkd-quantum-registerMilitaryQkdLink-v1',
                 'did:web:open-qkd-quantum.etzhayyim.com:ops',
                 'ai.gftd.apps.qkdQuantum.registerMilitaryQkdLink',
                 'open_qkd_quantum_register_military_qkd_link',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-qkd-quantum.etzhayyim.com:ops',
                 'did:web:open-qkd-quantum.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-qkd-quantum-registerMilitaryQkdLink-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-c2pa-content-cred-flagAdversarialDeepfake-v1',
                 'did:web:open-c2pa-content-cred.etzhayyim.com:ops',
                 'ai.gftd.apps.c2paContentCred.flagAdversarialDeepfake',
                 'open_c2pa_content_cred_flag_adversarial_deepfake',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-c2pa-content-cred.etzhayyim.com:ops',
                 'did:web:open-c2pa-content-cred.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-c2pa-content-cred-flagAdversarialDeepfake-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-spr-flagStrategicDrawdown-v1',
                 'did:web:open-spr.etzhayyim.com:ops',
                 'ai.gftd.apps.spr.flagStrategicDrawdown',
                 'open_spr_flag_strategic_drawdown',
                 15000,
                 '2026-04-25T15:00:00Z',
                 'did:web:open-spr.etzhayyim.com:ops',
                 'did:web:open-spr.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-defence-w5',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-spr-flagStrategicDrawdown-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-flagBwcBreach-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-flagDualUseGof-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-biosecurity-certification-trackBslExportControl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-amr-surveillance-flagBioweaponSignal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-flagCountermeasureGap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-mrna-vaccine-hub-flagStrategicReserveBreach-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-agri-food-security-flagFoodWeaponization-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-feed-provenance-flagAgroterrorism-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pandemic-prep-flagBioMilitaryStockpile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-trusted-flagger-flagStateMandatedTakedown-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-content-moderation-appeal-flagPoliticalCensorship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-press-finance-coercion-flagStateMediaCoercion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-misinformation-observatory-flagCoordinatedCampaign-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagJamming-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagGnssSpoofing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-itu-spectrum-flagSatelliteUplinkInterference-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-quantum-safe-crypto-flagPqcMigrationLag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-qkd-quantum-registerMilitaryQkdLink-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-c2pa-content-cred-flagAdversarialDeepfake-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-spr-flagStrategicDrawdown-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-flag-bwc-breach-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-flag-dual-use-gof-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-biosecurity-certification-track-bsl-export-control-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-amr-surveillance-flag-bioweapon-signal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-flag-countermeasure-gap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-mrna-vaccine-hub-flag-strategic-reserve-breach-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-agri-food-security-flag-food-weaponization-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-feed-provenance-flag-agroterrorism-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pandemic-prep-flag-bio-military-stockpile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-trusted-flagger-flag-state-mandated-takedown-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-content-moderation-appeal-flag-political-censorship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-press-finance-coercion-flag-state-media-coercion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-misinformation-observatory-flag-coordinated-campaign-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-jamming-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-gnss-spoofing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-itu-spectrum-flag-satellite-uplink-interference-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-quantum-safe-crypto-flag-pqc-migration-lag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-qkd-quantum-register-military-qkd-link-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-c2pa-content-cred-flag-adversarial-deepfake-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-spr-flag-strategic-drawdown-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
