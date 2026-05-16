"""Captured from Kysely migration 20260428285000_seed_open_smartphone_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428285000_seed_open_smartphone_bpmn_actors"
down_revision = 'r_20260428284000_open_smartphone_process_mining'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-recordBomLine-v1',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'open_smartphone_bom_record_bom_line',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_bom_record_bom_line" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-bom" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_bom_record_bom_line" name="recordBomLine" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_bom_line&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, line_id: lineId, bom_did: '
                 'bomDid, component_type: componentType, vendor_name: vendorName, part_number: '
                 'partNumber, unit_cost_usd: unitCostUsd, open_source: openSource, license: '
                 'license, patent_did: patentDid, alternative_count: alternativeCount, created_at: '
                 'string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, '
                 'user_id: callerDid, actor_id: &quot;sys.bpmn.open-smartphone-bom&quot;}" '
                 'target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-bom.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneBom.recordBomLine&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, componentType: '
                 'componentType, openSource: openSource}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2552,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-bom/recordBomLine.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-recordBomLine-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-assembleBom-v1',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'open_smartphone_bom_assemble_bom',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_bom_assemble_bom" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-bom" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_bom_assemble_bom" name="assembleBom" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_bom&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, bom_id: bomId, '
                 'design_name: designName, version: version, soc_did: socDid, modem_did: modemDid, '
                 'os_did: osDid, ems_facility_did: emsFacilityDid, target_price_usd: '
                 'targetPriceUsd, open_score_pct: openScorePct, status: &quot;draft&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-bom&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-bom.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneBom.assembleBom&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, designName: designName, '
                 'version: version}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2515,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-bom/assembleBom.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-assembleBom-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-recordAlternativeSource-v1',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'open_smartphone_bom_record_alternative_source',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_bom_record_alternative_source" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-bom" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_bom_record_alternative_source" '
                 'name="recordAlternativeSource" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_bom_sourcer&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, bom_line_did: bomLineDid, '
                 'alt_vendor: altVendor, alt_part_number: altPartNumber, alt_unit_cost_usd: '
                 'altUnitCostUsd, open_source: openSource, availability: availability, '
                 'lead_time_weeks: leadTimeWeeks, notes: notes, created_at: string(now()), '
                 'owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, '
                 'actor_id: &quot;sys.bpmn.open-smartphone-bom&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-bom.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneBom.recordAlternativeSource&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, bomLineDid: bomLineDid, '
                 'altVendor: altVendor}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2556,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-bom/recordAlternativeSource.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-recordAlternativeSource-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-computeOpenScore-v1',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'open_smartphone_bom_compute_open_score',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_bom_compute_open_score" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-bom" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_bom_compute_open_score" '
                 'name="computeOpenScore" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Select"/>\n'
                 '    <bpmn:serviceTask id="Task_Select" name="query bom lines">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT count(*) as total, sum(case when '
                 'open_source then 1 else 0 end) as open_count, sum(unit_cost_usd) as total_cost '
                 'FROM vertex_open_smartphone_bom_line WHERE bom_did = &apos;&quot; + bomDid + '
                 '&quot;&apos;&quot;" target="query"/>\n'
                 '          <zeebe:output source="=rows" target="lines"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_B</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_B" sourceRef="Task_Select" '
                 'targetRef="Task_LLM"/>\n'
                 '    <bpmn:serviceTask id="Task_LLM" name="compute score">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;You are an open hardware auditor. Compute '
                 'an open_score_pct (0-100) for a smartphone BOM and list key closed-source risks '
                 'and recommendations.&quot;" target="prompt"/>\n'
                 '          <zeebe:input source="=&quot;BOM stats: total_lines=&quot; + '
                 'string(lines[1].total) + &quot;, open_source_lines=&quot; + '
                 'string(lines[1].open_count) + &quot;, total_cost_usd=&quot; + '
                 'string(lines[1].total_cost)" target="context"/>\n'
                 '          <zeebe:input source="={type: &quot;object&quot;, required: '
                 '[&quot;openScorePct&quot;, &quot;keyClosedRisks&quot;, '
                 '&quot;recommendations&quot;], properties: {openScorePct: {type: '
                 '&quot;number&quot;}, keyClosedRisks: {type: &quot;array&quot;, items: {type: '
                 '&quot;string&quot;}}, recommendations: {type: &quot;array&quot;, items: {type: '
                 '&quot;string&quot;}}}}" target="schema"/>\n'
                 '          <zeebe:output source="=result" target="scoreResult"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_B</bpmn:incoming><bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Task_LLM" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-bom.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneBom.computeOpenScore&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={bomDid: bomDid, openScorePct: '
                 'scoreResult.openScorePct}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3553,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-bom/computeOpenScore.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'did:web:open-smartphone-bom.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-computeOpenScore-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-registerFacility-v1',
                 'did:web:open-smartphone-ems.gftd.ai',
                 'open_smartphone_ems_register_facility',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_ems_register_facility" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-ems" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_ems_register_facility" '
                 'name="registerFacility" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_ems_facility&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, facility_id: facilityId, '
                 'operator_name: operatorName, operator_lei: operatorLei, location_iso3: '
                 'locationIso3, city: city, facility_type: facilityType, monthly_capacity_units: '
                 'monthlyCapacityUnits, certifications: certifications, rba_audit_status: '
                 'rbaAuditStatus, conflict_mineral_compliant: conflictMineralCompliant, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-ems&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-ems.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneEms.registerFacility&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, locationIso3: locationIso3, '
                 'facilityType: facilityType}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2667,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-ems/registerFacility.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-ems.gftd.ai',
                 'did:web:open-smartphone-ems.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-registerFacility-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-recordCapacityOrder-v1',
                 'did:web:open-smartphone-ems.gftd.ai',
                 'open_smartphone_ems_record_capacity_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_ems_record_capacity_order" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-ems" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_ems_record_capacity_order" '
                 'name="recordCapacityOrder" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_ems_order&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, order_id: orderId, '
                 'facility_did: facilityDid, bom_did: bomDid, quantity_units: quantityUnits, '
                 'target_unit_cost_usd: targetUnitCostUsd, delivery_quarter: deliveryQuarter, '
                 'quality_standard: qualityStandard, order_status: &quot;planned&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-ems&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-ems.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneEms.recordCapacityOrder&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, facilityDid: facilityDid, '
                 'quantityUnits: quantityUnits}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2573,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-ems/recordCapacityOrder.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-ems.gftd.ai',
                 'did:web:open-smartphone-ems.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-recordCapacityOrder-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-fetchComplianceDelta-v1',
                 'did:web:open-smartphone-ems.gftd.ai:ops',
                 'open_smartphone_ems_fetch_compliance_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_ems_fetch_compliance_delta" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-ems" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_ems_fetch_compliance_delta" '
                 'name="fetchComplianceDelta" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch RBA news">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={url: '
                 '&quot;https://www.responsiblebusiness.org/news/&quot;, method: &quot;GET&quot;}" '
                 'target="request"/>\n'
                 '          <zeebe:output source="=response.body" target="rawHtml"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_B</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_B" sourceRef="Task_Fetch" '
                 'targetRef="Task_LLM"/>\n'
                 '    <bpmn:serviceTask id="Task_LLM" name="extract compliance updates">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;Extract EMS/OEM factory compliance updates '
                 '(RBA audit failures, conflict minerals 3TG, labor violations, ISO '
                 'certifications) from the following news page. Return structured data.&quot;" '
                 'target="prompt"/>\n'
                 '          <zeebe:input source="=rawHtml" target="context"/>\n'
                 '          <zeebe:input source="={type: &quot;object&quot;, properties: {updates: '
                 '{type: &quot;array&quot;, items: {type: &quot;object&quot;, properties: '
                 '{facilityName: {type: &quot;string&quot;}, country: {type: &quot;string&quot;}, '
                 'issueType: {type: &quot;string&quot;}, severity: {type: &quot;string&quot;}, '
                 'date: {type: &quot;string&quot;}}}}}}" target="schema"/>\n'
                 '          <zeebe:output source="=result" target="parsed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_B</bpmn:incoming><bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Task_LLM" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-ems.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneEms.fetchComplianceDelta&quot;" target="action"/>\n'
                 '          <zeebe:input source="={count: count(parsed.updates)}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3439,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-ems/fetchComplianceDelta.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-ems.gftd.ai:ops',
                 'did:web:open-smartphone-ems.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-fetchComplianceDelta-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-dailyPulse-v1',
                 'did:web:open-smartphone-ems.gftd.ai:ops',
                 'open_smartphone_ems_daily_pulse',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_ems_daily_pulse" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-ems" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_ems_daily_pulse" name="dailyPulse" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Select"/>\n'
                 '    <bpmn:serviceTask id="Task_Select" name="query stats">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT count(*) as total, '
                 'sum(monthly_capacity_units) as total_capacity FROM '
                 'vertex_open_smartphone_ems_facility WHERE status=&apos;active&apos;&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:output source="=rows" target="stats"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Select" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-ems.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneEms.dailyPulse&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={total: stats[1].total, totalCapacity: '
                 'stats[1].total_capacity}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2332,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-ems/dailyPulse.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-ems.gftd.ai:ops',
                 'did:web:open-smartphone-ems.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-dailyPulse-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-recordModemSpec-v1',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'open_smartphone_modem_record_modem_spec',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_smartphone_modem_record_modem_spec" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-modem" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_modem_record_modem_spec" '
                 'name="recordModemSpec" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_smartphone_modem_spec&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, modem_id: modemId, '
                 'chip_name: chipName, rat_support: ratSupport, baseband_chip: basebandChip, '
                 'open_source_fw: openSourceFw, fw_license: fwLicense, max_dl_mbps: maxDlMbps, '
                 'max_ul_mbps: maxUlMbps, release_year: releaseYear, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-modem&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-smartphone-modem.gftd.ai&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.smartphoneModem.recordModemSpec&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2368,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-modem/recordModemSpec.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-recordModemSpec-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-recordTypeApproval-v1',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'open_smartphone_modem_record_type_approval',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_modem_record_type_approval" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-modem" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_modem_record_type_approval" '
                 'name="recordTypeApproval" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_smartphone_modem_type_approval&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, modem_did: modemDid, '
                 'authority: authority, certificate_no: certificateNo, jurisdiction_iso3: '
                 'jurisdictionIso3, approved_at: approvedAt, expiry_date: expiryDate, '
                 'rat_approved: ratApproved, status: &quot;active&quot;, created_at: '
                 'string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, '
                 'user_id: callerDid, actor_id: &quot;sys.bpmn.open-smartphone-modem&quot;}" '
                 'target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-modem.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneModem.recordTypeApproval&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, authority: authority, '
                 'jurisdiction: jurisdictionIso3}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2565,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-modem/recordTypeApproval.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-recordTypeApproval-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-flagPatentBlocker-v1',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'open_smartphone_modem_flag_patent_blocker',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_modem_flag_patent_blocker" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-modem" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_modem_flag_patent_blocker" '
                 'name="flagPatentBlocker" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_smartphone_modem_sep_dep&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, modem_did: modemDid, '
                 'patent_no: patentNo, holder_did: holderDid, rat: rat, frand_declared: '
                 'frandDeclared, pool_id: poolId, expiry_date: expiryDate, blocker_status: '
                 '&quot;active&quot;, severity: severity, created_at: string(now()), owner_did: '
                 'callerDid, sensitivity_ord: 2, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-modem&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-modem.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneModem.flagPatentBlocker&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, patentNo: patentNo, '
                 'severity: severity}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2529,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-modem/flagPatentBlocker.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'did:web:open-smartphone-modem.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-flagPatentBlocker-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-fetchSepDelta-v1',
                 'did:web:open-smartphone-modem.gftd.ai:ops',
                 'open_smartphone_modem_fetch_sep_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_modem_fetch_sep_delta" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-modem" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_modem_fetch_sep_delta" name="fetchSepDelta" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="every '
                 '1d"><bpmn:outgoing>Flow_F</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle></bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" '
                 'name="manual"><bpmn:outgoing>Flow_FM</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_FM" sourceRef="Start_Manual" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_F" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch etsi ipr database">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://www.etsi.org/ipr-and-licensing/etsi-ipr-database&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:output source="=body" target="rawHtml"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_F</bpmn:incoming><bpmn:incoming>Flow_FM</bpmn:incoming><bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_Fetch" '
                 'targetRef="Task_Parse"/>\n'
                 '    <bpmn:serviceTask id="Task_Parse" name="extract sep declarations via llm">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.llm.json" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;Extract newly declared 5G/4G SEPs from: '
                 '&quot; + rawHtml" target="prompt"/>\n'
                 '          <zeebe:input source="={type: &quot;object&quot;, properties: {seps: '
                 '{type: &quot;array&quot;, items: {type: &quot;object&quot;, properties: '
                 '{patentNo: {type: &quot;string&quot;}, holder: {type: &quot;string&quot;}, rat: '
                 '{type: &quot;string&quot;}, frandDeclared: {type: &quot;boolean&quot;}}}}}}" '
                 'target="schema"/>\n'
                 '          <zeebe:output source="=result" target="parsed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_L</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Parse" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-modem.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneModem.fetchSepDelta&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={count: count(parsed.seps)}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3456,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-modem/fetchSepDelta.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-modem.gftd.ai:ops',
                 'did:web:open-smartphone-modem.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-fetchSepDelta-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-registerOsBuild-v1',
                 'did:web:open-smartphone-os.gftd.ai',
                 'open_smartphone_os_register_os_build',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_os_register_os_build" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_os_register_os_build" name="registerOsBuild" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_os_build&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, build_id: buildId, '
                 'os_name: osName, os_base: osBase, version: version, kernel_version: '
                 'kernelVersion, soc_support: socSupport, open_blobs_pct: openBlobsPct, '
                 'verified_boot: verifiedBoot, build_url: buildUrl, release_date: releaseDate, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-os&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-os.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneOs.registerOsBuild&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, osName: osName, version: '
                 'version}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2550,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-os/registerOsBuild.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-os.gftd.ai',
                 'did:web:open-smartphone-os.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-registerOsBuild-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-recordHalDriver-v1',
                 'did:web:open-smartphone-os.gftd.ai',
                 'open_smartphone_os_record_hal_driver',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_os_record_hal_driver" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_os_record_hal_driver" name="recordHalDriver" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_smartphone_os_hal_driver&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, driver_id: driverId, '
                 'os_did: osDid, soc_did: socDid, sensor_did: sensorDid, driver_type: driverType, '
                 'upstream_status: upstreamStatus, vendor_blobs_required: vendorBlobsRequired, '
                 'license: license, version: version, status: &quot;active&quot;, created_at: '
                 'string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, '
                 'user_id: callerDid, actor_id: &quot;sys.bpmn.open-smartphone-os&quot;}" '
                 'target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-os.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneOs.recordHalDriver&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, driverType: driverType, '
                 'upstreamStatus: upstreamStatus}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2557,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-os/recordHalDriver.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-os.gftd.ai',
                 'did:web:open-smartphone-os.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-recordHalDriver-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-trackOtaRelease-v1',
                 'did:web:open-smartphone-os.gftd.ai',
                 'open_smartphone_os_track_ota_release',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_os_track_ota_release" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_os_track_ota_release" name="trackOtaRelease" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_os_ota&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, ota_id: otaId, os_did: '
                 'osDid, from_version: fromVersion, to_version: toVersion, release_notes_url: '
                 'releaseNotesUrl, patch_level: patchLevel, cve_fixes: cveFixes, ota_size_mb: '
                 'otaSizeMb, signed: signed, release_date: releaseDate, status: '
                 '&quot;released&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-os&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-os.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneOs.trackOtaRelease&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, osDid: osDid, toVersion: '
                 'toVersion}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2547,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-os/trackOtaRelease.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-os.gftd.ai',
                 'did:web:open-smartphone-os.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-trackOtaRelease-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-fetchSecurityPatchDelta-v1',
                 'did:web:open-smartphone-os.gftd.ai:ops',
                 'open_smartphone_os_fetch_security_patch_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_os_fetch_security_patch_delta" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_os_fetch_security_patch_delta" '
                 'name="fetchSecurityPatchDelta" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch android bulletin">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={url: '
                 '&quot;https://source.android.com/docs/security/bulletin&quot;, method: '
                 '&quot;GET&quot;}" target="request"/>\n'
                 '          <zeebe:output source="=response.body" target="rawHtml"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_B</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_B" sourceRef="Task_Fetch" '
                 'targetRef="Task_LLM"/>\n'
                 '    <bpmn:serviceTask id="Task_LLM" name="extract patches">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;Extract latest Android/Linux mobile '
                 'security patches and CVE IDs from the bulletin page. List each patch with CVE '
                 'ID, severity, and affected Android version.&quot;" target="prompt"/>\n'
                 '          <zeebe:input source="=rawHtml" target="context"/>\n'
                 '          <zeebe:input source="={type: &quot;object&quot;, properties: {patches: '
                 '{type: &quot;array&quot;, items: {type: &quot;object&quot;, properties: {cveId: '
                 '{type: &quot;string&quot;}, severity: {type: &quot;string&quot;}, '
                 'affectedVersion: {type: &quot;string&quot;}, patchDate: {type: '
                 '&quot;string&quot;}}}}}}" target="schema"/>\n'
                 '          <zeebe:output source="=result" target="parsed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_B</bpmn:incoming><bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Task_LLM" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-os.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneOs.fetchSecurityPatchDelta&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={count: count(parsed.patches)}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3399,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-os/fetchSecurityPatchDelta.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-os.gftd.ai:ops',
                 'did:web:open-smartphone-os.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-fetchSecurityPatchDelta-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-recordLicensePool-v1',
                 'did:web:open-smartphone-patent.gftd.ai',
                 'open_smartphone_patent_record_license_pool',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_patent_record_license_pool" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-patent" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_patent_record_license_pool" '
                 'name="recordLicensePool" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_patent_pool&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, pool_id: poolId, '
                 'pool_name: poolName, administrator: administrator, standards_covered: '
                 'standardsCovered, member_count: memberCount, license_fee_usd_per_unit: '
                 'licenseFeeUsdPerUnit, frand_compliant: frandCompliant, url: url, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-patent&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-patent.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphonePatent.recordLicensePool&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, poolName: poolName}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2560,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-patent/recordLicensePool.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-patent.gftd.ai',
                 'did:web:open-smartphone-patent.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-recordLicensePool-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-mapPatentDependency-v1',
                 'did:web:open-smartphone-patent.gftd.ai',
                 'open_smartphone_patent_map_patent_dependency',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_patent_map_patent_dependency" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-patent" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_patent_map_patent_dependency" '
                 'name="mapPatentDependency" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_patent_dep&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, dep_id: depId, '
                 'component_type: componentType, component_did: componentDid, patent_no: patentNo, '
                 'holder_did: holderDid, standard: standard, dependency_type: dependencyType, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 2, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-patent&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-patent.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphonePatent.mapPatentDependency&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, patentNo: patentNo, '
                 'componentType: componentType}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2546,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-patent/mapPatentDependency.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-patent.gftd.ai',
                 'did:web:open-smartphone-patent.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-mapPatentDependency-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-flagExpiryGate-v1',
                 'did:web:open-smartphone-patent.gftd.ai:ops',
                 'open_smartphone_patent_flag_expiry_gate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_patent_flag_expiry_gate" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-patent" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_patent_flag_expiry_gate" '
                 'name="flagExpiryGate" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Select"/>\n'
                 '    <bpmn:serviceTask id="Task_Select" name="query expiring SEPs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, patent_no, holder_did, '
                 'rat, expiry_date FROM vertex_open_smartphone_patent_sep WHERE blocker_status = '
                 '&apos;active&apos; AND expiry_date IS NOT NULL ORDER BY expiry_date ASC LIMIT '
                 '200&quot;" target="query"/>\n'
                 '          <zeebe:output source="=rows" target="expiring"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Select" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-patent.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphonePatent.flagExpiryGate&quot;" target="action"/>\n'
                 '          <zeebe:input source="={expiringCount: count(expiring)}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2402,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-patent/flagExpiryGate.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-patent.gftd.ai:ops',
                 'did:web:open-smartphone-patent.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-flagExpiryGate-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-fetchSepLandscapeDelta-v1',
                 'did:web:open-smartphone-patent.gftd.ai:ops',
                 'open_smartphone_patent_fetch_sep_landscape_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_patent_fetch_sep_landscape_delta" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-patent" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_patent_fetch_sep_landscape_delta" '
                 'name="fetchSepLandscapeDelta" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch ETSI IPR DB">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={url: '
                 '&quot;https://www.etsi.org/intellectual-property-rights/ipr-database&quot;, '
                 'method: &quot;GET&quot;}" target="request"/>\n'
                 '          <zeebe:output source="=response.body" target="rawHtml"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_B</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_B" sourceRef="Task_Fetch" '
                 'targetRef="Task_LLM"/>\n'
                 '    <bpmn:serviceTask id="Task_LLM" name="extract SEPs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;Extract newly declared Standard Essential '
                 'Patents (SEPs) for 4G LTE, 5G NR, Wi-Fi (802.11), Bluetooth from the ETSI IPR '
                 'database. Include patent number, holder company, applicable standard, and FRAND '
                 'declaration status.&quot;" target="prompt"/>\n'
                 '          <zeebe:input source="=rawHtml" target="context"/>\n'
                 '          <zeebe:input source="={type: &quot;object&quot;, properties: {seps: '
                 '{type: &quot;array&quot;, items: {type: &quot;object&quot;, properties: '
                 '{patentNo: {type: &quot;string&quot;}, holder: {type: &quot;string&quot;}, '
                 'standard: {type: &quot;string&quot;}, cpcCodes: {type: &quot;array&quot;, items: '
                 '{type: &quot;string&quot;}}, frandDeclared: {type: &quot;boolean&quot;}, '
                 'expiryYear: {type: &quot;integer&quot;}}}}}}" target="schema"/>\n'
                 '          <zeebe:output source="=result" target="parsed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_B</bpmn:incoming><bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Task_LLM" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-patent.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphonePatent.fetchSepLandscapeDelta&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={count: count(parsed.seps)}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3588,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-patent/fetchSepLandscapeDelta.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-patent.gftd.ai:ops',
                 'did:web:open-smartphone-patent.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-fetchSepLandscapeDelta-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-registerSensor-v1',
                 'did:web:open-smartphone-sensor.gftd.ai',
                 'open_smartphone_sensor_register_sensor',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_registerSensor" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-sensor" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_sensor_register_sensor" '
                 'name="open.smartphoneSensor.registerSensor" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_smartphone_sensor_module&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, sensor_id: sensorId, '
                 'sensor_type: sensorType, vendor: vendor, model: model, interface_type: '
                 'interfaceType, open_driver: openDriver, mainline_kernel_status: '
                 'mainlineKernelStatus, pixel_count_mp: pixelCountMp, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-sensor&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-sensor.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneSensor.registerSensor&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2493,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-sensor/registerSensor.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-sensor.gftd.ai',
                 'did:web:open-smartphone-sensor.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-registerSensor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-recordCalibration-v1',
                 'did:web:open-smartphone-sensor.gftd.ai',
                 'open_smartphone_sensor_record_calibration',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_recordCalibration" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-sensor" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_sensor_record_calibration" '
                 'name="open.smartphoneSensor.recordCalibration" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_smartphone_sensor_calibration&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, sensor_did: sensorDid, '
                 'calibration_type: calibrationType, standard_ref: standardRef, calibrated_at: '
                 'calibratedAt, valid_until: validUntil, calibrated_by: calibratedBy, pass: pass, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-sensor&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-sensor.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneSensor.recordCalibration&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2482,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-sensor/recordCalibration.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-sensor.gftd.ai',
                 'did:web:open-smartphone-sensor.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-recordCalibration-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-fetchDriverAvailability-v1',
                 'did:web:open-smartphone-sensor.gftd.ai:ops',
                 'open_smartphone_sensor_fetch_driver_availability',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_fetchDriverAvailability" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-sensor" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_sensor_fetch_driver_availability" '
                 'name="open.smartphoneSensor.fetchDriverAvailability" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch driver data">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;https://cateee.net/lkddb/web-lkddb/&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:output source="=response" target="rawData"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_B</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_B" sourceRef="Task_Fetch" '
                 'targetRef="Task_LLM"/>\n'
                 '    <bpmn:serviceTask id="Task_LLM" name="classify drivers">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;Classify mainline Linux driver '
                 'availability for mobile sensors from: &quot; + rawData" target="prompt"/>\n'
                 '          <zeebe:input source="={type: &quot;object&quot;, properties: {drivers: '
                 '{type: &quot;array&quot;, items: {type: &quot;object&quot;, properties: '
                 '{sensorType: {type: &quot;string&quot;}, driverName: {type: &quot;string&quot;}, '
                 'kernelVersion: {type: &quot;string&quot;}, mainlined: {type: '
                 '&quot;boolean&quot;}}}}}}" target="schema"/>\n'
                 '          <zeebe:output source="=result" target="parsed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_B</bpmn:incoming><bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Task_LLM" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-sensor.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneSensor.fetchDriverAvailability&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={count: count(parsed.drivers)}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3263,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-sensor/fetchDriverAvailability.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-sensor.gftd.ai:ops',
                 'did:web:open-smartphone-sensor.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-fetchDriverAvailability-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-dailyPulse-v1',
                 'did:web:open-smartphone-sensor.gftd.ai:ops',
                 'open_smartphone_sensor_daily_pulse',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_dailyPulse" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-sensor" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_sensor_daily_pulse" '
                 'name="open.smartphoneSensor.dailyPulse" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Stats"/>\n'
                 '    <bpmn:serviceTask id="Task_Stats" name="query stats">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT count(*) as total, sum(case when '
                 'open_driver then 1 else 0 end) as open_count FROM '
                 'vertex_open_smartphone_sensor_module WHERE status=&#39;active&#39;&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:output source="=rows" target="stats"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Stats" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:open-smartphone-sensor.gftd.ai&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneSensor.dailyPulse&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={total: stats[1].total, openCount: '
                 'stats[1].open_count}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2328,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-sensor/dailyPulse.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-sensor.gftd.ai:ops',
                 'did:web:open-smartphone-sensor.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-dailyPulse-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-registerChipDesign-v1',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'open_smartphone_soc_register_chip_design',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_soc_register_chip_design" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-soc" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_soc_register_chip_design" '
                 'name="registerChipDesign" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openSmartphoneSoc.registerChipDesign", "version": '
                 '1, "resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save chip design">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_smartphone_soc_design&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, chip_id: chipId, '
                 'chip_name: chipName, isa: isa, process_node_nm: processNodeNm, die_area_mm2: '
                 'dieAreaMm2, transistor_count_b: transistorCountB, open_source_rtl: '
                 'openSourceRtl, rtl_license: rtlLicense, fab_did: fabDid, tape_out_date: '
                 'tapeOutDate, status: &quot;active&quot;, created_at: string(now()), owner_did: '
                 'callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-soc&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-soc.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneSoc.registerChipDesign&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, chipId: chipId, isa: isa}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2747,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-soc/registerChipDesign.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-registerChipDesign-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-trackFabOrder-v1',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'open_smartphone_soc_track_fab_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_soc_track_fab_order" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-soc" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_soc_track_fab_order" name="trackFabOrder" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openSmartphoneSoc.trackFabOrder", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save fab order">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_smartphone_soc_fab_order&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, order_id: orderId, '
                 'chip_did: chipDid, fab_did: fabDid, process_node_nm: processNodeNm, wafer_qty: '
                 'waferQty, delivery_estimate: deliveryEstimate, price_usd_k: priceUsdK, '
                 'order_status: &quot;placed&quot;, created_at: string(now()), owner_did: '
                 'callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-soc&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-soc.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.smartphoneSoc.trackFabOrder&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, orderId: orderId, chipDid: '
                 'chipDid}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2662,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-soc/trackFabOrder.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-trackFabOrder-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-flagExportControl-v1',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'open_smartphone_soc_flag_export_control',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_soc_flag_export_control" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-soc" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_soc_flag_export_control" '
                 'name="flagExportControl" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_smartphone_soc_export_flag&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, chip_did: chipDid, '
                 'flag_type: flagType, entity_list_entry: entityListEntry, jurisdiction: '
                 'jurisdiction, flagged_at: string(now()), severity: severity, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 2, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-smartphone-soc&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-soc.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneSoc.flagExportControl&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, chipDid: chipDid, severity: '
                 'severity}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2492,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-soc/flagExportControl.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'did:web:open-smartphone-soc.gftd.ai',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-flagExportControl-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-fetchRiscvEcosystemDelta-v1',
                 'did:web:open-smartphone-soc.gftd.ai:ops',
                 'open_smartphone_soc_fetch_riscv_ecosystem_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_smartphone_soc_fetch_riscv_ecosystem_delta" '
                 'targetNamespace="https://gftd.ai/bpmn/open-smartphone-soc" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_smartphone_soc_fetch_riscv_ecosystem_delta" '
                 'name="fetchRiscvEcosystemDelta" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openSmartphoneSoc.fetchRiscvEcosystemDelta", '
                 '"version": 1, "resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/P7D: fires every Monday at 06:00 UTC -->\n'
                 '    <bpmn:startEvent id="Start" name="weekly Monday 06:00">\n'
                 '      <bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_weekly">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" '
                 'name="manual"><bpmn:outgoing>Flow_CM</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_CM" sourceRef="Start_Manual" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '\n'
                 '    <!-- Step 1: fetch RISC-V exchange JSON feed -->\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch riscv.org exchange">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://riscv.org/exchange/?format=json&quot;" target="url"/>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:input source="=30" target="timeoutSec"/>\n'
                 '          <zeebe:output source="=bodyText" target="responseBody"/>\n'
                 '          <zeebe:output source="=status"   target="fetchStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_C</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_CM</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_Fetch" '
                 'targetRef="Task_Parse"/>\n'
                 '\n'
                 '    <!-- Step 2: extract new RISC-V chip releases via LLM structured output -->\n'
                 '    <bpmn:serviceTask id="Task_Parse" name="LLM extract releases">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;classifier&quot;" target="tier"/>\n'
                 '          <zeebe:input source="=&quot;You are a RISC-V ecosystem analyst. '
                 'Extract new chip releases from the provided content. Output ONE JSON object '
                 'matching the schema exactly. JSON only, no prose.&quot;" target="system"/>\n'
                 '          <zeebe:input source="=&quot;Extract new RISC-V chip releases from: '
                 '&quot; + responseBody" target="user"/>\n'
                 '          <zeebe:input source="={type: &quot;object&quot;, properties: '
                 '{releases: {type: &quot;array&quot;, items: {type: &quot;object&quot;, '
                 'properties: {name: {type: &quot;string&quot;}, vendor: {type: '
                 '&quot;string&quot;}, processNm: {type: &quot;integer&quot;}, openRtl: {type: '
                 '&quot;boolean&quot;}}}}}}" target="schema"/>\n'
                 '          <zeebe:input source="=1000" target="maxTokens"/>\n'
                 '          <zeebe:input source="=0.1" target="temperature"/>\n'
                 '          <zeebe:output source="=ok"        target="llmOk"/>\n'
                 '          <zeebe:output source="=data"      target="parsed"/>\n'
                 '          <zeebe:output source="=model"     target="llmModel"/>\n'
                 '          <zeebe:output source="=latencyMs" target="llmLatencyMs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_L</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Parse" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <!-- Step 3: emit audit event with release count -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-smartphone-soc.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.smartphoneSoc.fetchRiscvEcosystemDelta&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={count: count(parsed.releases), fetchStatus: '
                 'fetchStatus, llmOk: llmOk, llmModel: llmModel}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_A</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4785,
                 '00-contracts/bpmn/ai/gftd/open-smartphone-soc/fetchRiscvEcosystemDelta.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:open-smartphone-soc.gftd.ai:ops',
                 'did:web:open-smartphone-soc.gftd.ai:ops',
                 'sys.bpmn.seed.open-smartphone',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-fetchRiscvEcosystemDelta-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-recordBomLine-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-assembleBom-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-recordAlternativeSource-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-bom-computeOpenScore-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-registerFacility-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-recordCapacityOrder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-fetchComplianceDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-ems-dailyPulse-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-recordModemSpec-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-recordTypeApproval-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-flagPatentBlocker-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-modem-fetchSepDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-registerOsBuild-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-recordHalDriver-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-trackOtaRelease-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-os-fetchSecurityPatchDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-recordLicensePool-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-mapPatentDependency-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-flagExpiryGate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-patent-fetchSepLandscapeDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-registerSensor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-recordCalibration-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-fetchDriverAvailability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-sensor-dailyPulse-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-registerChipDesign-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-trackFabOrder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-flagExportControl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-smartphone-soc-fetchRiscvEcosystemDelta-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
