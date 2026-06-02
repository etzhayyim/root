"""Captured from Kysely migration 20260429090500_seed_legal_entity_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429090500_seed_legal_entity_bpmn_actors"
down_revision = 'r_20260429090400_seed_smishing_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectGlobalGleif-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_global_gleif',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_legal_entity_collect_global_gleif"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/legal-entity"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_entity_collect_global_gleif" name="legal entity '
                 'collect global gleif" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="GLEIF collection requested">\n'
                 '      <bpmn:outgoing>Flow_Fetch</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fetch" sourceRef="Start" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch and commit GLEIF pages">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="legalEntity.gleif.fetchPages"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=pages" target="pages"/>\n'
                 '          <zeebe:input source="=pageSize" target="pageSize"/>\n'
                 '          <zeebe:input source="=startPage" target="startPage"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Fetch</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Fetch" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit GLEIF collection">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;legal-entity.collectGlobalGleif&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ startPage: startPage, pages: pages, result: '
                 'result }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="GLEIF collection committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2342,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectGlobalGleif.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectGlobalGleif-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectGlobalGleif-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectGlobalGleif',
                 'legal_entity_collect_global_gleif',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectGlobalGleif-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-registerGleifDids-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_register_gleif_dids',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_legal_entity_register_gleif_dids"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/legal-entity"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_entity_register_gleif_dids" name="legal entity '
                 'register GLEIF DIDs" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="GLEIF DID registration requested">\n'
                 '      <bpmn:outgoing>Flow_Register</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Register" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="resolve and commit GLEIF DIDs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="legalEntity.gleif.registerDids"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=pages" target="pages"/>\n'
                 '          <zeebe:input source="=pageSize" target="pageSize"/>\n'
                 '          <zeebe:input source="=startPage" target="startPage"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Register</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Register" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit GLEIF DID registration">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;legal-entity.registerGleifDids&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ startPage: startPage, pages: pages, result: '
                 'result }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="GLEIF DIDs committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2365,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/registerGleifDids.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-registerGleifDids-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-registerGleifDids-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.registerGleifDids',
                 'legal_entity_register_gleif_dids',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-registerGleifDids-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectUsaEdgar-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_usa_edgar',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_legal_entity_collect_usa_edgar"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/legal-entity"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_entity_collect_usa_edgar" name="legal entity collect '
                 'USA EDGAR" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="USA EDGAR collection requested">\n'
                 '      <bpmn:outgoing>Flow_Collect</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Collect" sourceRef="Start" '
                 'targetRef="Task_Collect"/>\n'
                 '    <bpmn:serviceTask id="Task_Collect" name="fetch and commit SEC '
                 'registrants">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="legalEntity.edgar.collectUsa"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=pages" target="pages"/>\n'
                 '          <zeebe:input source="=pageSize" target="pageSize"/>\n'
                 '          <zeebe:input source="=startPage" target="startPage"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Collect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Collect" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit USA EDGAR collection">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;legal-entity.collectUsaEdgar&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ startPage: startPage, pages: pages, result: '
                 'result }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="USA EDGAR records committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2355,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectUsaEdgar.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectUsaEdgar-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectUsaEdgar-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectUsaEdgar',
                 'legal_entity_collect_usa_edgar',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectUsaEdgar-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-ingestSecDisclosure-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_ingest_sec_disclosure',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_legal_entity_ingest_sec_disclosure"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/legal-entity"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_entity_ingest_sec_disclosure" name="legal entity '
                 'ingest SEC disclosure" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="SEC disclosure ingest requested">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="Start" '
                 'targetRef="Task_Ingest"/>\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="fetch and commit SEC disclosure '
                 'records">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="legalEntity.edgar.ingestSecDisclosure"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=ticker" target="ticker"/>\n'
                 '          <zeebe:input source="=cik" target="cik"/>\n'
                 '          <zeebe:input source="=filingLimit" target="filingLimit"/>\n'
                 '          <zeebe:input source="=factsLimit" target="factsLimit"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit SEC disclosure ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;legal-entity.ingestSecDisclosure&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ ticker: ticker, cik: cik, result: result }" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="SEC disclosure records committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2440,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/ingestSecDisclosure.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-ingestSecDisclosure-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-ingestSecDisclosure-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.ingestSecDisclosure',
                 'legal_entity_ingest_sec_disclosure',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-ingestSecDisclosure-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectJpn-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_jpn',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_jpn" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_entity_collect_jpn" name="legal entity collect JPN '
                 'registry" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="JPN registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fetch" sourceRef="Start" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch and commit JPN registry '
                 'pages">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectJpn"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=from" target="from"/><zeebe:input '
                 'source="=to" target="to"/><zeebe:input source="=kind" '
                 'target="kind"/><zeebe:input source="=prefecture" '
                 'target="prefecture"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Fetch" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit JPN registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectJpn&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, startPage: startPage, result: '
                 'result }" target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="JPN registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2310,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectJpn.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectJpn-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectJpn-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectJpn',
                 'legal_entity_collect_jpn',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectJpn-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectGbr-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_gbr',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_gbr" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_entity_collect_gbr" name="legal entity collect GBR '
                 'registry" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="GBR registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fetch" sourceRef="Start" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch and commit GBR registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectGbr"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startIndex" '
                 'target="startIndex"/><zeebe:input source="=companyStatus" '
                 'target="companyStatus"/><zeebe:input source="=companyType" '
                 'target="companyType"/><zeebe:input source="=incorporatedFrom" '
                 'target="incorporatedFrom"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Fetch" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit GBR registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectGbr&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" '
                 'targetRef="End"/><bpmn:endEvent id="End" name="GBR registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2271,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectGbr.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectGbr-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectGbr-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectGbr',
                 'legal_entity_collect_gbr',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectGbr-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectFra-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_fra',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_fra" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_entity_collect_fra" name="legal entity collect FRA '
                 'registry" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="FRA registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch and commit FRA registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectFra"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=cursor" target="cursor"/><zeebe:input '
                 'source="=activesOnly" target="activesOnly"/><zeebe:input source="=departement" '
                 'target="departement"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Fetch" '
                 'targetRef="Task_Audit"/><bpmn:serviceTask id="Task_Audit" name="audit FRA '
                 'registry collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectFra&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" '
                 'targetRef="End"/><bpmn:endEvent id="End" name="FRA registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2182,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectFra.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectFra-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectFra-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectFra',
                 'legal_entity_collect_fra',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectFra-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNor-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_nor',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_nor" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_nor" name="legal '
                 'entity collect NOR registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="NOR registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit NOR registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectNor"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=organisasjonsform" '
                 'target="organisasjonsform"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit NOR registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectNor&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="NOR registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2115,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectNor.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNor-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectNor',
                 'legal_entity_collect_nor',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNor-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectDnk-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_dnk',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_dnk" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_dnk" name="legal '
                 'entity collect DNK registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="DNK registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit DNK registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectDnk"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=search" target="search"/><zeebe:output '
                 'source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit DNK registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectDnk&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, search: search, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="DNK registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2109,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectDnk.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectDnk-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectDnk-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectDnk',
                 'legal_entity_collect_dnk',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectDnk-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectFin-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_fin',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_fin" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_fin" name="legal '
                 'entity collect FIN registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="FIN registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit FIN registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectFin"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=companyForm" '
                 'target="companyForm"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit FIN registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectFin&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="FIN registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2103,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectFin.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectFin-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectFin-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectFin',
                 'legal_entity_collect_fin',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectFin-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectEst-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_est',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_est" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_est" name="legal '
                 'entity collect EST registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="EST registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit EST registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectEst"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=legalForm" '
                 'target="legalForm"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit EST registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectEst&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="EST registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2099,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectEst.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectEst-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectEst-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectEst',
                 'legal_entity_collect_est',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectEst-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectCze-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_cze',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_cze" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_cze" name="legal '
                 'entity collect CZE registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="CZE registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit CZE registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectCze"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=query" target="query"/><zeebe:output '
                 'source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit CZE registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectCze&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, query: query, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="CZE registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2105,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectCze.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectCze-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectCze-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectCze',
                 'legal_entity_collect_cze',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectCze-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNzl-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_nzl',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_nzl" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_nzl" name="legal '
                 'entity collect NZL registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="NZL registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit NZL registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectNzl"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=entityType" '
                 'target="entityType"/><zeebe:input source="=entityStatus" '
                 'target="entityStatus"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit NZL registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectNzl&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="NZL registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2160,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectNzl.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNzl-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNzl-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectNzl',
                 'legal_entity_collect_nzl',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNzl-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectChe-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_che',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_che" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_che" name="legal '
                 'entity collect CHE registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="CHE registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit CHE registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectChe"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=canton" target="canton"/><zeebe:input '
                 'source="=legalForm" target="legalForm"/><zeebe:input source="=activeOnly" '
                 'target="activeOnly"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit CHE registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectChe&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="CHE registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2201,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectChe.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectChe-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectChe-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectChe',
                 'legal_entity_collect_che',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectChe-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNld-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_nld',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_nld" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_nld" name="legal '
                 'entity collect NLD registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="NLD registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit NLD registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectNld"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=query" target="query"/><zeebe:output '
                 'source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit NLD registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectNld&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, query: query, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="NLD registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2105,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectNld.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNld-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNld-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectNld',
                 'legal_entity_collect_nld',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNld-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectIsr-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'legal_entity_collect_isr',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_isr" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_isr" name="legal '
                 'entity collect ISR registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="ISR registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit ISR registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectIsr"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=companyType" '
                 'target="companyType"/><zeebe:input source="=status" '
                 'target="status"/><zeebe:output source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit ISR registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectIsr&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="ISR registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 2150,
                 '00-contracts/bpmn/com/etzhayyim/legal-entity/collectIsr.bpmn',
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectIsr-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectIsr-v1',
                 'did:web:legal-entity.etzhayyim.com',
                 'com.etzhayyim.apps.legalEntity.collectIsr',
                 'legal_entity_collect_isr',
                 120000,
                 '2026-04-29T09:05:00Z',
                 'did:web:legal-entity.etzhayyim.com',
                 'did:web:legal-entity.etzhayyim.com',
                 'sys.bpmn.seed.legal-entity',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectIsr-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectGlobalGleif-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectGlobalGleif-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-registerGleifDids-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-registerGleifDids-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectUsaEdgar-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectUsaEdgar-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-ingestSecDisclosure-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-ingestSecDisclosure-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectJpn-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectJpn-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectGbr-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectGbr-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectFra-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectFra-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectDnk-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectDnk-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectFin-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectFin-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectEst-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectEst-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectCze-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectCze-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNzl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNzl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectChe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectChe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectNld-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectNld-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-entity-collectIsr-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-entity-collectIsr-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
