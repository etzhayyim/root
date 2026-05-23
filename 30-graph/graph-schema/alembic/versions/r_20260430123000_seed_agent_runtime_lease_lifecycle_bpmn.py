"""Captured from Kysely migration 20260430123000_seed_agent_runtime_lease_lifecycle_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430123000_seed_agent_runtime_lease_lifecycle_bpmn"
down_revision = 'r_20260430120000_vertex_agent_economy'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/agent-runtime-lease-lifecycle-v1',
                 'did:web:agent.etzhayyim.com',
                 'agent_runtime_lease_lifecycle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  ai.gftd.apps.agent.runtimeLeaseLifecycle — ADR-2604301200 P2.\n'
                 '\n'
                 '  XRPC/message-started process for reserving a persistent autonomous-agent\n'
                 '  runtime lease. The k8s namespace is always explicit; `default` is rejected\n'
                 '  again by the worker primitive.\n'
                 '\n'
                 '  Flow:\n'
                 '    Start -> Quote runtime bond -> Reserve runtime lease -> Audit -> End\n'
                 '\n'
                 '  Inputs:\n'
                 '    rootDid, agentDid\n'
                 '    runtimeNamespace default "yoro-actors"\n'
                 '    runtimeKind default "zeebe-langgraph"\n'
                 '    cpuMillicores, memoryMiB, gpuClass, gpuSecondsCapDay\n'
                 '    storageGiB, networkEgressGiBDay, maxParallelJobs, leasePeriodSec\n'
                 '    resourcePolicyCid, slashPolicyHash\n'
                 '    submitOnChain default false\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_agent_runtime_lease_lifecycle"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/agent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="agent_runtime_lease_lifecycle" name="agent runtime lease '
                 'lifecycle" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      '
                 '{"nsid":"ai.gftd.apps.agent.runtimeLeaseLifecycle","version":1,"tier":"T2"}\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="runtime lease request">\n'
                 '      <bpmn:outgoing>Flow_ToQuote</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToQuote" sourceRef="Start" '
                 'targetRef="Task_Quote"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Quote" name="quote runtime">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.runtime.quote" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=rootDid" target="rootDid"/>\n'
                 '          <zeebe:input source="=agentDid" target="agentDid"/>\n'
                 '          <zeebe:input source="=if runtimeKind = null then '
                 '&quot;zeebe-langgraph&quot; else runtimeKind" target="runtimeKind"/>\n'
                 '          <zeebe:input source="=if runtimeNamespace = null then '
                 '&quot;yoro-actors&quot; else runtimeNamespace" target="runtimeNamespace"/>\n'
                 '          <zeebe:input source="=if cpuMillicores = null then 500 else '
                 'cpuMillicores" target="cpuMillicores"/>\n'
                 '          <zeebe:input source="=if memoryMiB = null then 1024 else memoryMiB" '
                 'target="memoryMiB"/>\n'
                 '          <zeebe:input source="=if gpuClass = null then &quot;none&quot; else '
                 'gpuClass" target="gpuClass"/>\n'
                 '          <zeebe:input source="=if gpuSecondsCapDay = null then 0 else '
                 'gpuSecondsCapDay" target="gpuSecondsCapDay"/>\n'
                 '          <zeebe:input source="=if storageGiB = null then 10 else storageGiB" '
                 'target="storageGiB"/>\n'
                 '          <zeebe:input source="=if networkEgressGiBDay = null then 1 else '
                 'networkEgressGiBDay" target="networkEgressGiBDay"/>\n'
                 '          <zeebe:input source="=if maxParallelJobs = null then 1 else '
                 'maxParallelJobs" target="maxParallelJobs"/>\n'
                 '          <zeebe:input source="=if leasePeriodSec = null then 86400 else '
                 'leasePeriodSec" target="leasePeriodSec"/>\n'
                 '          <zeebe:input source="=if riskMultiplierBps = null then 10000 else '
                 'riskMultiplierBps" target="riskMultiplierBps"/>\n'
                 '          <zeebe:output source="=baseCostGccWei" target="baseCostGccWei"/>\n'
                 '          <zeebe:output source="=riskAdjustedCostGccWei" '
                 'target="riskAdjustedCostGccWei"/>\n'
                 '          <zeebe:output source="=bondGccWei" target="bondGccWei"/>\n'
                 '          <zeebe:output source="=resourceHash" target="resourceHash"/>\n'
                 '          <zeebe:output source="=escrowAddr" target="escrowAddr"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToQuote</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToReserve</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToReserve" sourceRef="Task_Quote" '
                 'targetRef="Task_Reserve"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Reserve" name="reserve runtime">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.runtime.reserve" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=rootDid" target="rootDid"/>\n'
                 '          <zeebe:input source="=agentDid" target="agentDid"/>\n'
                 '          <zeebe:input source="=if leaseId = null then &quot;&quot; else '
                 'leaseId" target="leaseId"/>\n'
                 '          <zeebe:input source="=if runtimeKind = null then '
                 '&quot;zeebe-langgraph&quot; else runtimeKind" target="runtimeKind"/>\n'
                 '          <zeebe:input source="=if runtimeNamespace = null then '
                 '&quot;yoro-actors&quot; else runtimeNamespace" target="runtimeNamespace"/>\n'
                 '          <zeebe:input source="=if cpuMillicores = null then 500 else '
                 'cpuMillicores" target="cpuMillicores"/>\n'
                 '          <zeebe:input source="=if memoryMiB = null then 1024 else memoryMiB" '
                 'target="memoryMiB"/>\n'
                 '          <zeebe:input source="=if gpuClass = null then &quot;none&quot; else '
                 'gpuClass" target="gpuClass"/>\n'
                 '          <zeebe:input source="=if gpuSecondsCapDay = null then 0 else '
                 'gpuSecondsCapDay" target="gpuSecondsCapDay"/>\n'
                 '          <zeebe:input source="=if storageGiB = null then 10 else storageGiB" '
                 'target="storageGiB"/>\n'
                 '          <zeebe:input source="=if networkEgressGiBDay = null then 1 else '
                 'networkEgressGiBDay" target="networkEgressGiBDay"/>\n'
                 '          <zeebe:input source="=if maxParallelJobs = null then 1 else '
                 'maxParallelJobs" target="maxParallelJobs"/>\n'
                 '          <zeebe:input source="=if leasePeriodSec = null then 86400 else '
                 'leasePeriodSec" target="leasePeriodSec"/>\n'
                 '          <zeebe:input source="=bondGccWei" target="bondGccWei"/>\n'
                 '          <zeebe:input source="=if resourcePolicyCid = null then &quot;&quot; '
                 'else resourcePolicyCid" target="resourcePolicyCid"/>\n'
                 '          <zeebe:input source="=if slashPolicyHash = null then &quot;&quot; else '
                 'slashPolicyHash" target="slashPolicyHash"/>\n'
                 '          <zeebe:input source="=if submitOnChain = null then false else '
                 'submitOnChain" target="submitOnChain"/>\n'
                 '          <zeebe:output source="=leaseId" target="leaseId"/>\n'
                 '          <zeebe:output source="=vertexId" target="runtimeLeaseVertexId"/>\n'
                 '          <zeebe:output source="=expiresAt" target="runtimeLeaseExpiresAt"/>\n'
                 '          <zeebe:output source="=pendingOnChain" '
                 'target="runtimeLeasePendingOnChain"/>\n'
                 '          <zeebe:output source="=onchain.txHash" target="runtimeLeaseTxHash"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToReserve</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Reserve" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit runtime lease">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:agent.etzhayyim.com:runtime&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;agent.runtime.lease.reserve&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '            rootDid: rootDid,\n'
                 '            agentDid: agentDid,\n'
                 '            leaseId: leaseId,\n'
                 '            runtimeNamespace: if runtimeNamespace = null then '
                 '&quot;yoro-actors&quot; else runtimeNamespace,\n'
                 '            bondGccWei: bondGccWei,\n'
                 '            resourceHash: resourceHash,\n'
                 '            pendingOnChain: runtimeLeasePendingOnChain,\n'
                 '            txHash: runtimeLeaseTxHash,\n'
                 '            vertexId: runtimeLeaseVertexId\n'
                 '          }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="runtimeLeaseAuditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="reserved">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7695,
                 '00-contracts/bpmn/ai/gftd/agent/runtimeLeaseLifecycle.bpmn',
                 '2026-04-30T12:30:00Z',
                 'did:web:agent.etzhayyim.com',
                 'did:web:agent.etzhayyim.com',
                 'sys.bpmn.seed.agent.runtimeLeaseLifecycle',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/agent-runtime-lease-lifecycle-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/agent-runtimeLeaseLifecycle-v1',
                 'did:web:agent.etzhayyim.com',
                 'ai.gftd.apps.agent.runtimeLeaseLifecycle',
                 'agent_runtime_lease_lifecycle',
                 90000,
                 '2026-04-30T12:30:00Z',
                 'did:web:agent.etzhayyim.com',
                 'did:web:agent.etzhayyim.com',
                 'sys.bpmn.seed.agent.runtimeLeaseLifecycle',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/agent-runtimeLeaseLifecycle-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/agent-runtimeLeaseLifecycle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/agent-runtime-lease-lifecycle-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
