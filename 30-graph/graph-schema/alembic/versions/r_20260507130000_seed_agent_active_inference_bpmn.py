"""Captured from Kysely migration 20260507130000_seed_agent_active_inference_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507130000_seed_agent_active_inference_bpmn"
down_revision = 'r_20260507120100_seed_shosha_sanctions_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-active-inference-tick-v1',
                 'did:web:bpmn.gftd.ai',
                 'agent_active_inference_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Active Inference tick — ADR-2605061200 / ADR-2605061300.\n'
                 '\n'
                 '  Inputs:\n'
                 '    agentDid\n'
                 '    tickKind\n'
                 '    beliefSnapshotHash\n'
                 '    candidateActions\n'
                 '    mokutekiGatePass\n'
                 '\n'
                 '  Outputs:\n'
                 '    selectedActionId\n'
                 '    expectedFreeEnergy\n'
                 '    rejectedActions\n'
                 '    tickInserted\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_agent_active_inference_tick"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/agent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="agent_active_inference_tick" name="Agent active inference '
                 'tick" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="manual / timer">\n'
                 '      <bpmn:outgoing>Flow_Start_Evaluate</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Evaluate" sourceRef="Start" '
                 'targetRef="Task_Evaluate"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Evaluate" name="Evaluate expected free energy">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.evaluateExpectedFreeEnergy"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=candidateActions" target="candidateActions"/>\n'
                 '          <zeebe:input source="=mokutekiGatePass" target="mokutekiGatePass"/>\n'
                 '          <zeebe:input source="=true" target="requireSafetyFloor"/>\n'
                 '          <zeebe:output source="=selectedActionId" target="selectedActionId"/>\n'
                 '          <zeebe:output source="=expectedFreeEnergy" '
                 'target="expectedFreeEnergy"/>\n'
                 '          <zeebe:output source="=rejected" target="rejectedActions"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Evaluate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Evaluate_WriteTick</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Evaluate_WriteTick" sourceRef="Task_Evaluate" '
                 'targetRef="Task_WriteTick"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_WriteTick" name="Record active inference tick">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.recordActiveInferenceTick"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=agentDid" target="agentDid"/>\n'
                 '          <zeebe:input source="=tickKind" target="tickKind"/>\n'
                 '          <zeebe:input source="=beliefSnapshotHash" '
                 'target="beliefSnapshotHash"/>\n'
                 '          <zeebe:input source="=candidateActions" target="candidateActions"/>\n'
                 '          <zeebe:input source="=expectedFreeEnergy" '
                 'target="expectedFreeEnergy"/>\n'
                 '          <zeebe:input source="=selectedActionId" target="selectedActionId"/>\n'
                 '          <zeebe:input source="=mokutekiGatePass" target="mokutekiGatePass"/>\n'
                 '          <zeebe:input source="=string(now())" target="createdAt"/>\n'
                 '          <zeebe:input source="=tickId" target="tickId"/>\n'
                 '          <zeebe:output source="=inserted" target="tickInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Evaluate_WriteTick</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_WriteTick_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_WriteTick_Audit" sourceRef="Task_WriteTick" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="Emit active inference audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;agent.activeInference.tick&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;agentDid&quot;: agentDid, '
                 '&quot;selectedActionId&quot;: selectedActionId, &quot;expectedFreeEnergy&quot;: '
                 'expectedFreeEnergy, &quot;rejected&quot;: rejectedActions, &quot;inserted&quot;: '
                 'tickInserted }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_WriteTick_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4101,
                 '00-contracts/bpmn/ai/gftd/agent/activeInferenceTick.bpmn',
                 '2026-05-07T13:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'sys.bpmn.seed.agent-active-inference',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-active-inference-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '         result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '         sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        120000, $5, 'active', $6,\n"
         "        1, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-active-inference-tick-v1',
                 'did:web:bpmn.gftd.ai',
                 'ai.gftd.apps.agent.activeInferenceTick',
                 'agent_active_inference_tick',
                 'vertex_agent_active_inference_tick',
                 '2026-05-07T13:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'sys.bpmn.seed.agent-active-inference',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-active-inference-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-homeostasis-watch-v1',
                 'did:web:bpmn.gftd.ai',
                 'agent_homeostasis_watch',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Agent homeostasis watch — ADR-2605061200.\n'
                 '\n'
                 '  Inputs:\n'
                 '    agentDid\n'
                 '    computeBudgetRemaining\n'
                 '    storagePressure\n'
                 '    leaseSecondsRemaining\n'
                 '    errorRate1h\n'
                 '    toolSuccessRate1h\n'
                 '    energyOrCostProxy\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_agent_homeostasis_watch"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/agent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="agent_homeostasis_watch" name="Agent homeostasis watch" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="manual / timer">\n'
                 '      <bpmn:outgoing>Flow_Start_Evaluate</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Evaluate" sourceRef="Start" '
                 'targetRef="Task_Evaluate"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Evaluate" name="Evaluate viability">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.evaluateViability"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=computeBudgetRemaining" '
                 'target="computeBudgetRemaining"/>\n'
                 '          <zeebe:input source="=storagePressure" target="storagePressure"/>\n'
                 '          <zeebe:input source="=leaseSecondsRemaining" '
                 'target="leaseSecondsRemaining"/>\n'
                 '          <zeebe:input source="=errorRate1h" target="errorRate1h"/>\n'
                 '          <zeebe:input source="=toolSuccessRate1h" target="toolSuccessRate1h"/>\n'
                 '          <zeebe:input source="=energyOrCostProxy" target="energyOrCostProxy"/>\n'
                 '          <zeebe:output source="=viabilityState" target="viabilityState"/>\n'
                 '          <zeebe:output source="=blockers" target="viabilityBlockers"/>\n'
                 '          <zeebe:output source="=nextActions" target="viabilityNextActions"/>\n'
                 '          <zeebe:output source="=normalized" target="homeostasisNormalized"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Evaluate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Evaluate_Write</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Evaluate_Write" sourceRef="Task_Evaluate" '
                 'targetRef="Task_Write"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Write" name="Record homeostasis snapshot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.recordHomeostasisSnapshot"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=agentDid" target="agentDid"/>\n'
                 '          <zeebe:input source="=homeostasisNormalized" '
                 'target="homeostasisNormalized"/>\n'
                 '          <zeebe:input source="=viabilityState" target="viabilityState"/>\n'
                 '          <zeebe:input source="=string(now())" target="createdAt"/>\n'
                 '          <zeebe:output source="=inserted" target="homeostasisInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Evaluate_Write</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Write_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Write_Audit" sourceRef="Task_Write" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="Emit homeostasis audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;agent.homeostasis.snapshot&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;agentDid&quot;: agentDid, '
                 '&quot;viabilityState&quot;: viabilityState, &quot;blockers&quot;: '
                 'viabilityBlockers, &quot;nextActions&quot;: viabilityNextActions, '
                 '&quot;inserted&quot;: homeostasisInserted }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Write_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3954,
                 '00-contracts/bpmn/ai/gftd/agent/homeostasisWatch.bpmn',
                 '2026-05-07T13:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'sys.bpmn.seed.agent-active-inference',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-homeostasis-watch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '         result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '         sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        120000, $5, 'active', $6,\n"
         "        1, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-homeostasis-watch-v1',
                 'did:web:bpmn.gftd.ai',
                 'ai.gftd.apps.agent.recordHomeostasis',
                 'agent_homeostasis_watch',
                 'vertex_agent_homeostasis_snapshot',
                 '2026-05-07T13:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'sys.bpmn.seed.agent-active-inference',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-homeostasis-watch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '         actor_id, actor_did, org_did)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-realworld-effect-dispatch-v1',
                 'did:web:bpmn.gftd.ai',
                 'agent_realworld_effect_dispatch',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Real-world effect dispatch gate — ADR-2605061300.\n'
                 '\n'
                 '  Phase 1 does not call channel-specific send/post/print/robotics adapters.\n'
                 '  It classifies and records the effect boundary so dispatch can only happen\n'
                 '  after payload hash, authority, approval, and receipt policy are visible.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_agent_realworld_effect_dispatch"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/agent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="agent_realworld_effect_dispatch" name="Agent real-world '
                 'effect dispatch gate" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="effect proposal received">\n'
                 '      <bpmn:outgoing>Flow_Start_Classify</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Classify" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="Classify real-world effect">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.classifyRealWorldEffect"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=channel" target="channel"/>\n'
                 '          <zeebe:input source="=payload" target="payload"/>\n'
                 '          <zeebe:input source="=actionProposalId" target="actionProposalId"/>\n'
                 '          <zeebe:input source="=agentDid" target="agentDid"/>\n'
                 '          <zeebe:input source="=principalDid" target="principalDid"/>\n'
                 '          <zeebe:input source="=effectClass" target="effectClass"/>\n'
                 '          <zeebe:input source="=targetRef" target="targetRef"/>\n'
                 '          <zeebe:input source="=summary" target="summary"/>\n'
                 '          <zeebe:input source="=approvalRef" target="approvalRef"/>\n'
                 '          <zeebe:input source="=budgetRef" target="budgetRef"/>\n'
                 '          <zeebe:output source="=realWorldEffect" target="realWorldEffect"/>\n'
                 '          <zeebe:output source="=requiresApproval" target="requiresApproval"/>\n'
                 '          <zeebe:output source="=blockers" target="effectBlockers"/>\n'
                 '          <zeebe:output source="=externalEffectPenalty" '
                 'target="externalEffectPenalty"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Classify</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Classify_Write</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Classify_Write" sourceRef="Task_Classify" '
                 'targetRef="Task_Write"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Write" name="Record real-world effect gate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_agent_realworld_effect&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={ vertex_id: realWorldEffect.vertex_id, '
                 'action_proposal_id: realWorldEffect.action_proposal_id, agent_did: '
                 'realWorldEffect.agent_did, principal_did: realWorldEffect.principal_did, '
                 'channel: realWorldEffect.channel, effect_class: realWorldEffect.effect_class, '
                 'target_ref_hash: realWorldEffect.target_ref_hash, payload_hash: '
                 'realWorldEffect.payload_hash, summary: realWorldEffect.summary, approval_ref: '
                 'realWorldEffect.approval_ref, budget_ref: realWorldEffect.budget_ref, '
                 'dispatch_state: realWorldEffect.dispatch_state, dispatch_receipt_ref: '
                 'realWorldEffect.dispatch_receipt_ref, observation_plan_json: '
                 'realWorldEffect.observation_plan_json, created_at: realWorldEffect.created_at, '
                 'updated_at: realWorldEffect.updated_at, sensitivity_ord: 1, actor_id: '
                 '&quot;sys.agent.realWorldEffect&quot;, owner_did: realWorldEffect.agent_did, '
                 'org_id: realWorldEffect.agent_did, user_id: realWorldEffect.agent_did }" '
                 'target="values"/>\n'
                 '          <zeebe:input source="=&quot;agent_realworld_effect_dispatch&quot;" '
                 'target="_bpmnProcessId"/>\n'
                 '          <zeebe:output source="=inserted" target="effectInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Classify_Write</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Write_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Write_Audit" sourceRef="Task_Write" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="Emit real-world effect audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;agent.realWorldEffect.classified&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;agentDid&quot;: agentDid, '
                 '&quot;channel&quot;: channel, &quot;requiresApproval&quot;: requiresApproval, '
                 '&quot;blockers&quot;: effectBlockers, &quot;externalEffectPenalty&quot;: '
                 'externalEffectPenalty, &quot;inserted&quot;: effectInserted }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Write_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="gate recorded">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5164,
                 '00-contracts/bpmn/ai/gftd/agent/realWorldEffectDispatch.bpmn',
                 '2026-05-07T13:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'sys.bpmn.seed.agent-active-inference',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-realworld-effect-dispatch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '         result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '         sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        120000, $5, 'active', $6,\n"
         "        1, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-realworld-effect-dispatch-v1',
                 'did:web:bpmn.gftd.ai',
                 'ai.gftd.apps.agent.classifyRealWorldEffect',
                 'agent_realworld_effect_dispatch',
                 'vertex_agent_realworld_effect',
                 '2026-05-07T13:00:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'sys.bpmn.seed.agent-active-inference',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-realworld-effect-dispatch-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-realworld-effect-dispatch-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-realworld-effect-dispatch-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-homeostasis-watch-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-homeostasis-watch-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/agent-active-inference-tick-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/agent-active-inference-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
