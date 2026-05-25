"""Captured from Kysely migration 20260428230100_seed_open_cyber_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428230100_seed_open_cyber_bpmn_actors"
down_revision = 'r_20260428230000_vertex_business_person_career_skill'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-record-cve-disclosure-v1',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'open_cyber_vuln_cve',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_vuln_cve" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-vuln" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_vuln_cve" name="CVE 開示" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="cve">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_vuln_cve&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, cve_id: cveId, product: '
                 'product, vendor: vendor, cvss_v3_score: cvssV3Score, cvss_v3_vector: '
                 'cvssV3Vector, exploit_available: exploitAvailable, in_the_wild: inTheWild, '
                 'severity_tier: if cvssV3Score &gt;= 9.0 then &quot;critical&quot; else if '
                 'cvssV3Score &gt;= 7.0 then &quot;high&quot; else if cvssV3Score &gt;= 4.0 then '
                 '&quot;medium&quot; else &quot;low&quot;, require_emergency_patch: cvssV3Score '
                 '&gt;= 9.0 or inTheWild = true, published_at: publishedAt, status: '
                 '&quot;published&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-vuln&quot;}" target="values"/>\n'
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
                 '          <zeebe:input source="=&quot;did:web:open-cyber-vuln.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberVuln.cve.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, cveId: cveId, cvssV3Score: '
                 'cvssV3Score}" target="payload"/>\n'
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
                 2719,
                 '00-contracts/bpmn/ai/gftd/open-cyber-vuln/recordCveDisclosure.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-record-cve-disclosure-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-record-patch-advisory-v1',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'open_cyber_vuln_patch',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_vuln_patch" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-vuln" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_vuln_patch" name="Patch advisory" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="patch">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_vuln_patch&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, advisory_id: advisoryId, '
                 'cve_id: cveId, vendor: vendor, product: product, fixed_version: fixedVersion, '
                 'urgency: urgency, workaround_available: workaroundAvailable, issued_at: '
                 'issuedAt, status: &quot;issued&quot;, created_at: string(now()), owner_did: '
                 'callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-vuln&quot;}" target="values"/>\n'
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
                 '          <zeebe:input source="=&quot;did:web:open-cyber-vuln.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberVuln.patch.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, advisoryId: advisoryId, '
                 'vendor: vendor, product: product}" target="payload"/>\n'
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
                 2476,
                 '00-contracts/bpmn/ai/gftd/open-cyber-vuln/recordPatchAdvisory.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-record-patch-advisory-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-link-exploit-to-actor-v1',
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
                 '&quot;app.etzhayyim.apps.cyberVuln.linkExploitToActor&quot;,\n'
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
                 '00-contracts/bpmn/ai/gftd/open-cyber-vuln/linkExploitToActor.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-link-exploit-to-actor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-record-assignment-v1',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'open_cve_cna_record_assignment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cve_cna_record_assignment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cve-cna" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cve_cna_record_assignment" name="recordAssignment" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input source="=&quot;vertex_open_cve_cna&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, cve_id: cveId, '
                 'cna_lei: cnaLei, product_category: productCategory, cvss_base: cvssBase, '
                 'assigner_process: assignerProcess, patch_lag_vid: patchLagVid, assigned_at: '
                 'assignedAt, status: &quot;active&quot;, created_at: string(now()), owner_did: '
                 'callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cve-cna&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-cve-cna.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;open.cveCna.recordAssignment&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2309,
                 '00-contracts/bpmn/ai/gftd/open-cve-cna/recordAssignment.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-record-assignment-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-disclosure-gap-v1',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'open_cve_cna_flag_disclosure_gap',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cve_cna_flag_disclosure_gap" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cve-cna" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cve_cna_flag_disclosure_gap" name="flagDisclosureGap" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input source="=&quot;vertex_open_cve_cna&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, flag_id: flagId, '
                 'cve_vid: cveVid, gap_kind: gapKind, days_embargo_to_disclose: '
                 'daysEmbargoToDisclose, reported_at: reportedAt, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: &quot;sys.bpmn.open-cve-cna&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-cve-cna.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;open.cveCna.flagDisclosureGap&quot;" '
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
                 '</bpmn:definitions>',
                 2266,
                 '00-contracts/bpmn/ai/gftd/open-cve-cna/flagDisclosureGap.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-disclosure-gap-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-weaponized-cve-v1',
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
                 '&quot;app.etzhayyim.apps.cveCna.flagWeaponizedCve&quot;,\n'
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
                 '00-contracts/bpmn/ai/gftd/open-cve-cna/flagWeaponizedCve.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-weaponized-cve-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-kev-catalog-record-entry-v1',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'open_kev_catalog_record_entry',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_kev_catalog_record_entry" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-kev-catalog" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_kev_catalog_record_entry" name="recordEntry" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_kev_catalog&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, entry_id: entryId, cve_id: cveId, '
                 'product_category: productCategory, exploitation_maturity: exploitationMaturity, '
                 'disclosure_gap_vid: disclosureGapVid, due_date: dueDate, added_at: addedAt, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-kev-catalog&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-kev-catalog.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input source="=&quot;open.kevCatalog.recordEntry&quot;" '
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
                 '</bpmn:definitions>',
                 2331,
                 '00-contracts/bpmn/ai/gftd/open-kev-catalog/recordEntry.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-kev-catalog-record-entry-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-kev-catalog-flag-remediation-lag-v1',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'open_kev_catalog_flag_remediation_lag',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_kev_catalog_flag_remediation_lag" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-kev-catalog" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_kev_catalog_flag_remediation_lag" '
                 'name="flagRemediationLag" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_kev_catalog&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, flag_id: flagId, entry_vid: entryVid, lag_kind: '
                 'lagKind, days_past_due: daysPastDue, reported_at: reportedAt, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-kev-catalog&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-kev-catalog.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.kevCatalog.flagRemediationLag&quot;" '
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
                 '</bpmn:definitions>',
                 2281,
                 '00-contracts/bpmn/ai/gftd/open-kev-catalog/flagRemediationLag.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-kev-catalog-flag-remediation-lag-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-oss-vuln-register-advisory-v1',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'open_oss_vuln_register_advisory',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_oss_vuln_register_advisory" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-oss-vuln" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_oss_vuln_register_advisory" name="registerAdvisory" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input source="=&quot;vertex_open_oss_vuln&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, advisory_id: '
                 'advisoryId, scheme: scheme, cvss3_score: cvss3Score, cvss4_score: cvss4Score, '
                 'epss_pct: epssPct, cwe_id: cweId, affected_ecosystem: affectedEcosystem, '
                 'affected_package: affectedPackage, version_ranges: versionRanges, kev_tagged: '
                 'kevTagged, published_at: publishedAt, risk_tier: if kevTagged = true or '
                 '(cvss4Score != null and cvss4Score &gt;= 9) or (cvss3Score != null and '
                 'cvss3Score &gt;= 9) then &quot;critical&quot; else if (cvss4Score != null and '
                 'cvss4Score &gt;= 7) or (cvss3Score != null and cvss3Score &gt;= 7) then '
                 '&quot;high&quot; else if (cvss4Score != null and cvss4Score &gt;= 4) or '
                 '(cvss3Score != null and cvss3Score &gt;= 4) then &quot;medium&quot; else '
                 '&quot;low&quot;, status: &quot;active&quot;, created_at: string(now()), '
                 'owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, '
                 'actor_id: &quot;sys.bpmn.open-oss-vuln&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-oss-vuln.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;open.ossVuln.registerAdvisory&quot;" '
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
                 '</bpmn:definitions>',
                 2837,
                 '00-contracts/bpmn/ai/gftd/open-oss-vuln/registerAdvisory.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-oss-vuln-register-advisory-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-oss-vuln-record-sbom-match-v1',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'open_oss_vuln_record_sbom_match',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_oss_vuln_record_sbom_match" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-oss-vuln" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_oss_vuln_record_sbom_match" name="recordSbomMatch" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input source="=&quot;vertex_open_oss_vuln&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, match_id: matchId, '
                 'advisory_vid: advisoryVid, operator_lei: operatorLei, product_name: productName, '
                 'sbom_format: sbomFormat, component_count: componentCount, affected_components: '
                 'affectedComponents, remediation_status: remediationStatus, matched_at: '
                 'matchedAt, status: &quot;active&quot;, created_at: string(now()), owner_did: '
                 'callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-oss-vuln&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-oss-vuln.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;open.ossVuln.recordSbomMatch&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2399,
                 '00-contracts/bpmn/ai/gftd/open-oss-vuln/recordSbomMatch.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-oss-vuln-record-sbom-match-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-record-threat-actor-v1',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'open_cyber_threat_actor',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_threat_actor" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-threat" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_threat_actor" name="Threat actor" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="actor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_threat_actor&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, actor_id_code: '
                 'actorIdCode, actor_name: actorName, aliases: aliases, attribution: attribution, '
                 'suspected_nexus: suspectedNexus, primary_motivation: primaryMotivation, '
                 'capability_tier: if attribution = &quot;state&quot; then '
                 '&quot;nation-state-top-tier&quot; else if attribution = &quot;criminal&quot; and '
                 'primaryMotivation = &quot;financial&quot; then &quot;advanced&quot; else if '
                 'primaryMotivation = &quot;espionage&quot; then &quot;competent&quot; else if '
                 'attribution = &quot;hacktivist&quot; then &quot;emerging&quot; else '
                 '&quot;script-kiddie&quot;, first_observed: firstObserved, status: '
                 '&quot;tracked&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 2, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-threat&quot;}" target="values"/>\n'
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
                 '          <zeebe:input source="=&quot;did:web:open-cyber-threat.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberThreat.actor.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, actorIdCode: actorIdCode, '
                 'attribution: attribution}" target="payload"/>\n'
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
                 2882,
                 '00-contracts/bpmn/ai/gftd/open-cyber-threat/recordThreatActor.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-record-threat-actor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-assess-threat-actor-v1',
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
                 '&quot;app.etzhayyim.apps.cyberThreat.assessThreatActor&quot;,\n'
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
                 '00-contracts/bpmn/ai/gftd/open-cyber-threat/assessThreatActor.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-assess-threat-actor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-record-campaign-v1',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'open_cyber_threat_campaign',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_threat_campaign" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-threat" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_threat_campaign" name="Campaign+TTP" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="campaign">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_threat_campaign&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, campaign_id: campaignId, '
                 'threat_actor_code: threatActorCode, target_sector: targetSector, target_country: '
                 'targetCountry, mitre_tactics: mitreTactics, mitre_techniques: mitreTechniques, '
                 'start_observed: startObserved, end_observed: endObserved, impact_tier: if '
                 'targetSector = &quot;critical-infrastructure&quot; or targetSector = '
                 '&quot;govt&quot; then &quot;systemic&quot; else if targetCountry = null then '
                 '&quot;global&quot; else &quot;regional&quot;, status: &quot;tracked&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 2, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-threat&quot;}" target="values"/>\n'
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
                 '          <zeebe:input source="=&quot;did:web:open-cyber-threat.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberThreat.campaign.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, campaignId: campaignId, '
                 'threatActorCode: threatActorCode}" target="payload"/>\n'
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
                 2770,
                 '00-contracts/bpmn/ai/gftd/open-cyber-threat/recordCampaign.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-record-campaign-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-report-incident-v1',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'open_cyber_incident_report',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_incident_report" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-incident" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_incident_report" name="Cyber incident" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="report">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_incident_report&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, incident_id: incidentId, '
                 'victim_org_id: victimOrgId, sector: sector, attack_vector: attackVector, '
                 'impact_type: impactType, affected_systems: affectedSystems, data_exposed: '
                 'dataExposed, ransom_demanded_usd: ransomDemandedUsd, casualties: casualties, '
                 'severity: if casualties &gt;= 1 or impactType = &quot;wiper&quot; or '
                 '(ransomDemandedUsd != null and ransomDemandedUsd &gt;= 1000000) then '
                 '&quot;critical&quot; else if list '
                 'contains([&quot;data-breach&quot;,&quot;service-disruption&quot;,&quot;ransomware&quot;], '
                 'impactType) or (ransomDemandedUsd != null and ransomDemandedUsd &gt;= 100000) '
                 'then &quot;high&quot; else if impactType = &quot;espionage&quot; then '
                 '&quot;medium&quot; else &quot;low&quot;, require_regulatory_notice: casualties '
                 '&gt;= 1 or impactType = &quot;wiper&quot; or list '
                 'contains([&quot;data-breach&quot;,&quot;service-disruption&quot;,&quot;ransomware&quot;], '
                 'impactType), detected_at: detectedAt, reported_at: reportedAt, status: '
                 '&quot;reported&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 2, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-incident&quot;}" target="values"/>\n'
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
                 '          <zeebe:input source="=&quot;did:web:open-cyber-incident.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberIncident.incident.report&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, incidentId: incidentId, '
                 'impactType: impactType, casualties: casualties}" target="payload"/>\n'
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
                 3283,
                 '00-contracts/bpmn/ai/gftd/open-cyber-incident/reportIncident.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-report-incident-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-record-i-o-c-v1',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'open_cyber_incident_ioc',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_incident_ioc" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-incident" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_incident_ioc" name="IOC 記録" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="ioc">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_incident_ioc&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, ioc_id: iocId, '
                 'incident_vid: incidentVid, ioc_type: iocType, value: value, context: context, '
                 'confidence: confidence, tlp: tlp, first_seen_at: firstSeenAt, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 2, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-incident&quot;}" target="values"/>\n'
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
                 '          <zeebe:input source="=&quot;did:web:open-cyber-incident.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberIncident.ioc.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, iocId: iocId, iocType: '
                 'iocType}" target="payload"/>\n'
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
                 2434,
                 '00-contracts/bpmn/ai/gftd/open-cyber-incident/recordIOC.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-record-i-o-c-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-link-incident-to-treaty-v1',
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
                 '&quot;app.etzhayyim.apps.cyberIncident.linkIncidentToTreaty&quot;,\n'
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
                 '00-contracts/bpmn/ai/gftd/open-cyber-incident/linkIncidentToTreaty.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-link-incident-to-treaty-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-compliance-record-isms-audit-v1',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'open_cyber_compliance_isms',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_compliance_isms" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-compliance" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_compliance_isms" name="ISMS audit" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="isms">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_compliance_isms&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, audit_id: auditId, '
                 'org_lei: orgLei, framework: framework, assessment_date: assessmentDate, '
                 'findings_high: findingsHigh, findings_medium: findingsMedium, findings_low: '
                 'findingsLow, pass_fail: passFail, certification_tier: if passFail = '
                 '&quot;pass&quot; and (findingsHigh = null or findingsHigh = 0) then '
                 '&quot;certified&quot; else if passFail = &quot;pass&quot; or passFail = '
                 '&quot;conditional-pass&quot; then &quot;provisional&quot; else if (findingsHigh '
                 '!= null and findingsHigh &gt;= 1) and passFail = &quot;fail&quot; then '
                 '&quot;remediation-required&quot; else &quot;failed&quot;, expires_at: expiresAt, '
                 'status: &quot;recorded&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-compliance&quot;}" target="values"/>\n'
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
                 'source="=&quot;did:web:open-cyber-compliance.etzhayyim.com&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberCompliance.isms.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, auditId: auditId, '
                 'framework: framework, passFail: passFail}" target="payload"/>\n'
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
                 2935,
                 '00-contracts/bpmn/ai/gftd/open-cyber-compliance/recordIsmsAudit.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-compliance-record-isms-audit-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-compliance-record-regulatory-reporting-v1',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'open_cyber_compliance_regulatory',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_compliance_regulatory" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-compliance" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_compliance_regulatory" name="Regulatory filing" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="regulatory">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_cyber_compliance_regulatory&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, filing_id: filingId, '
                 'regulator: regulator, filer_lei: filerLei, incident_vid: incidentVid, '
                 'filing_type: filingType, deadline_hours: deadlineHours, filed_within_deadline: '
                 'filedWithinDeadline, timeliness_tier: if filedWithinDeadline = true then '
                 '&quot;on-time&quot; else if deadlineHours != null and deadlineHours &gt;= 168 '
                 'then &quot;late&quot; else if deadlineHours != null and deadlineHours &gt;= 336 '
                 'then &quot;significantly-late&quot; else &quot;non-reported&quot;, filed_at: '
                 'filedAt, status: &quot;submitted&quot;, created_at: string(now()), owner_did: '
                 'callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-compliance&quot;}" target="values"/>\n'
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
                 'source="=&quot;did:web:open-cyber-compliance.etzhayyim.com&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;openCyberCompliance.regulatory.record&quot;" target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, filingId: filingId, '
                 'regulator: regulator, filingType: filingType}" target="payload"/>\n'
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
                 2859,
                 '00-contracts/bpmn/ai/gftd/open-cyber-compliance/recordRegulatoryReporting.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-compliance-record-regulatory-reporting-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-record-soc-alert-v1',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'open_cyber_soc_alert',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_soc_alert" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-soc" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_soc_alert" name="SOC alert" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="alert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_soc_alert&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, alert_id: alertId, '
                 'source_siem: sourceSiem, detection_rule: detectionRule, severity: severity, '
                 'triage_tier: if severity = &quot;critical&quot; then &quot;flash&quot; else if '
                 'severity = &quot;high&quot; then &quot;priority&quot; else if list '
                 'contains([&quot;medium&quot;,&quot;low&quot;], severity) then '
                 '&quot;routine&quot; else &quot;auto-close&quot;, fired_at: firedAt, triaged_at: '
                 'triagedAt, false_positive: falsePositive, status: &quot;triaged&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 2, org_id: '
                 'callerDid, user_id: callerDid, actor_id: &quot;sys.bpmn.open-cyber-soc&quot;}" '
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
                 '          <zeebe:input source="=&quot;did:web:open-cyber-soc.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberSoc.alert.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, alertId: alertId, '
                 'sourceSiem: sourceSiem, severity: severity}" target="payload"/>\n'
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
                 2709,
                 '00-contracts/bpmn/ai/gftd/open-cyber-soc/recordSocAlert.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-record-soc-alert-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-record-incident-response-v1',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'open_cyber_soc_ir',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_soc_ir" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-soc" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_soc_ir" name="IR workflow" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="ir">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_cyber_soc_ir&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, ir_id: irId, alert_vid: '
                 'alertVid, playbook: playbook, mttr_minutes: mttrMinutes, containment_achieved: '
                 'containmentAchieved, eradication_achieved: eradicationAchieved, '
                 'effectiveness_tier: if containmentAchieved = true and eradicationAchieved = true '
                 'and (mttrMinutes != null and mttrMinutes &lt;= 60) then &quot;excellent&quot; '
                 'else if containmentAchieved = true and eradicationAchieved = true then '
                 '&quot;effective&quot; else if containmentAchieved = true then '
                 '&quot;acceptable&quot; else if mttrMinutes != null and mttrMinutes &gt;= 720 '
                 'then &quot;delayed&quot; else &quot;ineffective&quot;, started_at: startedAt, '
                 'closed_at: closedAt, status: &quot;closed&quot;, created_at: string(now()), '
                 'owner_did: callerDid, sensitivity_ord: 2, org_id: callerDid, user_id: callerDid, '
                 'actor_id: &quot;sys.bpmn.open-cyber-soc&quot;}" target="values"/>\n'
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
                 '          <zeebe:input source="=&quot;did:web:open-cyber-soc.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openCyberSoc.ir.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, irId: irId, mttrMinutes: '
                 'mttrMinutes}" target="payload"/>\n'
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
                 2881,
                 '00-contracts/bpmn/ai/gftd/open-cyber-soc/recordIncidentResponse.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-record-incident-response-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-escalate-state-apt-v1',
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
                 '&quot;app.etzhayyim.apps.cyberSoc.escalateStateApt&quot;,\n'
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
                 '00-contracts/bpmn/ai/gftd/open-cyber-soc/escalateStateApt.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-escalate-state-apt-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-resilience-stress-record-stress-test-v1',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'open_cyber_resilience_stress_record_stress_test',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_resilience_stress_record_stress_test" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-resilience-stress" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_resilience_stress_record_stress_test" '
                 'name="recordStressTest" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_cyber_resilience_stress&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, test_id: testId, '
                 'entity_lei: entityLei, regime: regime, entity_category: entityCategory, '
                 'test_type: testType, provider_lei: providerLei, scenarios_executed: '
                 'scenariosExecuted, completed_at: completedAt, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-resilience-stress&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-cyber-resilience-stress.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.cyberResilienceStress.recordStressTest&quot;" '
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
                 '</bpmn:definitions>',
                 2449,
                 '00-contracts/bpmn/ai/gftd/open-cyber-resilience-stress/recordStressTest.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-resilience-stress-record-stress-test-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-resilience-stress-report-resilience-gap-v1',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'open_cyber_resilience_stress_report_resilience_gap',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_cyber_resilience_stress_report_resilience_gap" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-cyber-resilience-stress" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_cyber_resilience_stress_report_resilience_gap" '
                 'name="reportResilienceGap" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_cyber_resilience_stress&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, gap_id: gapId, '
                 'test_vid: testVid, gap_category: gapCategory, severity: severity, '
                 'mitigation_due_at: mitigationDueAt, reported_at: reportedAt, rpo_rto_tier: if '
                 'severity = &quot;critical&quot; then &quot;rpo_zero&quot; else if severity = '
                 '&quot;high&quot; then &quot;rto_same_day&quot; else &quot;rto_flexible&quot;, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-cyber-resilience-stress&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-cyber-resilience-stress.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.cyberResilienceStress.reportResilienceGap&quot;" '
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
                 '</bpmn:definitions>',
                 2572,
                 '00-contracts/bpmn/ai/gftd/open-cyber-resilience-stress/reportResilienceGap.bpmn',
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-resilience-stress-report-resilience-gap-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-recordCveDisclosure-v1',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberVuln.recordCveDisclosure',
                 'open_cyber_vuln_cve',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-recordCveDisclosure-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-recordPatchAdvisory-v1',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberVuln.recordPatchAdvisory',
                 'open_cyber_vuln_patch',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-recordPatchAdvisory-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-linkExploitToActor-v1',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberVuln.linkExploitToActor',
                 'open_cyber_vuln_link_exploit_to_actor',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'did:web:open-cyber-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-linkExploitToActor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-recordAssignment-v1',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cveCna.recordAssignment',
                 'open_cve_cna_record_assignment',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-recordAssignment-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-flagDisclosureGap-v1',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cveCna.flagDisclosureGap',
                 'open_cve_cna_flag_disclosure_gap',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-flagDisclosureGap-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-flagWeaponizedCve-v1',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cveCna.flagWeaponizedCve',
                 'open_cve_cna_flag_weaponized_cve',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'did:web:open-cve-cna.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-flagWeaponizedCve-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-kev-catalog-recordEntry-v1',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'app.etzhayyim.apps.kevCatalog.recordEntry',
                 'open_kev_catalog_record_entry',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-kev-catalog-recordEntry-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-kev-catalog-flagRemediationLag-v1',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'app.etzhayyim.apps.kevCatalog.flagRemediationLag',
                 'open_kev_catalog_flag_remediation_lag',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'did:web:open-kev-catalog.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-kev-catalog-flagRemediationLag-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-oss-vuln-registerAdvisory-v1',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'app.etzhayyim.apps.ossVuln.registerAdvisory',
                 'open_oss_vuln_register_advisory',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-oss-vuln-registerAdvisory-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-oss-vuln-recordSbomMatch-v1',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'app.etzhayyim.apps.ossVuln.recordSbomMatch',
                 'open_oss_vuln_record_sbom_match',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'did:web:open-oss-vuln.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-oss-vuln-recordSbomMatch-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-recordThreatActor-v1',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberThreat.recordThreatActor',
                 'open_cyber_threat_actor',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-recordThreatActor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-assessThreatActor-v1',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberThreat.assessThreatActor',
                 'open_cyber_threat_assess_threat_actor',
                 30000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-assessThreatActor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-recordCampaign-v1',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberThreat.recordCampaign',
                 'open_cyber_threat_campaign',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'did:web:open-cyber-threat.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-recordCampaign-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-reportIncident-v1',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberIncident.reportIncident',
                 'open_cyber_incident_report',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-reportIncident-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-recordIOC-v1',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberIncident.recordIOC',
                 'open_cyber_incident_ioc',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-recordIOC-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-linkIncidentToTreaty-v1',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberIncident.linkIncidentToTreaty',
                 'open_cyber_incident_link_incident_to_treaty',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'did:web:open-cyber-incident.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-linkIncidentToTreaty-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-compliance-recordIsmsAudit-v1',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberCompliance.recordIsmsAudit',
                 'open_cyber_compliance_isms',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-compliance-recordIsmsAudit-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-compliance-recordRegulatoryReporting-v1',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberCompliance.recordRegulatoryReporting',
                 'open_cyber_compliance_regulatory',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'did:web:open-cyber-compliance.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-compliance-recordRegulatoryReporting-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-recordSocAlert-v1',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberSoc.recordSocAlert',
                 'open_cyber_soc_alert',
                 15000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-recordSocAlert-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-recordIncidentResponse-v1',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberSoc.recordIncidentResponse',
                 'open_cyber_soc_ir',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-recordIncidentResponse-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-escalateStateApt-v1',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberSoc.escalateStateApt',
                 'open_cyber_soc_escalate_state_apt',
                 30000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'did:web:open-cyber-soc.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-escalateStateApt-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-resilience-stress-recordStressTest-v1',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberResilienceStress.recordStressTest',
                 'open_cyber_resilience_stress_record_stress_test',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-resilience-stress-recordStressTest-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-resilience-stress-reportResilienceGap-v1',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'app.etzhayyim.apps.cyberResilienceStress.reportResilienceGap',
                 'open_cyber_resilience_stress_report_resilience_gap',
                 20000,
                 '2026-04-28T23:01:00Z',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'did:web:open-cyber-resilience-stress.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-cyber',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-resilience-stress-reportResilienceGap-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-recordCveDisclosure-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-recordPatchAdvisory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-vuln-linkExploitToActor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-recordAssignment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-flagDisclosureGap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cve-cna-flagWeaponizedCve-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-kev-catalog-recordEntry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-kev-catalog-flagRemediationLag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-oss-vuln-registerAdvisory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-oss-vuln-recordSbomMatch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-recordThreatActor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-assessThreatActor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-threat-recordCampaign-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-reportIncident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-recordIOC-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-incident-linkIncidentToTreaty-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-compliance-recordIsmsAudit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-compliance-recordRegulatoryReporting-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-recordSocAlert-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-recordIncidentResponse-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-soc-escalateStateApt-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-resilience-stress-recordStressTest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-cyber-resilience-stress-reportResilienceGap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-record-cve-disclosure-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-record-patch-advisory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-vuln-link-exploit-to-actor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-record-assignment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-disclosure-gap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cve-cna-flag-weaponized-cve-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-kev-catalog-record-entry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-kev-catalog-flag-remediation-lag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-oss-vuln-register-advisory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-oss-vuln-record-sbom-match-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-record-threat-actor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-assess-threat-actor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-threat-record-campaign-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-report-incident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-record-i-o-c-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-incident-link-incident-to-treaty-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-compliance-record-isms-audit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-compliance-record-regulatory-reporting-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-record-soc-alert-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-record-incident-response-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-soc-escalate-state-apt-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-resilience-stress-record-stress-test-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-cyber-resilience-stress-report-resilience-gap-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
