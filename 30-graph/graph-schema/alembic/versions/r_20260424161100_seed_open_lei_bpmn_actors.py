"""Captured from Kysely migration 20260424161100_seed_open_lei_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424161100_seed_open_lei_bpmn_actors"
down_revision = 'r_20260424161000_vertex_open_lei'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-register-legal-entity-v1',
                 'did:web:open-lei.gftd.ai',
                 'open_lei_register_legal_entity',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_lei_register_legal_entity"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-lei"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_lei_register_legal_entity" name="LEI 登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Lifecycle"/>\n'
                 '\n'
                 '    <!--\n'
                 '      lifecycleState:\n'
                 '        active  : registrationStatus = "ISSUED"\n'
                 '        lapsed  : registrationStatus in '
                 '{"LAPSED","PENDING_TRANSFER","DUPLICATE"}\n'
                 '        retired : registrationStatus in {"RETIRED","MERGED"}\n'
                 '      requireRenewal = lapsed\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Lifecycle" name="lifecycle 判定">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if registrationStatus = &quot;ISSUED&quot; then '
                 '&quot;active&quot;\n'
                 '                                else if list '
                 'contains([&quot;RETIRED&quot;,&quot;MERGED&quot;], registrationStatus) then '
                 '&quot;retired&quot;\n'
                 '                                else &quot;lapsed&quot;" '
                 'target="lifecycleState"/>\n'
                 '          <zeebe:output source="=list '
                 'contains([&quot;LAPSED&quot;,&quot;PENDING_TRANSFER&quot;,&quot;DUPLICATE&quot;], '
                 'registrationStatus)" target="requireRenewal"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Lifecycle" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="entity 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_lei_entity&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, lei: lei, legal_name: legalName,\n'
                 '              country: country, legal_form: legalForm,\n'
                 '              registration_authority: registrationAuthority,\n'
                 '              registration_status: registrationStatus,\n'
                 '              issued_at: issuedAt, next_renewal_at: nextRenewalAt,\n'
                 '              status: lifecycleState, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-lei&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Save" targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_OK">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Renew</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_OK</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Renew" sourceRef="Gate" '
                 'targetRef="Task_AuditRenew">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requireRenewal = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_OK" sourceRef="Gate" targetRef="Task_AuditOk"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditRenew" name="audit lei.renewalRequired">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.lei.renewalRequired&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, lei: lei, '
                 'registrationStatus: registrationStatus, lifecycleState: lifecycleState}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Renew</bpmn:incoming><bpmn:outgoing>Flow_ER</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ER" sourceRef="Task_AuditRenew" '
                 'targetRef="End_R"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditOk" name="audit lei.register">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.lei.register&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, lei: lei, lifecycleState: '
                 'lifecycleState, country: country}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_OK</bpmn:incoming><bpmn:outgoing>Flow_EA</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EA" sourceRef="Task_AuditOk" '
                 'targetRef="End_A"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_A"><bpmn:incoming>Flow_EA</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_R"><bpmn:incoming>Flow_ER</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5395,
                 '00-contracts/bpmn/ai/gftd/open-lei/registerLegalEntity.bpmn',
                 '2026-04-24T16:30:00Z',
                 'did:web:open-lei.gftd.ai',
                 'did:web:open-lei.gftd.ai',
                 'sys.bpmn.seed.open-lei',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-register-legal-entity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-record-ownership-v1',
                 'did:web:open-lei.gftd.ai',
                 'open_lei_record_ownership',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_lei_record_ownership"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-lei"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_lei_record_ownership" name="LEI ownership 記録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="ownership 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_lei_ownership&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, parent_lei: parentLei, child_lei: childLei,\n'
                 '              relationship_type: relationshipType, ownership_pct: ownershipPct,\n'
                 '              relationship_period_start: relationshipPeriodStart,\n'
                 '              relationship_period_end: relationshipPeriodEnd,\n'
                 '              confidence: confidence, source: source,\n'
                 '              status: &quot;active&quot;, created_at: string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-lei&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Edge</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Edge" sourceRef="Task_Save" '
                 'targetRef="Task_Edge"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Edge" name="parent ↔ child edge">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_lei_ownership_pair&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:pair&quot;,\n'
                 '              src_vid: '
                 '&quot;at://did:web:open-lei.gftd.ai/ai.gftd.apps.openLei.entity/&quot; + '
                 'string(parentLei),\n'
                 '              dst_vid: '
                 '&quot;at://did:web:open-lei.gftd.ai/ai.gftd.apps.openLei.entity/&quot; + '
                 'string(childLei),\n'
                 '              role: relationshipType,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '1,\n'
                 '              org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-lei&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Edge</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Edge" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit ownership.record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.ownership.record&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, parentLei: parentLei, '
                 'childLei: childLei, relationshipType: relationshipType}" target="payload"/>\n'
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
                 3896,
                 '00-contracts/bpmn/ai/gftd/open-lei/recordOwnership.bpmn',
                 '2026-04-24T16:30:00Z',
                 'did:web:open-lei.gftd.ai',
                 'did:web:open-lei.gftd.ai',
                 'sys.bpmn.seed.open-lei',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-record-ownership-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-collect-gleif-global-v1',
                 'did:web:open-lei.gftd.ai',
                 'open_lei_collect_gleif_global_lei',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Global GLEIF LEI data collection plan for Camunda Zeebe.\n'
                 '\n'
                 '  Source:\n'
                 '    GLEIF Concatenated Files daily download:\n'
                 '      - LEI-CDF v3.1 Level 1: who is who\n'
                 '      - RR-CDF v2.1 Level 2: who owns whom\n'
                 '      - Reporting Exceptions v2.1: why parent data is not reported\n'
                 '\n'
                 '  Inputs:\n'
                 '    requestId\n'
                 '    asOfDate\n'
                 '    mode\n'
                 '    datasets\n'
                 '    shard\n'
                 '    shardCount\n'
                 '    limit\n'
                 '    countries\n'
                 '    keywords\n'
                 '\n'
                 '  Outputs:\n'
                 '    openLeiGleifManifestPlan\n'
                 '    openLeiGleifBulkCollect\n'
                 '    openLeiGleifRecordNormalize\n'
                 '    openLeiGleifEmsMatch\n'
                 '    finalStatus\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_open_lei_collect_gleif_global_lei"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-lei"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_lei_collect_gleif_global_lei" name="Collect GLEIF '
                 'global LEI data" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="GLEIF collection requested">\n'
                 '      <bpmn:outgoing>Flow_Start_Manifest</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Manifest" sourceRef="Start" '
                 'targetRef="Task_Manifest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Manifest" name="Plan GLEIF dataset manifest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.gleif.manifest.plan"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=asOfDate" target="asOfDate"/>\n'
                 '          <zeebe:input source="=datasets" target="datasets"/>\n'
                 '          <zeebe:input source="=mode" target="mode"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Manifest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Manifest_Collect</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manifest_Collect" sourceRef="Task_Manifest" '
                 'targetRef="Task_Collect"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Collect" name="Collect GLEIF bulk shard">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.gleif.bulk.collect"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=datasetKind" target="datasetKind"/>\n'
                 '          <zeebe:input source="=asOfDate" target="asOfDate"/>\n'
                 '          <zeebe:input source="=shard" target="shard"/>\n'
                 '          <zeebe:input source="=shardCount" target="shardCount"/>\n'
                 '          <zeebe:input source="=limit" target="limit"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Manifest_Collect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Collect_Normalize</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Collect_Normalize" sourceRef="Task_Collect" '
                 'targetRef="Task_Normalize"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Normalize" name="Normalize LEI records">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.gleif.record.normalize"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=datasetKind" target="datasetKind"/>\n'
                 '          <zeebe:input source="=records" target="records"/>\n'
                 '          <zeebe:input source="=asOfDate" target="asOfDate"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Collect_Normalize</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Normalize_GW</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Normalize_GW" sourceRef="Task_Normalize" '
                 'targetRef="GW_DatasetKind"/>\n'
                 '\n'
                 '    <!-- Branch: rr-cdf → ownership ingest; others → skip directly to EMS match '
                 '-->\n'
                 '    <bpmn:exclusiveGateway id="GW_DatasetKind" name="dataset kind?">\n'
                 '      <bpmn:incoming>Flow_Normalize_GW</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_GW_OwnershipIngest</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_GW_SkipOwnership</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_GW_OwnershipIngest" sourceRef="GW_DatasetKind" '
                 'targetRef="Task_OwnershipIngest">\n'
                 '      <bpmn:conditionExpression>=datasetKind = '
                 '"rr-cdf"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_GW_SkipOwnership" sourceRef="GW_DatasetKind" '
                 'targetRef="GW_Merge">\n'
                 '      <bpmn:conditionExpression>=datasetKind != '
                 '"rr-cdf"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_OwnershipIngest" name="Ingest ownership graph '
                 '(rr-cdf)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.gleif.ownership.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=openLeiGleifRecordNormalize" '
                 'target="openLeiGleifRecordNormalize"/>\n'
                 '          <zeebe:input source="=500" target="batchSize"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_GW_OwnershipIngest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_OwnershipIngest_Merge</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_OwnershipIngest_Merge" '
                 'sourceRef="Task_OwnershipIngest" targetRef="GW_Merge"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_Merge" name="merge">\n'
                 '      <bpmn:incoming>Flow_GW_SkipOwnership</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_OwnershipIngest_Merge</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Merge_EmsMatch</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Merge_EmsMatch" sourceRef="GW_Merge" '
                 'targetRef="Task_EmsMatch"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EmsMatch" name="Match LEI entities to EMS '
                 'candidates">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="openLei.gleif.ems.match"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=openLeiGleifRecordNormalize.entityRows" '
                 'target="entityRows"/>\n'
                 '          <zeebe:input source="=countries" target="countries"/>\n'
                 '          <zeebe:input source="=keywords" target="keywords"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Merge_EmsMatch</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_EmsMatch_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EmsMatch_Audit" sourceRef="Task_EmsMatch" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="Emit GLEIF collection audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-lei.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openLei.gleif.collectGlobal&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ requestId: requestId, manifest: '
                 'openLeiGleifManifestPlan, collection: openLeiGleifBulkCollect, normalize: '
                 'openLeiGleifRecordNormalize, emsMatch: openLeiGleifEmsMatch }" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=&quot;collected&quot;" target="finalStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_EmsMatch_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="GLEIF collection planned">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7098,
                 '00-contracts/bpmn/ai/gftd/open-lei/collectGleifGlobalLei.bpmn',
                 '2026-04-24T16:30:00Z',
                 'did:web:open-lei.gftd.ai',
                 'did:web:open-lei.gftd.ai',
                 'sys.bpmn.seed.open-lei',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-collect-gleif-global-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-registerLegalEntity-v1',
                 'did:web:open-lei.gftd.ai',
                 'ai.gftd.apps.openLei.registerLegalEntity',
                 'open_lei_register_legal_entity',
                 30000,
                 '2026-04-24T16:30:00Z',
                 'did:web:open-lei.gftd.ai',
                 'did:web:open-lei.gftd.ai',
                 'sys.bpmn.seed.open-lei',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-registerLegalEntity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-recordOwnership-v1',
                 'did:web:open-lei.gftd.ai',
                 'ai.gftd.apps.openLei.recordOwnership',
                 'open_lei_record_ownership',
                 15000,
                 '2026-04-24T16:30:00Z',
                 'did:web:open-lei.gftd.ai',
                 'did:web:open-lei.gftd.ai',
                 'sys.bpmn.seed.open-lei',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-recordOwnership-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-collectGleifGlobal-v1',
                 'did:web:open-lei.gftd.ai',
                 'ai.gftd.apps.openLei.collectGleifGlobal',
                 'open_lei_collect_gleif_global_lei',
                 180000,
                 '2026-04-24T16:30:00Z',
                 'did:web:open-lei.gftd.ai',
                 'did:web:open-lei.gftd.ai',
                 'sys.bpmn.seed.open-lei',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-collectGleifGlobal-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-registerLegalEntity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-recordOwnership-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-lei-collectGleifGlobal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-register-legal-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-record-ownership-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-lei-collect-gleif-global-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
