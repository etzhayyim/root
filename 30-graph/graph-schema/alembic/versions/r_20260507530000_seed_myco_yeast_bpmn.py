"""Captured from Kysely migration 20260507530000_seed_myco_yeast_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507530000_seed_myco_yeast_bpmn"
down_revision = 'r_20260507530000_magatama_organizer_run_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-budding-v1',
                 'did:web:bpmn.gftd.ai',
                 'kobo_budding',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_kobo_budding" targetNamespace="https://gftd.ai/bpmn/kobo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kobo_budding" name="budding" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_BudAgent"/>\n'
                 '    <bpmn:serviceTask id="Task_BudAgent" name="bud-agent">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="kobo.bud_agent"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=parentDid" target="parentDid"/>\n'
                 '          <zeebe:input source="=childDid" target="childDid"/>\n'
                 '          <zeebe:input source="=childVertexId" target="childVertexId"/>\n'
                 '          <zeebe:input source="=childRole" target="childRole"/>\n'
                 '          <zeebe:input source="=parentEta" target="parentEta"/>\n'
                 '          <zeebe:input source="=callerDid" target="callerDid"/>\n'
                 '          <zeebe:input source="=buddingEdgeId" target="buddingEdgeId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_BudAgent" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:kobo.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;kobo.budAgent&quot;" target="action"/>\n'
                 '          <zeebe:input source="={parentDid: parentDid, childDid: childDid, '
                 'buddingEdgeId: buddingEdgeId}" target="payload"/>\n'
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
                 2260,
                 '00-contracts/bpmn/ai/gftd/kobo/budding.bpmn',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-budding-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-budding-v1',
                 'did:web:bpmn.gftd.ai',
                 'kobo_budding',
                 'ai.gftd.apps.kobo.budAgent',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-budding-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-germination-v1',
                 'did:web:bpmn.gftd.ai',
                 'kobo_germination',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_kobo_germination" targetNamespace="https://gftd.ai/bpmn/kobo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kobo_germination" name="germination" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Germinate"/>\n'
                 '    <bpmn:serviceTask id="Task_Germinate" name="germinate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="kobo.germinate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=sporeVertexId" target="sporeVertexId"/>\n'
                 '          <zeebe:input source="=quorumN" target="quorumN"/>\n'
                 '          <zeebe:input source="=newAgentDid" target="newAgentDid"/>\n'
                 '          <zeebe:input source="=newAgentVertexId" target="newAgentVertexId"/>\n'
                 '          <zeebe:input source="=originAgentDid" target="originAgentDid"/>\n'
                 '          <zeebe:input source="=restoredEta" target="restoredEta"/>\n'
                 '          <zeebe:input source="=callerDid" target="callerDid"/>\n'
                 '          <zeebe:output source="=germinated" target="germinated"/>\n'
                 '          <zeebe:output source="=confirmedCount" target="confirmedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Q</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Q" sourceRef="Task_Germinate" '
                 'targetRef="Gate_Germinated"/>\n'
                 '    <bpmn:exclusiveGateway id="Gate_Germinated" name="germinated?">\n'
                 '      <bpmn:incoming>Flow_Q</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Yes</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_No</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Yes" sourceRef="Gate_Germinated" '
                 'targetRef="Task_Audit">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=germinated = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_No" sourceRef="Gate_Germinated" '
                 'targetRef="End_Reject"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:kobo.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;kobo.germinate&quot;" target="action"/>\n'
                 '          <zeebe:input source="={sporeVertexId: sporeVertexId, newAgentDid: '
                 'newAgentDid, confirmedCount: confirmedCount}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Yes</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent id="End_Reject" '
                 'name="quorum-not-met"><bpmn:incoming>Flow_No</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3122,
                 '00-contracts/bpmn/ai/gftd/kobo/germination.bpmn',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-germination-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-germination-v1',
                 'did:web:bpmn.gftd.ai',
                 'kobo_germination',
                 'ai.gftd.apps.kobo.spawnAgent',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-germination-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-sporulation-v1',
                 'did:web:bpmn.gftd.ai',
                 'kobo_sporulation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_kobo_sporulation" targetNamespace="https://gftd.ai/bpmn/kobo" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="kobo_sporulation" name="sporulation" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Sporulate"/>\n'
                 '    <bpmn:serviceTask id="Task_Sporulate" name="sporulate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="kobo.sporulate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=sporeVertexId" target="sporeVertexId"/>\n'
                 '          <zeebe:input source="=agentDid" target="agentDid"/>\n'
                 '          <zeebe:input source="=agentVertexId" target="agentVertexId"/>\n'
                 '          <zeebe:input source="=blobCbor" target="blobCbor"/>\n'
                 '          <zeebe:input source="=revivalKeyHint" target="revivalKeyHint"/>\n'
                 '          <zeebe:input source="=quorumN" target="quorumN"/>\n'
                 '          <zeebe:input source="=callerDid" target="callerDid"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Task_Sporulate" '
                 'targetRef="Task_DistributeCustody"/>\n'
                 '    <!-- Custody distribution is a cross-system dispatch — kept as '
                 'generic.pds.dispatch -->\n'
                 '    <bpmn:serviceTask id="Task_DistributeCustody" name="distribute-custody">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.houshi.storeSpore&quot;" '
                 'target="nsid"/>\n'
                 '          <zeebe:input source="={sporeVertexId: sporeVertexId, custodianDids: '
                 'custodianDids}" target="body"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_DistributeCustody" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:kobo.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;kobo.sporulate&quot;" target="action"/>\n'
                 '          <zeebe:input source="={agentDid: agentDid, sporeVertexId: '
                 'sporeVertexId}" target="payload"/>\n'
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
                 3010,
                 '00-contracts/bpmn/ai/gftd/kobo/sporulation.bpmn',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-sporulation-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-sporulation-v1',
                 'did:web:bpmn.gftd.ai',
                 'kobo_sporulation',
                 'ai.gftd.apps.kobo.sporulate',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-sporulation-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kabi-anastomosis-gate-v1',
                 'did:web:bpmn.gftd.ai',
                 'kabi_anastomosis_gate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_kabi_anastomosis_gate" '
                 'targetNamespace="https://gftd.ai/bpmn/kabi" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="kabi_anastomosis_gate" name="anastomosis-gate" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Probe"/>\n'
                 '    <bpmn:serviceTask id="Task_Probe" name="anastomosis-probe">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kabi.anastomosis_probe"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=networkADid" target="networkADid"/>\n'
                 '          <zeebe:input source="=networkBDid" target="networkBDid"/>\n'
                 '          <zeebe:input source="=edgeId" target="edgeId"/>\n'
                 '          <zeebe:input source="=callerDid" target="callerDid"/>\n'
                 '          <zeebe:output source="=probeResult" target="probeResult"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_G</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_G" sourceRef="Task_Probe" '
                 'targetRef="Gate_Compatible"/>\n'
                 '    <bpmn:exclusiveGateway id="Gate_Compatible" name="compatible?">\n'
                 '      <bpmn:incoming>Flow_G</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Yes</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_No</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Yes" sourceRef="Gate_Compatible" '
                 'targetRef="Task_ExtendHypha">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=probeResult.compatible = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_No" sourceRef="Gate_Compatible" '
                 'targetRef="Task_Audit"/>\n'
                 '    <!-- Hypha extension is a cross-system dispatch — kept as '
                 'generic.pds.dispatch -->\n'
                 '    <bpmn:serviceTask id="Task_ExtendHypha" name="extend-hypha">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.kabi.extendHypha&quot;" '
                 'target="nsid"/>\n'
                 '          <zeebe:input source="={srcAgentDid: networkADid, dstAgentDid: '
                 'networkBDid, eta: probeResult.compatibility_score, flow: 0}" target="body"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Yes</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_ExtendHypha" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:kabi.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;kabi.anastomosisGate&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={networkADid: networkADid, networkBDid: '
                 'networkBDid, probeResult: probeResult}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_No</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3563,
                 '00-contracts/bpmn/ai/gftd/kabi/anastomosis-gate.bpmn',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kabi-anastomosis-gate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kabi-anastomosis-gate-v1',
                 'did:web:bpmn.gftd.ai',
                 'kabi_anastomosis_gate',
                 'ai.gftd.apps.kabi.fusionProbe',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kabi-anastomosis-gate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kinoko-ponf-fruiting-v1',
                 'did:web:bpmn.gftd.ai',
                 'kinoko_ponf_fruiting',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_kinoko_ponf_fruiting" '
                 'targetNamespace="https://gftd.ai/bpmn/kinoko" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <!-- Triggered by R/PT15M timer when flow threshold may be reached -->\n'
                 '  <bpmn:process id="kinoko_ponf_fruiting" name="ponf-fruiting" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="every-15min">\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_CheckThreshold"/>\n'
                 '    <bpmn:serviceTask id="Task_CheckThreshold" name="check-flow-threshold">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kinoko.check_flow_threshold"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=blockVertexId" target="blockVertexId"/>\n'
                 '          <zeebe:input source="=lastBlockId" target="lastBlockId"/>\n'
                 '          <zeebe:input source="=blockHash" target="blockHash"/>\n'
                 '          <zeebe:output source="=blockFormed" target="blockFormed"/>\n'
                 '          <zeebe:output source="=totalFlow" target="totalFlow"/>\n'
                 '          <zeebe:output source="=participantCount" target="participantCount"/>\n'
                 '          <zeebe:output source="=minEta" target="minEta"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_T</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_T" sourceRef="Task_CheckThreshold" '
                 'targetRef="Gate_BlockFormed"/>\n'
                 '    <bpmn:exclusiveGateway id="Gate_BlockFormed" name="block formed?">\n'
                 '      <bpmn:incoming>Flow_T</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Yes</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_No</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Yes" sourceRef="Gate_BlockFormed" '
                 'targetRef="Task_Audit">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=blockFormed = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_No" sourceRef="Gate_BlockFormed" '
                 'targetRef="End_Skip"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:kinoko.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;kinoko.formBlock&quot;" target="action"/>\n'
                 '          <zeebe:input source="={blockVertexId: blockVertexId, totalFlow: '
                 'totalFlow, participantCount: participantCount, minEta: minEta}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Yes</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent id="End_Skip" '
                 'name="threshold-not-reached"><bpmn:incoming>Flow_No</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3309,
                 '00-contracts/bpmn/ai/gftd/kinoko/ponf-fruiting.bpmn',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kinoko-ponf-fruiting-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kinoko-ponf-fruiting-v1',
                 'did:web:bpmn.gftd.ai',
                 'kinoko_ponf_fruiting',
                 'ai.gftd.apps.kinoko.formBlock',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kinoko-ponf-fruiting-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/hakkou-ferment-pipeline-v1',
                 'did:web:bpmn.gftd.ai',
                 'hakkou_ferment_pipeline',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_hakkou_ferment_pipeline" '
                 'targetNamespace="https://gftd.ai/bpmn/hakkou" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="hakkou_ferment_pipeline" name="ferment-pipeline" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_CreateRecord"/>\n'
                 '    <bpmn:serviceTask id="Task_CreateRecord" name="create-ferment-record">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="hakkou.create_ferment_record"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=fermentVertexId" target="fermentVertexId"/>\n'
                 '          <zeebe:input source="=agentDid" target="agentDid"/>\n'
                 '          <zeebe:input source="=inputKind" target="inputKind"/>\n'
                 '          <zeebe:input source="=inputRef" target="inputRef"/>\n'
                 '          <zeebe:input source="=outputKind" target="outputKind"/>\n'
                 '          <zeebe:input source="=callerDid" target="callerDid"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_CreateRecord" '
                 'targetRef="Task_LlmTransform"/>\n'
                 '    <bpmn:serviceTask id="Task_LlmTransform" name="llm-transform">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="hakkou.llm_transform"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=inputKind" target="inputKind"/>\n'
                 '          <zeebe:input source="=inputRef" target="inputRef"/>\n'
                 '          <zeebe:input source="=outputKind" target="outputKind"/>\n'
                 '          <zeebe:output source="=fermentOutput" target="fermentOutput"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_L</bpmn:incoming><bpmn:outgoing>Flow_W</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_W" sourceRef="Task_LlmTransform" '
                 'targetRef="Task_WriteOutput"/>\n'
                 '    <!-- Output dispatch is dynamic (outputNsid varies by run) — kept as '
                 'generic.pds.dispatch -->\n'
                 '    <bpmn:serviceTask id="Task_WriteOutput" name="write-output">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=outputNsid" target="nsid"/>\n'
                 '          <zeebe:input source="=fermentOutput" target="body"/>\n'
                 '          <zeebe:output source="=vertexId" target="outputVertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_W</bpmn:incoming><bpmn:outgoing>Flow_Finalize</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Finalize" sourceRef="Task_WriteOutput" '
                 'targetRef="Task_Finalize"/>\n'
                 '    <bpmn:serviceTask id="Task_Finalize" name="finalize-ferment">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="hakkou.finalize_ferment"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=fermentVertexId" target="fermentVertexId"/>\n'
                 '          <zeebe:input source="=outputVertexId" target="outputVertexId"/>\n'
                 '          <zeebe:input source="=ethanolHash" target="ethanolHash"/>\n'
                 '          <zeebe:input source="=co2AuditRef" target="co2AuditRef"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Finalize</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Finalize" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:hakkou.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;hakkou.ferment&quot;" target="action"/>\n'
                 '          <zeebe:input source="={fermentVertexId: fermentVertexId, agentDid: '
                 'agentDid, outputVertexId: outputVertexId, ethanolHash: ethanolHash}" '
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
                 4468,
                 '00-contracts/bpmn/ai/gftd/hakkou/ferment-pipeline.bpmn',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/hakkou-ferment-pipeline-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.myco-yeast'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/hakkou-ferment-pipeline-v1',
                 'did:web:bpmn.gftd.ai',
                 'hakkou_ferment_pipeline',
                 'ai.gftd.apps.hakkou.startFerment',
                 '2026-05-07T23:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/hakkou-ferment-pipeline-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-budding-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-budding-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-germination-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-germination-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kobo-sporulation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kobo-sporulation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kabi-anastomosis-gate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kabi-anastomosis-gate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/kinoko-ponf-fruiting-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/kinoko-ponf-fruiting-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/hakkou-ferment-pipeline-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/hakkou-ferment-pipeline-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
