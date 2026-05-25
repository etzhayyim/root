"""Captured from Kysely migration 20260428000000_seed_arms_expired_permit_scanner."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428000000_seed_arms_expired_permit_scanner"
down_revision = 'r_20260427230800_seed_lawfirm_search_precedent_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         "      'sys.bpmn.seed.arms'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/arms-expired-permit-scanner-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_expired_permit_scanner',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  arms.expiredPermitScanner — R/P1D batch job.\n'
                 '\n'
                 '  Scans vertex_arms_permit for permits where expires_at < NOW() AND status = '
                 "'active',\n"
                 "  then overwrites those rows with status = 'expired' via RisingWave PK-upsert\n"
                 '  (same vertex_id re-insert = implicit overwrite per ADR-0036 / record-log '
                 'semantics).\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.arms.scanExpiredPermits  (manual trigger + timer)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/arms-expired-permit-scanner-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_arms_expired_permit_scanner"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/arms"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="arms_expired_permit_scanner" name="arms expired permit '
                 'scanner" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.arms.scanExpiredPermits", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/P1D: fires once per day. Also triggerable via XRPC for manual scans. '
                 '-->\n'
                 '    <bpmn:startEvent id="Start" name="daily">\n'
                 '      <bpmn:outgoing>Flow_ToCount</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1d">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCount" sourceRef="Start" '
                 'targetRef="Task_CountExpired"/>\n'
                 '\n'
                 '    <!-- Step 1: count permits that have passed their expiry but are still '
                 'active -->\n'
                 '    <bpmn:serviceTask id="Task_CountExpired" name="count active-but-expired '
                 'permits">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input\n'
                 '            source="=&quot;SELECT COUNT(*) AS expired_count FROM '
                 'vertex_arms_permit WHERE expires_at &lt; NOW() AND status = \'active\'&quot;"\n'
                 '            target="sql"/>\n'
                 '          <zeebe:output source="=rows[1].expired_count" target="expiredCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCount</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToExpire</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToExpire" sourceRef="Task_CountExpired" '
                 'targetRef="Task_ExpireBatch"/>\n'
                 '\n'
                 '    <!--\n'
                 '      Step 2: RisingWave PK-upsert pattern — INSERT INTO ... SELECT ... '
                 'overwriting status.\n'
                 '      Same vertex_id re-insert = implicit overwrite (no ON CONFLICT needed, RW '
                 'spec).\n'
                 '      Selects ALL columns to avoid partial-row null issues.\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_ExpireBatch" name="expire permits (PK upsert)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input\n'
                 '            source="=&quot;INSERT INTO vertex_arms_permit (vertex_id, _seq, '
                 'created_date, sensitivity_ord, owner_did, holder_did, firearm_vid, permit_type, '
                 'permit_hash, issued_at, expires_at, jurisdiction, status, created_at, org_id, '
                 'user_id, actor_id) SELECT vertex_id, _seq, created_date, sensitivity_ord, '
                 'owner_did, holder_did, firearm_vid, permit_type, permit_hash, issued_at, '
                 "expires_at, jurisdiction, 'expired', created_at, org_id, user_id, actor_id FROM "
                 'vertex_arms_permit WHERE expires_at &lt; NOW() AND status = \'active\'&quot;"\n'
                 '            target="sql"/>\n'
                 '          <zeebe:output source="=rowCount" target="expiredRows"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToExpire</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_ExpireBatch" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <!-- Step 3: OCEL audit event -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit audit event">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;app.etzhayyim.apps.arms.scanExpiredPermits&quot;" target="activity"/>\n'
                 '          <zeebe:input source="=&quot;arms.etzhayyim.com&quot;" target="actorDid"/>\n'
                 '          <zeebe:input source="=expiredRows" target="expiredRows"/>\n'
                 '          <zeebe:input source="=expiredCount" target="expiredCountBefore"/>\n'
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
                 '</bpmn:definitions>\n',
                 4755,
                 '00-contracts/bpmn/ai/gftd/arms/expiredPermitScanner.bpmn',
                 '2026-04-28T00:00:00Z',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/arms-expired-permit-scanner-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST(60000 AS integer),\n'
         "      'active',\n"
         '      $5,\n'
         '      1,\n'
         '      $6,\n'
         '      $7,\n'
         "      'sys.bpmn.seed.arms'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/arms-scanExpiredPermits-v1',
                 'did:web:arms.etzhayyim.com',
                 'app.etzhayyim.apps.arms.scanExpiredPermits',
                 'arms_expired_permit_scanner',
                 '2026-04-28T00:00:00Z',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/arms-scanExpiredPermits-v1']}]

DOWN = [{'sql': '\n    DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/arms-scanExpiredPermits-v1']},
 {'sql': '\n    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/arms-expired-permit-scanner-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
