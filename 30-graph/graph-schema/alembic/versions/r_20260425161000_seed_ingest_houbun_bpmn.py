"""Captured from Kysely migration 20260425161000_seed_ingest_houbun_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425161000_seed_ingest_houbun_bpmn"
down_revision = 'r_20260425160000_vertex_ingest_spine'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'ingest_houbun_egov_jpn_delta',\n"
         "           1, $3, CAST($4 AS integer), $5, 'active',\n"
         '           $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/ingest-houbun-egov-jpn-delta-v1',
                 'did:web:ingest.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_ingest_houbun_egov_jpn_delta"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/ingest"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="ingest_houbun_egov_jpn_delta" name="ingest houbun e-Gov JPN '
                 'delta" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="start">\n'
                 '      <bpmn:outgoing>Flow_CreateRun</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_CreateRun" sourceRef="Start" '
                 'targetRef="Task_CreateRun"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_CreateRun" name="create run">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="houbun.createRun" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_CreateRun</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Health</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health" sourceRef="Task_CreateRun" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rw.health.probe" retries="1"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=healthy" target="rwHealthy"/>\n'
                 '          <zeebe:output source="=reason" target="rwHealthReason"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Health</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_HealthGate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_HealthGate" sourceRef="Task_Health" '
                 'targetRef="Gateway_RwHealthy"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gateway_RwHealthy" name="RisingWave healthy?" '
                 'default="Flow_RwDegraded">\n'
                 '      <bpmn:incoming>Flow_HealthGate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Plan</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_RwDegraded</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Plan" sourceRef="Gateway_RwHealthy" '
                 'targetRef="Task_Plan">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=rwHealthy = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_RwDegraded" sourceRef="Gateway_RwHealthy" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Plan" name="plan e-Gov JPN shard">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="houbun.egovJpn.plan" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Plan</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AcquireCursor</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AcquireCursor" sourceRef="Task_Plan" '
                 'targetRef="Task_AcquireCursor"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AcquireCursor" name="acquire cursor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="houbun.acquireCursor" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_AcquireCursor</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Fetch</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fetch" sourceRef="Task_AcquireCursor" '
                 'targetRef="Task_Fetch"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch e-Gov law">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="houbun.egovJpn.fetch" retries="3"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Fetch</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_WriteGraph</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_WriteGraph" sourceRef="Task_Fetch" '
                 'targetRef="Task_WriteGraph"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_WriteGraph" name="write houbun graph">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="houbun.writeGraph" retries="3"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_WriteGraph</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_IpfsPin</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_IpfsPin" sourceRef="Task_WriteGraph" '
                 'targetRef="Task_IpfsPin"/>\n'
                 '\n'
                 '    <!-- Pin fetched document WebP to IPFS after graph write.\n'
                 '         source_url must be set by houbun.egovJpn.fetch as the canonical '
                 'document URL.\n'
                 '         Output ipfs_cid / ipfs_url are carried forward for audit. -->\n'
                 '    <bpmn:serviceTask id="Task_IpfsPin" name="pin to IPFS">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="ipfs.add" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=document_url" target="source_url"/>\n'
                 '          <zeebe:input source="=document_filename" target="filename"/>\n'
                 '          <zeebe:output source="=cid" target="ipfs_cid"/>\n'
                 '          <zeebe:output source="=ipfs_url" target="ipfs_url"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_IpfsPin</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Verify</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Verify" sourceRef="Task_IpfsPin" '
                 'targetRef="Task_Verify"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Verify" name="verify visibility">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="houbun.verifyVisibility" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Verify</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AdvanceCursor</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AdvanceCursor" sourceRef="Task_Verify" '
                 'targetRef="Task_AdvanceCursor"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AdvanceCursor" name="advance cursor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="houbun.advanceCursor" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_AdvanceCursor</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Complete</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Complete" sourceRef="Task_AdvanceCursor" '
                 'targetRef="Task_Complete"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Complete" name="complete run">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="houbun.completeRun" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Complete</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Complete" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit houbun e-Gov delta audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;app.etzhayyim.ingest.houbunEgovJpnDelta.completed&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;processId&quot;: '
                 '&quot;ingest_houbun_egov_jpn_delta&quot;, &quot;runId&quot;: runId, '
                 '&quot;rwHealthy&quot;: rwHealthy, &quot;rwHealthReason&quot;: rwHealthReason, '
                 '&quot;phase&quot;: if rwHealthy = true then &quot;completed&quot; else '
                 '&quot;rw-degraded&quot; }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_RwDegraded</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="completed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7275,
                 '00-contracts/bpmn/ai/gftd/ingest/houbunEgovJpnDelta.bpmn',
                 '2026-04-25T16:10:00Z',
                 'did:web:ingest.etzhayyim.com',
                 'did:web:ingest.etzhayyim.com',
                 'sys.bpmn.seed.ingest-houbun',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/ingest-houbun-egov-jpn-delta-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'app.etzhayyim.apps.ingest.start',\n"
         "           'ingest_houbun_egov_jpn_delta', 1, CAST(0 AS integer), 'active',\n"
         '           $3, 1, $4, $5, $6\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $7)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/ingest-start-houbun-egov-jpn-delta-v1',
                 'did:web:ingest.etzhayyim.com',
                 '2026-04-25T16:10:00Z',
                 'did:web:ingest.etzhayyim.com',
                 'did:web:ingest.etzhayyim.com',
                 'sys.bpmn.seed.ingest-houbun',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/ingest-start-houbun-egov-jpn-delta-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/ingest-start-houbun-egov-jpn-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/ingest-houbun-egov-jpn-delta-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
