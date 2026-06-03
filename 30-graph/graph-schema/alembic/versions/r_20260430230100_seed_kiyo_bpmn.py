"""Captured from Kysely migration 20260430230100_seed_kiyo_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430230100_seed_kiyo_bpmn"
down_revision = 'r_20260430230000_vertex_kiyo'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-submit-paper-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_submit_paper',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  XRPC-triggered: com.etzhayyim.apps.kiyo.submitPaper\n'
                 '  Flow: validateAuthor → pinToIpfs → insertPaper → announceSubmission\n'
                 '  Storage: ipfs.etzhayyim.com (CIDv1, content-addressed)\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.kiyo.submitPaper\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-submit-paper-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_kiyo_submit_paper"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kiyo"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="kiyo_submit_paper" name="kiyo submit paper" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.kiyo.submitPaper", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="XRPC / on-demand">\n'
                 '      <bpmn:outgoing>Flow_Start</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start" sourceRef="Start_Manual" '
                 'targetRef="Task_ValidateAuthor"/>\n'
                 '\n'
                 '    <!-- 1. Validate caller is a registered actor DID -->\n'
                 '    <bpmn:serviceTask id="Task_ValidateAuthor" name="validate author DID">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kiyo.validateAuthor"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=ownerDid"    target="ownerDid"/>\n'
                 '          <zeebe:input  source="=authors"     target="authors"/>\n'
                 '          <zeebe:output source="=valid"       target="authorValid"/>\n'
                 '          <zeebe:output source="=authorNames" target="authorNames"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterValidate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterValidate" sourceRef="Task_ValidateAuthor" '
                 'targetRef="Task_PinToIpfs"/>\n'
                 '\n'
                 '    <!-- 2. Pin PDF to ipfs.etzhayyim.com -->\n'
                 '    <bpmn:serviceTask id="Task_PinToIpfs" name="pin PDF to ipfs.etzhayyim.com">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://ip5s7b2x.etzhayyim.com/xrpc/etzhayyim.ipfs.v1.IpfsCommandService/Publish&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="=&quot;POST&quot;"               '
                 'target="method"/>\n'
                 '          <zeebe:input source="=&quot;application/json&quot;"   '
                 'target="contentType"/>\n'
                 '          <zeebe:input source="={content_base64: fileBase64, content_type: '
                 'fileContentType}" target="body"/>\n'
                 '          <zeebe:input source="=30000"                          '
                 'target="timeoutMs"/>\n'
                 '          <zeebe:output source="=bodyJson.cid"  target="ipfsCid"/>\n'
                 '          <zeebe:output source="=status"        target="ipfsStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterIpfs</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterIpfs" sourceRef="Task_PinToIpfs" '
                 'targetRef="Task_InsertPaper"/>\n'
                 '\n'
                 '    <!-- 3. Insert vertex_kiyo_paper + edges into RisingWave -->\n'
                 '    <bpmn:serviceTask id="Task_InsertPaper" name="insert paper record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kiyo.insertPaper"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=paperId"     target="paperId"/>\n'
                 '          <zeebe:input source="=title"       target="title"/>\n'
                 '          <zeebe:input source="=abstract"    target="abstract"/>\n'
                 '          <zeebe:input source="=subject"     target="subject"/>\n'
                 '          <zeebe:input source="=authors"     target="authors"/>\n'
                 '          <zeebe:input source="=ownerDid"    target="ownerDid"/>\n'
                 '          <zeebe:input source="=authorType"  target="authorType"/>\n'
                 '          <zeebe:input source="=ipfsCid"     target="ipfsCid"/>\n'
                 '          <zeebe:input source="=sourceBase64" target="sourceBase64"/>\n'
                 '          <zeebe:output source="=vertexId"   target="paperVertexId"/>\n'
                 '          <zeebe:output source="=paperId"    target="paperId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterInsert</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterInsert" sourceRef="Task_InsertPaper" '
                 'targetRef="Task_Announce"/>\n'
                 '\n'
                 '    <!-- 4. Post announcement to AT Protocol -->\n'
                 '    <bpmn:serviceTask id="Task_Announce" name="announce on AT Protocol">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;app.bsky.feed.post&quot;" target="type"/>\n'
                 '          <zeebe:input source="=ownerDid"                       target="did"/>\n'
                 '          <zeebe:input source="=&quot;📄 New preprint: &quot; + title + &quot; — '
                 'kiyo:&quot; + paperId + &quot; https://kiyo.etzhayyim.com/paper/&quot; + paperId" '
                 'target="text"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Announce" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="submitted"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5030,
                 '00-contracts/bpmn/com/etzhayyim/kiyo/submitPaper.bpmn',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-submit-paper-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-submit-paper-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'com.etzhayyim.apps.kiyo.submitPaper',
                 'kiyo_submit_paper',
                 60000,
                 'vertex_kiyo_paper,vertex_kiyo_revision,edge_kiyo_authored_by',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-submit-paper-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-submit-revision-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_submit_revision',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  XRPC-triggered: com.etzhayyim.apps.kiyo.submitRevision\n'
                 '  Flow: validateOwner → pinNewVersion → insertRevision → updatePaper\n'
                 '  NSID: com.etzhayyim.apps.kiyo.submitRevision\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_kiyo_submit_revision"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kiyo"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="kiyo_submit_revision" name="kiyo submit revision" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.kiyo.submitRevision", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="XRPC / on-demand">\n'
                 '      <bpmn:outgoing>Flow_Start</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start" sourceRef="Start_Manual" '
                 'targetRef="Task_ValidateOwner"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ValidateOwner" name="validate paper owner">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kiyo.validateOwner"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=paperId"     target="paperId"/>\n'
                 '          <zeebe:input  source="=callerDid"   target="callerDid"/>\n'
                 '          <zeebe:output source="=valid"       target="ownerValid"/>\n'
                 '          <zeebe:output source="=nextVersion" target="nextVersion"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterValidate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterValidate" sourceRef="Task_ValidateOwner" '
                 'targetRef="Task_PinRevision"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_PinRevision" name="pin new version to '
                 'ipfs.etzhayyim.com">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://ip5s7b2x.etzhayyim.com/xrpc/etzhayyim.ipfs.v1.IpfsCommandService/Publish&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="=&quot;POST&quot;"             target="method"/>\n'
                 '          <zeebe:input source="=&quot;application/json&quot;" '
                 'target="contentType"/>\n'
                 '          <zeebe:input source="={content_base64: fileBase64, content_type: '
                 'fileContentType}" target="body"/>\n'
                 '          <zeebe:input source="=30000"                        '
                 'target="timeoutMs"/>\n'
                 '          <zeebe:output source="=bodyJson.cid"  target="newIpfsCid"/>\n'
                 '          <zeebe:output source="=status"        target="ipfsStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterPin</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterPin" sourceRef="Task_PinRevision" '
                 'targetRef="Task_InsertRevision"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_InsertRevision" name="insert revision + update '
                 'paper">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kiyo.insertRevision"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=paperId"      target="paperId"/>\n'
                 '          <zeebe:input source="=nextVersion"  target="version"/>\n'
                 '          <zeebe:input source="=newIpfsCid"   target="ipfsCid"/>\n'
                 '          <zeebe:input source="=callerDid"    target="ownerDid"/>\n'
                 '          <zeebe:output source="=revisionVertexId" target="revisionVertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_InsertRevision" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="revision inserted"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3589,
                 '00-contracts/bpmn/com/etzhayyim/kiyo/submitRevision.bpmn',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-submit-revision-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-submit-revision-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'com.etzhayyim.apps.kiyo.submitRevision',
                 'kiyo_submit_revision',
                 60000,
                 'vertex_kiyo_revision,vertex_kiyo_paper',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-submit-revision-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-citation-sync-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_citation_sync',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer R/P1D — fetch text from IPFS → LangGraph citation extractor\n'
                 '               → resolve DOIs via bunken → insert edge_kiyo_cites\n'
                 '  NSID: com.etzhayyim.apps.kiyo.citationSync\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_kiyo_citation_sync"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kiyo"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="kiyo_citation_sync" name="kiyo citation sync" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.kiyo.citationSync", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every day">\n'
                 '      <bpmn:outgoing>Flow_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P1D">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="on-demand">\n'
                 '      <bpmn:outgoing>Flow_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer"  sourceRef="Start_Timer"  '
                 'targetRef="Task_FetchPapers"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_FetchPapers"/>\n'
                 '\n'
                 "    <!-- 1. Select papers whose citations haven't been synced in 24h -->\n"
                 '    <bpmn:serviceTask id="Task_FetchPapers" name="select unsynced papers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT paper_id, ipfs_cid FROM '
                 "vertex_kiyo_paper WHERE ipfs_cid IS NOT NULL AND status = 'active' ORDER BY "
                 'submitted_at DESC LIMIT 50&quot;" target="sql"/>\n'
                 '          <zeebe:output source="=rows" target="papers"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterFetch</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterFetch" sourceRef="Task_FetchPapers" '
                 'targetRef="Task_ExtractCitations"/>\n'
                 '\n'
                 '    <!-- 2. LangGraph: IPFS fetch → LLM citation extract → bunken DOI resolve '
                 '-->\n'
                 '    <bpmn:serviceTask id="Task_ExtractCitations" name="LangGraph citation '
                 'extract">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kiyo.extractCitations"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=papers"           target="papers"/>\n'
                 '          <zeebe:input  source="=50"               target="maxPapers"/>\n'
                 '          <zeebe:output source="=citationEdges"    target="citationEdges"/>\n'
                 '          <zeebe:output source="=processedCount"   target="processedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterExtract</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterExtract" sourceRef="Task_ExtractCitations" '
                 'targetRef="Task_InsertEdges"/>\n'
                 '\n'
                 '    <!-- 3. Insert edge_kiyo_cites rows -->\n'
                 '    <bpmn:serviceTask id="Task_InsertEdges" name="insert citation edges">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kiyo.insertCitationEdges"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=citationEdges"  target="edges"/>\n'
                 '          <zeebe:output source="=insertedCount"  target="insertedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_InsertEdges" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="citations synced"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3705,
                 '00-contracts/bpmn/com/etzhayyim/kiyo/citationSync.bpmn',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-citation-sync-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-citation-sync-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'com.etzhayyim.apps.kiyo.citationSync',
                 'kiyo_citation_sync',
                 300000,
                 'edge_kiyo_cites',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-citation-sync-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-embedding-index-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_embedding_index',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer R/P1D — embed abstracts of new papers via murakumo\n'
                 '  LangGraph batch embedding → UPDATE vertex_kiyo_paper.embedding\n'
                 '  NSID: com.etzhayyim.apps.kiyo.embeddingIndex\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_kiyo_embedding_index"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kiyo"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="kiyo_embedding_index" name="kiyo embedding index" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.kiyo.embeddingIndex", "version": 1, '
                 '"resultTimeoutMs": 180000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every day">\n'
                 '      <bpmn:outgoing>Flow_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P1D">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="on-demand">\n'
                 '      <bpmn:outgoing>Flow_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer"  sourceRef="Start_Timer"  '
                 'targetRef="Task_FetchUnembedded"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_FetchUnembedded"/>\n'
                 '\n'
                 '    <!-- 1. Select papers without embedding -->\n'
                 '    <bpmn:serviceTask id="Task_FetchUnembedded" name="select papers without '
                 'embedding">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT paper_id, title, abstract FROM '
                 "vertex_kiyo_paper WHERE embedding IS NULL AND status = 'active' LIMIT "
                 '100&quot;" target="sql"/>\n'
                 '          <zeebe:output source="=rows" target="papers"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterFetch</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterFetch" sourceRef="Task_FetchUnembedded" '
                 'targetRef="Task_EmbedBatch"/>\n'
                 '\n'
                 '    <!-- 2. LangGraph: batch embed title+abstract via murakumo -->\n'
                 '    <bpmn:serviceTask id="Task_EmbedBatch" name="embed abstracts via '
                 'LangGraph">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kiyo.embedAbstracts"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=papers"       target="papers"/>\n'
                 '          <zeebe:output source="=embeddings"   target="embeddings"/>\n'
                 '          <zeebe:output source="=embeddedCount" target="embeddedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterEmbed</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterEmbed" sourceRef="Task_EmbedBatch" '
                 'targetRef="Task_UpdateEmbeddings"/>\n'
                 '\n'
                 '    <!-- 3. Batch-update vertex_kiyo_paper.embedding -->\n'
                 '    <bpmn:serviceTask id="Task_UpdateEmbeddings" name="persist embeddings">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kiyo.persistEmbeddings"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=embeddings"   target="embeddings"/>\n'
                 '          <zeebe:output source="=updatedCount" target="updatedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_UpdateEmbeddings" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="embeddings indexed"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3577,
                 '00-contracts/bpmn/com/etzhayyim/kiyo/embeddingIndex.bpmn',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-embedding-index-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-embedding-index-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'com.etzhayyim.apps.kiyo.embeddingIndex',
                 'kiyo_embedding_index',
                 180000,
                 'vertex_kiyo_paper',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-embedding-index-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-weekly-digest-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'kiyo_weekly_digest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer R/P7D — select top-cited papers → LLM digest → AT post\n'
                 '  NSID: com.etzhayyim.apps.kiyo.weeklyDigest\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_kiyo_weekly_digest"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kiyo"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="kiyo_weekly_digest" name="kiyo weekly digest" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.kiyo.weeklyDigest", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 7 days">\n'
                 '      <bpmn:outgoing>Flow_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P7D">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="on-demand">\n'
                 '      <bpmn:outgoing>Flow_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer"  sourceRef="Start_Timer"  '
                 'targetRef="Task_SelectTop"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_SelectTop"/>\n'
                 '\n'
                 '    <!-- 1. Select top-10 papers by citation+endorsement this week -->\n'
                 '    <bpmn:serviceTask id="Task_SelectTop" name="select top papers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT p.paper_id, p.title, p.abstract, '
                 'COALESCE(s.citation_in_count,0)+COALESCE(s.endorsement_count,0) AS score FROM '
                 'vertex_kiyo_paper p LEFT JOIN mv_kiyo_paper_stats s ON s.paper_id=p.paper_id '
                 'WHERE p.status=\'active\' ORDER BY score DESC LIMIT 10&quot;" target="sql"/>\n'
                 '          <zeebe:output source="=rows" target="topPapers"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterSelect</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterSelect" sourceRef="Task_SelectTop" '
                 'targetRef="Task_GenerateDigest"/>\n'
                 '\n'
                 '    <!-- 2. LLM: generate digest text -->\n'
                 '    <bpmn:serviceTask id="Task_GenerateDigest" name="generate weekly digest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;You are the editorial bot for kiyo.etzhayyim.com '
                 '(紀要), a self-hosted research archive. Summarize the top papers of the week in '
                 '280 characters or less (Japanese or English). Include paper IDs.&quot;" '
                 'target="systemPrompt"/>\n'
                 '          <zeebe:input source="=&quot;Top papers this week:\\n&quot; + '
                 'string(topPapers)" target="userPrompt"/>\n'
                 '          <zeebe:input source="={digestText: {type: '
                 '&quot;string&quot;}}"                target="schema"/>\n'
                 '          <zeebe:output source="=result.digestText" target="digestText"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_AfterLlm</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterLlm" sourceRef="Task_GenerateDigest" '
                 'targetRef="Task_PostDigest"/>\n'
                 '\n'
                 '    <!-- 3. Post to AT Protocol -->\n'
                 '    <bpmn:serviceTask id="Task_PostDigest" name="post weekly digest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;app.bsky.feed.post&quot;"     '
                 'target="type"/>\n'
                 '          <zeebe:input source="=&quot;did:web:kiyo.etzhayyim.com&quot;"  '
                 'target="did"/>\n'
                 '          <zeebe:input source="=&quot;📚 kiyo weekly digest\\n&quot; + '
                 'digestText" target="text"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_PostDigest" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="digest posted"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4033,
                 '00-contracts/bpmn/com/etzhayyim/kiyo/weeklyDigest.bpmn',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-weekly-digest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-weekly-digest-v1',
                 'did:web:kiyo.etzhayyim.com',
                 'com.etzhayyim.apps.kiyo.weeklyDigest',
                 'kiyo_weekly_digest',
                 60000,
                 '',
                 '2026-04-30T23:01:00+09:00',
                 'did:web:kiyo.etzhayyim.com',
                 'did:web:kiyo.etzhayyim.com',
                 'sys.bpmn.seed.kiyo',
                 'did:web:kiyo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-weekly-digest-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-submit-paper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-submit-paper-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-submit-revision-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-submit-revision-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-citation-sync-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-citation-sync-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-embedding-index-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-embedding-index-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-weekly-digest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-weekly-digest-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
