"""Captured from Kysely migration 20260506200000_seed_malak_referral_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506200000_seed_malak_referral_bpmn"
down_revision = 'r_20260506190000_seed_malak_active_inference_loop_bpmn'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-draft-agency-referral-v1',
                 'did:web:malak.gftd.ai',
                 'malak_draft_agency_referral',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.draftAgencyReferral — draft-only agency referral package.\n'
                 '\n'
                 '  This process records a reviewable referral draft. It does not send email,\n'
                 '  submit an INTERPOL notice, or call any external agency API.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.malak.draftAgencyReferral\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_draft_agency_referral"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_draft_agency_referral" name="malak '
                 'draftAgencyReferral" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.draftAgencyReferral", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToDerive</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToDerive" sourceRef="Start" '
                 'targetRef="Task_Derive"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Derive" name="validate referral draft">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="malak.validateAgencyReferralDraft"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=actorId" target="actorId"/>\n'
                 '          <zeebe:input source="=caseId" target="caseId"/>\n'
                 '          <zeebe:input source="=agency" target="agency"/>\n'
                 '          <zeebe:input source="=legalBasis" target="legalBasis"/>\n'
                 '          <zeebe:input source="=approvalRef" target="approvalRef"/>\n'
                 '          <zeebe:input source="=summary" target="summary"/>\n'
                 '          <zeebe:input source="=evidenceIds" target="evidenceIds"/>\n'
                 '          <zeebe:input source="=attributionConfidence" '
                 'target="attributionConfidence"/>\n'
                 '          <zeebe:input source="=referralKind" target="referralKind"/>\n'
                 '          <zeebe:input source="=tlp" target="tlp"/>\n'
                 '          <zeebe:output source="=derived" target="derived"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToDerive</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToHash</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToHash" sourceRef="Task_Derive" '
                 'targetRef="Task_Hash"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Hash" name="hash referral payload">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.hash.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={ referralId: derived.referralId, caseId: '
                 'string(caseId), actorId: string(actorId), agency: string(agency), referralKind: '
                 'derived.normalizedKind, tlp: derived.normalizedTlp, attributionConfidence: '
                 'derived.confidence, legalBasis: string(legalBasis), approvalRef: '
                 'string(approvalRef), evidenceIds: derived.evidenceIds, summary: string(summary) '
                 '}" target="value"/>\n'
                 '          <zeebe:output source="=hash" target="payloadHash"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToHash</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToInsert</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToInsert" sourceRef="Task_Hash" '
                 'targetRef="Task_Insert"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="insert referral draft">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_malak_agency_referral_draft&quot;" '
                 'target="table"/>\n'
                 "          <zeebe:input source='={\n"
                 '            vertex_id: string '
                 'join(["at://did:web:malak.gftd.ai/ai.gftd.apps.malak.agencyReferralDraft/", '
                 'derived.referralId], ""),\n'
                 '            rkey: derived.referralId,\n'
                 '            repo: "did:web:malak.gftd.ai",\n'
                 '            referral_id: derived.referralId,\n'
                 '            case_id: string(caseId),\n'
                 '            actor_id: string(actorId),\n'
                 '            agency: string(agency),\n'
                 '            referral_kind: derived.normalizedKind,\n'
                 '            tlp: derived.normalizedTlp,\n'
                 '            attribution_confidence: derived.confidence,\n'
                 '            legal_basis: string(legalBasis),\n'
                 '            approval_ref: string(approvalRef),\n'
                 '            evidence_ids_json: string(derived.evidenceIds),\n'
                 '            summary: string(summary),\n'
                 '            payload_hash: string(payloadHash),\n'
                 '            draft_state: "draft",\n'
                 '            created_at: string(now()),\n'
                 '            updated_at: string(now()),\n'
                 '            created_date: substring(string(now()), 1, 10),\n'
                 '            sensitivity_ord: if derived.normalizedTlp = "red" then 120 else '
                 '100,\n'
                 '            owner_did: "did:web:malak.gftd.ai",\n'
                 '            org_id: "did:web:malak.gftd.ai",\n'
                 '            user_id: if callerDid = null then "did:web:malak.gftd.ai" else '
                 'string(callerDid)\n'
                 '          }\' target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=inserted" target="draftInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToInsert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Insert" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit referral draft">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;malak.agencyReferral.drafted&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ referralId: derived.referralId, caseId: '
                 'string(caseId), actorId: string(actorId), agency: string(agency), payloadHash: '
                 'payloadHash, inserted: draftInserted }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="draft recorded">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5992,
                 '00-contracts/bpmn/ai/gftd/malak/draftAgencyReferral.bpmn',
                 '2026-05-06T20:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-referral',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-draft-agency-referral-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-draftAgencyReferral-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.draftAgencyReferral',
                 'malak_draft_agency_referral',
                 'vertex_malak_agency_referral_draft',
                 '2026-05-06T20:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-referral',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-draftAgencyReferral-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-draftAgencyReferral-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-draft-agency-referral-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
