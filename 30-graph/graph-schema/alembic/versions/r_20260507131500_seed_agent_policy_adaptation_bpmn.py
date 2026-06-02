"""Captured from Kysely migration 20260507131500_seed_agent_policy_adaptation_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507131500_seed_agent_policy_adaptation_bpmn"
down_revision = 'r_20260507131400_vertex_agent_policy_adaptation_proposal'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '       actor_id, actor_did, org_did)\n'
         '    SELECT\n'
         "      $1, $2, 'agent_policy_adaptation', 1,\n"
         "      $3, CAST($4 AS integer), $5, 'active',\n"
         '      $6, 1, $7, $8, $9,\n'
         "      $10, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/agent-policy-adaptation-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Agent policy adaptation — ADR-2605061200.\n'
                 '\n'
                 '  Inputs:\n'
                 '    agentDid\n'
                 '    preferenceKey\n'
                 '    proposal\n'
                 '    mokutekiGatePass\n'
                 '    tripleWitnessPass\n'
                 '    currentPreference\n'
                 '    maxWeightDelta\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_agent_policy_adaptation"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/agent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="agent_policy_adaptation" name="Agent policy adaptation" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="manual / timer">\n'
                 '      <bpmn:outgoing>Flow_Start_Adapt</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Adapt" sourceRef="Start" '
                 'targetRef="Task_Adapt"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Adapt" name="Build bounded policy adaptation">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.adaptPolicy"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=agentDid" target="agentDid"/>\n'
                 '          <zeebe:input source="=preferenceKey" target="preferenceKey"/>\n'
                 '          <zeebe:input source="=proposal" target="proposal"/>\n'
                 '          <zeebe:input source="=mokutekiGatePass" target="mokutekiGatePass"/>\n'
                 '          <zeebe:input source="=tripleWitnessPass" target="tripleWitnessPass"/>\n'
                 '          <zeebe:input source="=currentPreference" target="currentPreference"/>\n'
                 '          <zeebe:input source="=if maxWeightDelta = null then 0.2 else '
                 'maxWeightDelta" target="maxWeightDelta"/>\n'
                 '          <zeebe:output source="=accepted" target="policyAccepted"/>\n'
                 '          <zeebe:output source="=blockers" target="policyBlockers"/>\n'
                 '          <zeebe:output source="=policyProposal" target="policyProposal"/>\n'
                 '          <zeebe:output source="=preference" target="preference"/>\n'
                 '          <zeebe:output source="=proposalHash" target="proposalHash"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Adapt</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Adapt_WriteProposal</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Adapt_WriteProposal" sourceRef="Task_Adapt" '
                 'targetRef="Task_WriteProposal"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_WriteProposal" name="Record policy adaptation '
                 'proposal">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_agent_policy_adaptation_proposal&quot;" target="table"/>\n'
                 '          <zeebe:input source="=policyProposal" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:input source="=&quot;agent_policy_adaptation&quot;" '
                 'target="_bpmnProcessId"/>\n'
                 '          <zeebe:output source="=inserted" target="policyProposalInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Adapt_WriteProposal</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_WriteProposal_Gateway</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_WriteProposal_Gateway" '
                 'sourceRef="Task_WriteProposal" targetRef="Gateway_Accepted"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gateway_Accepted" name="accepted?" '
                 'default="Flow_Accepted_AuditBlocked">\n'
                 '      <bpmn:incoming>Flow_WriteProposal_Gateway</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Accepted_WritePreference</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Accepted_AuditBlocked</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Accepted_WritePreference" '
                 'sourceRef="Gateway_Accepted" targetRef="Task_WritePreference">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">=policyAccepted = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Accepted_AuditBlocked" '
                 'sourceRef="Gateway_Accepted" targetRef="Task_AuditBlocked"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_WritePreference" name="Activate bounded prior '
                 'preference">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_agent_prior_preference&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=preference" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:input source="=&quot;agent_policy_adaptation&quot;" '
                 'target="_bpmnProcessId"/>\n'
                 '          <zeebe:output source="=inserted" target="preferenceInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Accepted_WritePreference</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_WritePreference_AuditAccepted</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_WritePreference_AuditAccepted" '
                 'sourceRef="Task_WritePreference" targetRef="Task_AuditAccepted"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditAccepted" name="Audit policy adaptation '
                 'accepted">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;agent.policyAdaptation.accepted&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;agentDid&quot;: agentDid, '
                 '&quot;preferenceKey&quot;: preferenceKey, &quot;proposalHash&quot;: '
                 'proposalHash, &quot;proposalInserted&quot;: policyProposalInserted, '
                 '&quot;preferenceInserted&quot;: preferenceInserted }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_WritePreference_AuditAccepted</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AuditAccepted_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AuditAccepted_End" '
                 'sourceRef="Task_AuditAccepted" targetRef="End_Accepted"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditBlocked" name="Audit policy adaptation '
                 'blocked">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;agent.policyAdaptation.blocked&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;agentDid&quot;: agentDid, '
                 '&quot;preferenceKey&quot;: preferenceKey, &quot;proposalHash&quot;: '
                 'proposalHash, &quot;proposalInserted&quot;: policyProposalInserted, '
                 '&quot;blockers&quot;: policyBlockers }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Accepted_AuditBlocked</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AuditBlocked_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AuditBlocked_End" sourceRef="Task_AuditBlocked" '
                 'targetRef="End_Blocked"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End_Accepted" name="accepted">\n'
                 '      <bpmn:incoming>Flow_AuditAccepted_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:endEvent id="End_Blocked" name="blocked">\n'
                 '      <bpmn:incoming>Flow_AuditBlocked_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 6970,
                 '00-contracts/bpmn/com/etzhayyim/agent/policyAdaptation.bpmn',
                 '2026-05-07T13:15:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.agent-policy-adaptation',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/agent-policy-adaptation-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '       result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '       sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '    SELECT\n'
         "      $1, $2, 'com.etzhayyim.apps.agent.adaptPolicy',\n"
         "      'agent_policy_adaptation', 1, 120000,\n"
         "      'vertex_agent_policy_adaptation_proposal,vertex_agent_prior_preference',\n"
         "      'active', $3, 1, $4, $5, $6,\n"
         "      $7, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/agent-policy-adaptation-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '2026-05-07T13:15:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.agent-policy-adaptation',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/agent-policy-adaptation-v1']}]

DOWN = [{'sql': '\n    DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/agent-policy-adaptation-v1']},
 {'sql': '\n    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/agent-policy-adaptation-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
