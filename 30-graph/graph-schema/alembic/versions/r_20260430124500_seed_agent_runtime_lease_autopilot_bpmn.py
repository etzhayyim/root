"""Captured from Kysely migration 20260430124500_seed_agent_runtime_lease_autopilot_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430124500_seed_agent_runtime_lease_autopilot_bpmn"
down_revision = 'r_20260430123000_seed_agent_runtime_lease_lifecycle_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, $3, 1, $4,\n'
         "           CAST($5 AS integer), $6, 'active', $7,\n"
         '           1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:agent.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-runtime-lease-autopilot-v1',
                 'did:web:agent.gftd.ai',
                 'agent_runtime_lease_autopilot',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  agent_runtime_lease_autopilot — ADR-2604301200 P3.\n'
                 '\n'
                 '  Timer-started persistent lifecycle loop for autonomous agents. Every 15\n'
                 '  minutes, or on an operator manual start, it asks the worker to renew\n'
                 '  near-expiring leases, hibernate leases that passed the grace window, and\n'
                 '  reserve a runtime for active economy profiles that do not have one.\n'
                 '\n'
                 '  The runtime namespace is explicit and never defaults to the k8s default\n'
                 '  namespace; the worker rejects `default` again before any insert/action.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_agent_runtime_lease_autopilot"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/agent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process\n'
                 '      id="agent_runtime_lease_autopilot"\n'
                 '      name="agent runtime lease autopilot"\n'
                 '      isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      {"adr":"2604301200","tier":"T2","trigger":"timer","interval":"R/PT15M"}\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 15 minutes">\n'
                 '      <bpmn:outgoing>Flow_ToAutopilot</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT15M">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAutopilot" sourceRef="Start_Timer" '
                 'targetRef="Task_Autopilot"/>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="operator tick">\n'
                 '      <bpmn:outgoing>Flow_Manual_ToAutopilot</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow\n'
                 '        id="Flow_Manual_ToAutopilot"\n'
                 '        sourceRef="Start_Manual"\n'
                 '        targetRef="Task_Autopilot"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Autopilot" name="runtime lease autopilot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.runtime.autopilotTick" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=21600" target="renewWindowSec"/>\n'
                 '          <zeebe:input source="=3600" target="hibernateGraceSec"/>\n'
                 '          <zeebe:input source="=86400" target="defaultLeasePeriodSec"/>\n'
                 '          <zeebe:input source="=true" target="startMissingProfiles"/>\n'
                 '          <zeebe:input source="=true" target="autoRenew"/>\n'
                 '          <zeebe:input source="=false" target="submitOnChain"/>\n'
                 '          <zeebe:input source="=&quot;zeebe-langgraph&quot;" '
                 'target="runtimeKind"/>\n'
                 '          <zeebe:input source="=&quot;yoro-actors&quot;" '
                 'target="runtimeNamespace"/>\n'
                 '          <zeebe:input source="=50" target="limit"/>\n'
                 '          <zeebe:output source="=renewed" '
                 'target="runtimeLeaseAutopilotRenewed"/>\n'
                 '          <zeebe:output source="=hibernated" '
                 'target="runtimeLeaseAutopilotHibernated"/>\n'
                 '          <zeebe:output source="=started" '
                 'target="runtimeLeaseAutopilotStarted"/>\n'
                 '          <zeebe:output source="=errors" target="runtimeLeaseAutopilotErrors"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAutopilot</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Manual_ToAutopilot</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Autopilot" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit autopilot tick">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:agent.gftd.ai:runtime&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;agent.runtime.autopilot.tick&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '            renewed: runtimeLeaseAutopilotRenewed,\n'
                 '            hibernated: runtimeLeaseAutopilotHibernated,\n'
                 '            started: runtimeLeaseAutopilotStarted,\n'
                 '            errors: runtimeLeaseAutopilotErrors,\n'
                 '            runtimeNamespace: &quot;yoro-actors&quot;\n'
                 '          }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" '
                 'target="runtimeLeaseAutopilotAuditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="autopilot tick complete">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4549,
                 '00-contracts/bpmn/ai/gftd/agent/runtimeLeaseAutopilot.bpmn',
                 '2026-04-30T12:45:00Z',
                 'did:web:agent.gftd.ai',
                 'did:web:agent.gftd.ai',
                 'sys.bpmn.seed.agent.runtime.autopilot',
                 'at://did:web:agent.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-runtime-lease-autopilot-v1']}]

DOWN = [{'sql': '\n    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:agent.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-runtime-lease-autopilot-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
