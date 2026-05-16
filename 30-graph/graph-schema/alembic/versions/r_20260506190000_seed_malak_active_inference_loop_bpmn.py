"""Captured from Kysely migration 20260506190000_seed_malak_active_inference_loop_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506190000_seed_malak_active_inference_loop_bpmn"
down_revision = 'r_20260506180000_vertex_malak_active_inference_loop'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '       actor_id, actor_did, org_did)\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 100, $8, $9, $10,\n'
         '      $11, $12\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $13\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-run-investigation-tick-v1',
                 'did:web:malak.gftd.ai',
                 'malak_run_investigation_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.runInvestigationTick — one bounded Active Inference tick.\n'
                 '\n'
                 '  Scores candidate investigation actions with agent.evaluateExpectedFreeEnergy,\n'
                 '  writes vertex_malak_investigation_tick, and emits an audit event.\n'
                 '  This BPMN does not send agency reports or perform external effects.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.malak.runInvestigationTick\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_run_investigation_tick"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_run_investigation_tick" name="malak '
                 'runInvestigationTick" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.runInvestigationTick", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToEvaluate</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEvaluate" sourceRef="Start" '
                 'targetRef="Task_Evaluate"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Evaluate" name="evaluate expected free energy">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="agent.evaluateExpectedFreeEnergy"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=candidateActions" target="candidateActions"/>\n'
                 '          <zeebe:input source="=legalBasis != null and string(legalBasis) != '
                 '&quot;&quot;" target="mokutekiGatePass"/>\n'
                 '          <zeebe:input source="=true" target="requireSafetyFloor"/>\n'
                 '          <zeebe:output source="=selectedActionId" target="selectedActionId"/>\n'
                 '          <zeebe:output source="=expectedFreeEnergy" '
                 'target="expectedFreeEnergy"/>\n'
                 '          <zeebe:output source="=rejected" target="rejectedActions"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToEvaluate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToWrite</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToWrite" sourceRef="Task_Evaluate" '
                 'targetRef="Task_Write"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Write" name="write investigation tick">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_malak_investigation_tick&quot;" '
                 'target="table"/>\n'
                 "          <zeebe:input source='={\n"
                 '            vertex_id: string '
                 'join(["at://did:web:malak.gftd.ai/ai.gftd.apps.malak.investigationTick/", '
                 'string(actorId), "-", string(now())], ""),\n'
                 '            rkey: string join(["tick-", string(actorId), "-", string(now())], '
                 '""),\n'
                 '            repo: "did:web:malak.gftd.ai",\n'
                 '            actor_id: string(actorId),\n'
                 '            case_id: if caseId = null then "" else string(caseId),\n'
                 '            tick_kind: if tickKind = null then "deliberative" else '
                 'string(tickKind),\n'
                 '            observation_refs_json: string(if observationRefs = null then [] else '
                 'observationRefs),\n'
                 '            candidate_actions_json: string(candidateActions),\n'
                 '            expected_free_energy_json: string(expectedFreeEnergy),\n'
                 '            selected_action_id: if selectedActionId = null then "" else '
                 'string(selectedActionId),\n'
                 '            rejected_actions_json: string(rejectedActions),\n'
                 '            attribution_confidence: if attributionConfidence = null then 0 else '
                 'attributionConfidence,\n'
                 '            legal_basis: if legalBasis = null then "" else string(legalBasis),\n'
                 '            approval_ref: if approvalRef = null then "" else '
                 'string(approvalRef),\n'
                 '            gate_pass: legalBasis != null and string(legalBasis) != "",\n'
                 '            created_at: string(now()),\n'
                 '            created_date: substring(string(now()), 1, 10),\n'
                 '            sensitivity_ord: 100,\n'
                 '            owner_did: "did:web:malak.gftd.ai",\n'
                 '            org_id: "did:web:malak.gftd.ai",\n'
                 '            user_id: if callerDid = null then "did:web:malak.gftd.ai" else '
                 'string(callerDid)\n'
                 '          }\' target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=inserted" target="tickInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToWrite</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Write" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit investigation tick">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;malak.investigation.tick&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ actorId: actorId, caseId: caseId, '
                 'selectedActionId: selectedActionId, expectedFreeEnergy: expectedFreeEnergy, '
                 'rejected: rejectedActions, inserted: tickInserted }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n'
                 '\n',
                 5277,
                 '00-contracts/bpmn/ai/gftd/malak/runInvestigationTick.bpmn',
                 '2026-05-06T19:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-active-inference',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-run-investigation-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '       result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '       sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      30000, $5, 'active', $6,\n"
         '      100, $7, $8, $9, $10, $11\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-runInvestigationTick-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.runInvestigationTick',
                 'malak_run_investigation_tick',
                 'vertex_malak_investigation_tick',
                 '2026-05-06T19:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-active-inference',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-runInvestigationTick-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-runInvestigationTick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-run-investigation-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
