"""Captured from Kysely migration 20260427230400_seed_legal_logical_actors_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427230400_seed_legal_logical_actors_bpmn"
down_revision = 'r_20260427230300_vertex_adr_legal_aid'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/judge-register-judge-v1',
                 'did:web:judge.etzhayyim.com',
                 'judge_register_judge',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_judge_register_judge" '
                 'targetNamespace="https://etzhayyim.com/bpmn/judge" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="judge_register_judge" name="registerJudge" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="upsert vertex_judge">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_judge&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:judge.etzhayyim.com:&quot; + jurisdiction + &quot;:&quot; + '
                 'judgeSlug + &quot;/com.etzhayyim.apps.judge.profile/self&quot;, judge_did: '
                 '&quot;did:web:judge.etzhayyim.com:&quot; + jurisdiction + &quot;:&quot; + judgeSlug, '
                 'full_name: fullName, full_name_local: fullNameLocal, court_did: courtDid, '
                 'court_level: courtLevel, jurisdiction: jurisdiction, appointed_at: appointedAt, '
                 'retired_at: retiredAt, specializations_csv: specializations, biography_uri: '
                 'biographyUri, owner_did: &quot;did:web:judge.etzhayyim.com&quot;, sensitivity_ord: 1, '
                 'created_at: now}" target="row"/>\n'
                 '          <zeebe:input source="=&quot;upsert&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=vertex_id" target="vertexId"/>\n'
                 '          <zeebe:output source="=row.judge_did" target="did"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Insert" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1980,
                 '00-contracts/bpmn/com/etzhayyim/judge/registerJudge.bpmn',
                 '2026-04-27T23:04:00Z',
                 'did:web:judge.etzhayyim.com',
                 'did:web:judge.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/judge-register-judge-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/judge-list-judges-v1',
                 'did:web:judge.etzhayyim.com',
                 'judge_list_judges',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_judge_list_judges" targetNamespace="https://etzhayyim.com/bpmn/judge" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="judge_list_judges" name="listJudges" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Select"/>\n'
                 '    <bpmn:serviceTask id="Task_Select" name="select judges">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, judge_did, full_name, '
                 'court_did, jurisdiction, appointed_at FROM vertex_judge WHERE ($1::varchar IS '
                 'NULL OR jurisdiction = $1) AND ($2::varchar IS NULL OR court_did = $2) ORDER BY '
                 'full_name LIMIT $3 OFFSET $4&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[jurisdiction, courtDid, limit, offset]" '
                 'target="params"/>\n'
                 '          <zeebe:output source="=rows" target="judges"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Select" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1516,
                 '00-contracts/bpmn/com/etzhayyim/judge/listJudges.bpmn',
                 '2026-04-27T23:04:00Z',
                 'did:web:judge.etzhayyim.com',
                 'did:web:judge.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/judge-list-judges-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bengoshi-register-lawyer-v1',
                 'did:web:bengoshi.etzhayyim.com',
                 'bengoshi_register_lawyer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_bengoshi_register_lawyer" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bengoshi" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="bengoshi_register_lawyer" name="registerLawyer" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="upsert vertex_lawyer">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_lawyer&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:bengoshi.etzhayyim.com:&quot; + jurisdiction + &quot;:&quot; + '
                 'lawyerSlug + &quot;/com.etzhayyim.apps.bengoshi.profile/self&quot;, lawyer_did: '
                 '&quot;did:web:bengoshi.etzhayyim.com:&quot; + jurisdiction + &quot;:&quot; + '
                 'lawyerSlug, full_name: fullName, full_name_local: fullNameLocal, bar_id: barId, '
                 'bar_association: barAssociation, jurisdiction: jurisdiction, admitted_at: '
                 'admittedAt, practice_areas_csv: practiceAreas, languages_csv: languages, '
                 'firm_did: firmDid, owner_did: &quot;did:web:bengoshi.etzhayyim.com&quot;, '
                 'sensitivity_ord: 1, created_at: now}" target="row"/>\n'
                 '          <zeebe:input source="=&quot;upsert&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=vertex_id" target="vertexId"/>\n'
                 '          <zeebe:output source="=row.lawyer_did" target="did"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Insert" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2000,
                 '00-contracts/bpmn/com/etzhayyim/bengoshi/registerLawyer.bpmn',
                 '2026-04-27T23:04:00Z',
                 'did:web:bengoshi.etzhayyim.com',
                 'did:web:bengoshi.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bengoshi-register-lawyer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bengoshi-search-lawyers-v1',
                 'did:web:bengoshi.etzhayyim.com',
                 'bengoshi_search_lawyers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_bengoshi_search_lawyers" '
                 'targetNamespace="https://etzhayyim.com/bpmn/bengoshi" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="bengoshi_search_lawyers" name="searchLawyers" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Select"/>\n'
                 '    <bpmn:serviceTask id="Task_Select" name="select lawyers">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, lawyer_did, full_name, '
                 'bar_association, jurisdiction, practice_areas_csv, languages_csv, firm_did FROM '
                 'vertex_lawyer WHERE ($1::varchar IS NULL OR jurisdiction = $1) AND ($2::varchar '
                 "IS NULL OR practice_areas_csv LIKE '%' || $2 || '%') AND ($3::varchar IS NULL OR "
                 "languages_csv LIKE '%' || $3 || '%') ORDER BY full_name LIMIT $4 OFFSET "
                 '$5&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[jurisdiction, practiceArea, language, limit, '
                 'offset]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="lawyers"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Select" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1680,
                 '00-contracts/bpmn/com/etzhayyim/bengoshi/searchLawyers.bpmn',
                 '2026-04-27T23:04:00Z',
                 'did:web:bengoshi.etzhayyim.com',
                 'did:web:bengoshi.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bengoshi-search-lawyers-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/adr-register-arbitrator-v1',
                 'did:web:adr.etzhayyim.com',
                 'adr_register_arbitrator',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_adr_register_arbitrator" '
                 'targetNamespace="https://etzhayyim.com/bpmn/adr" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="adr_register_arbitrator" name="registerArbitrator" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="upsert vertex_adr_arbitrator">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_adr_arbitrator&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:adr.etzhayyim.com:&quot; + institution + &quot;:&quot; + '
                 'arbitratorSlug + &quot;/com.etzhayyim.apps.adr.profile/self&quot;, arbitrator_did: '
                 '&quot;did:web:adr.etzhayyim.com:&quot; + institution + &quot;:&quot; + arbitratorSlug, '
                 'full_name: fullName, institution: institution, panel: panel, nationality: '
                 'nationality, languages_csv: languages, expertise_csv: expertise, owner_did: '
                 '&quot;did:web:adr.etzhayyim.com&quot;, sensitivity_ord: 1, created_at: now}" '
                 'target="row"/>\n'
                 '          <zeebe:input source="=&quot;upsert&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=vertex_id" target="vertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Insert" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1844,
                 '00-contracts/bpmn/com/etzhayyim/adr/registerArbitrator.bpmn',
                 '2026-04-27T23:04:00Z',
                 'did:web:adr.etzhayyim.com',
                 'did:web:adr.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/adr-register-arbitrator-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/adr-create-case-v1',
                 'did:web:adr.etzhayyim.com',
                 'adr_create_case',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_adr_create_case" targetNamespace="https://etzhayyim.com/bpmn/adr" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="adr_create_case" name="createCase" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="insert adr case (Tier 3)">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_adr_case&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:adr.etzhayyim.com:&quot; + institution + '
                 '&quot;/com.etzhayyim.apps.adr.case/&quot; + caseRef, case_ref: caseRef, institution: '
                 'institution, panel: panel, seat: seat, governing_law: governingLaw, parties_enc: '
                 'partiesEnc, claim_amount_enc: claimAmountEnc, currency: currency, status: '
                 '&quot;pending&quot;, opened_at: openedAt, owner_did: '
                 '&quot;did:web:adr.etzhayyim.com&quot;, sensitivity_ord: 3, created_at: now}" '
                 'target="row"/>\n'
                 '          <zeebe:output source="=vertex_id" target="vertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Insert" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1699,
                 '00-contracts/bpmn/com/etzhayyim/adr/createCase.bpmn',
                 '2026-04-27T23:04:00Z',
                 'did:web:adr.etzhayyim.com',
                 'did:web:adr.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/adr-create-case-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-aid-register-office-v1',
                 'did:web:legal-aid.etzhayyim.com',
                 'legal_aid_register_office',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_aid_register_office" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-aid" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_aid_register_office" name="registerOffice" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="upsert vertex_legal_aid_office">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_legal_aid_office&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:legal-aid.etzhayyim.com:&quot; + jurisdiction + &quot;:&quot; + '
                 'officeSlug + &quot;/com.etzhayyim.apps.legal-aid.profile/self&quot;, office_did: '
                 '&quot;did:web:legal-aid.etzhayyim.com:&quot; + jurisdiction + &quot;:&quot; + '
                 'officeSlug, display_name: displayName, jurisdiction: jurisdiction, office_type: '
                 'officeType, address_locality: addressLocality, languages_csv: languages, '
                 'specialties_csv: specialties, intake_url: intakeUrl, owner_did: '
                 '&quot;did:web:legal-aid.etzhayyim.com&quot;, sensitivity_ord: 1, created_at: now}" '
                 'target="row"/>\n'
                 '          <zeebe:input source="=&quot;upsert&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=vertex_id" target="vertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Insert" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1923,
                 '00-contracts/bpmn/com/etzhayyim/legal-aid/registerOffice.bpmn',
                 '2026-04-27T23:04:00Z',
                 'did:web:legal-aid.etzhayyim.com',
                 'did:web:legal-aid.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-aid-register-office-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-aid-open-case-v1',
                 'did:web:legal-aid.etzhayyim.com',
                 'legal_aid_open_case',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_aid_open_case" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-aid" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_aid_open_case" name="openCase" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="insert legal-aid case (Tier 3)">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_legal_aid_case&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: &quot;at://&quot; + officeDid + '
                 '&quot;/com.etzhayyim.apps.legal-aid.case/&quot; + applicantHash, office_did: '
                 'officeDid, applicant_hash: applicantHash, applicant_pii_enc: applicantPiiEnc, '
                 'matter_area: matterArea, income_bracket: incomeBracket, language_code: '
                 'languageCode, intake_channel: intakeChannel, opened_at: openedAt, status: '
                 '&quot;open&quot;, owner_did: officeDid, sensitivity_ord: 3, created_at: now}" '
                 'target="row"/>\n'
                 '          <zeebe:input source="=&quot;skip&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=vertex_id" target="vertexId"/>\n'
                 '          <zeebe:output source="=row.applicant_hash" target="caseRef"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Insert" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1859,
                 '00-contracts/bpmn/com/etzhayyim/legal-aid/openCase.bpmn',
                 '2026-04-27T23:04:00Z',
                 'did:web:legal-aid.etzhayyim.com',
                 'did:web:legal-aid.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-aid-open-case-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/judge-registerJudge-v1',
                 'did:web:judge.etzhayyim.com',
                 'com.etzhayyim.apps.judge.registerJudge',
                 'judge_register_judge',
                 15000,
                 '2026-04-27T23:04:00Z',
                 'did:web:judge.etzhayyim.com',
                 'did:web:judge.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/judge-registerJudge-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/judge-listJudges-v1',
                 'did:web:judge.etzhayyim.com',
                 'com.etzhayyim.apps.judge.listJudges',
                 'judge_list_judges',
                 15000,
                 '2026-04-27T23:04:00Z',
                 'did:web:judge.etzhayyim.com',
                 'did:web:judge.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/judge-listJudges-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bengoshi-registerLawyer-v1',
                 'did:web:bengoshi.etzhayyim.com',
                 'com.etzhayyim.apps.bengoshi.registerLawyer',
                 'bengoshi_register_lawyer',
                 15000,
                 '2026-04-27T23:04:00Z',
                 'did:web:bengoshi.etzhayyim.com',
                 'did:web:bengoshi.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bengoshi-registerLawyer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bengoshi-searchLawyers-v1',
                 'did:web:bengoshi.etzhayyim.com',
                 'com.etzhayyim.apps.bengoshi.searchLawyers',
                 'bengoshi_search_lawyers',
                 15000,
                 '2026-04-27T23:04:00Z',
                 'did:web:bengoshi.etzhayyim.com',
                 'did:web:bengoshi.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bengoshi-searchLawyers-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/adr-registerArbitrator-v1',
                 'did:web:adr.etzhayyim.com',
                 'com.etzhayyim.apps.adr.registerArbitrator',
                 'adr_register_arbitrator',
                 15000,
                 '2026-04-27T23:04:00Z',
                 'did:web:adr.etzhayyim.com',
                 'did:web:adr.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/adr-registerArbitrator-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/adr-createCase-v1',
                 'did:web:adr.etzhayyim.com',
                 'com.etzhayyim.apps.adr.createCase',
                 'adr_create_case',
                 15000,
                 '2026-04-27T23:04:00Z',
                 'did:web:adr.etzhayyim.com',
                 'did:web:adr.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/adr-createCase-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-aid-registerOffice-v1',
                 'did:web:legal-aid.etzhayyim.com',
                 'com.etzhayyim.apps.legal-aid.registerOffice',
                 'legal_aid_register_office',
                 15000,
                 '2026-04-27T23:04:00Z',
                 'did:web:legal-aid.etzhayyim.com',
                 'did:web:legal-aid.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-aid-registerOffice-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-aid-openCase-v1',
                 'did:web:legal-aid.etzhayyim.com',
                 'com.etzhayyim.apps.legal-aid.openCase',
                 'legal_aid_open_case',
                 15000,
                 '2026-04-27T23:04:00Z',
                 'did:web:legal-aid.etzhayyim.com',
                 'did:web:legal-aid.etzhayyim.com',
                 'sys.bpmn.seed.legal-logical-actors',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-aid-openCase-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/judge-registerJudge-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/judge-listJudges-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bengoshi-registerLawyer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/bengoshi-searchLawyers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/adr-registerArbitrator-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/adr-createCase-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-aid-registerOffice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-aid-openCase-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/judge-register-judge-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/judge-list-judges-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bengoshi-register-lawyer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/bengoshi-search-lawyers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/adr-register-arbitrator-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/adr-create-case-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-aid-register-office-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-aid-open-case-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
