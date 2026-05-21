"""Captured from Kysely migration 20260428140100_seed_yadoya_bpmn_lifecycle."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428140100_seed_yadoya_bpmn_lifecycle"
down_revision = 'r_20260428140100_seed_telecom_wlan_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yadoya-cancel-reservation-v1',
                 'did:web:yadoya.etzhayyim.com',
                 'yadoya_cancel_reservation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yadoya_cancel_reservation" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yadoya" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yadoya_cancel_reservation" name="cancelReservation" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Lookup"/>\n'
                 '    <bpmn:serviceTask id="Task_Lookup" name="lookup reservation">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <bpmn:documentation>Returns the row to be cancelled. Caller-side '
                 'checks (owner, checkin\n'
                 '          not passed, status != cancelled) are enforced by the yadoya Worker\n'
                 '          before publishing the message; the BPMN actor only commits the\n'
                 '          state transition.</bpmn:documentation>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, status, guest_did, '
                 'checkin FROM vertex_yadoya_reservation WHERE reservation_id = $1 LIMIT 1&quot;" '
                 'target="sql"/>\n'
                 '          <zeebe:input source="=[reservationId]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="reservationRows"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_D</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_D" sourceRef="Task_Lookup" '
                 'targetRef="Task_Delete"/>\n'
                 '    <bpmn:serviceTask id="Task_Delete" name="delete current row">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.delete"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <bpmn:documentation>RisingWave does not support OLTP UPDATE TX for '
                 'this table; emulate\n'
                 '          the status transition with delete-then-insert keyed on '
                 'vertex_id.</bpmn:documentation>\n'
                 '          <zeebe:input source="=&quot;vertex_yadoya_reservation&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: reservationRows[1].vertex_id}" '
                 'target="where"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_D</bpmn:incoming><bpmn:outgoing>Flow_I</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_I" sourceRef="Task_Delete" '
                 'targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="insert cancelled row">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_yadoya_reservation&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: reservationRows[1].vertex_id, '
                 'sensitivity_ord: 3, owner_did: &quot;did:web:yadoya.etzhayyim.com&quot;, '
                 'reservation_id: reservationId, hotel_vid: hotelId, guest_did: guestDid, checkin: '
                 'checkin, checkout: checkout, guests: guests, nights: nights, channel: channel, '
                 'status: &quot;cancelled&quot;, cancelled_at: cancelledAt, cancel_reason: '
                 'cancelReason, currency: currency, created_at: createdAt, org_id: orgId, user_id: '
                 'userId, actor_id: &quot;did:web:yadoya.etzhayyim.com&quot;}" target="row"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_I</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Insert" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:yadoya.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;yadoya.reservation.cancel&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={reservationId: reservationId, hotelId: hotelId, '
                 'status: &quot;cancelled&quot;, reason: cancelReason}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4260,
                 '00-contracts/bpmn/ai/gftd/yadoya/cancelReservation.bpmn',
                 '2026-04-28T14:01:00Z',
                 'did:web:yadoya.etzhayyim.com',
                 'did:web:yadoya.etzhayyim.com',
                 'sys.bpmn.seed.yadoya-lifecycle',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yadoya-cancel-reservation-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yadoya-get-reservation-v1',
                 'did:web:yadoya.etzhayyim.com',
                 'yadoya_get_reservation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yadoya_get_reservation" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yadoya" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yadoya_get_reservation" name="getReservation" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Lookup"/>\n'
                 '    <bpmn:serviceTask id="Task_Lookup" name="lookup reservation (Tier 1/2 '
                 'only)">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <bpmn:documentation>Tier-3 columns (guest_summary_signal_v1, '
                 'amount_bucket) are\n'
                 '          intentionally NOT projected here. The yadoya Worker is the\n'
                 '          authoritative redaction layer for getReservation (XRPC) — this\n'
                 '          BPMN path mirrors the same column set so an alternate caller\n'
                 '          (e.g. another BPMN flow) cannot bypass the redaction by going\n'
                 '          through Zeebe.</bpmn:documentation>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, reservation_id, '
                 'hotel_vid, guest_did, checkin, checkout, guests, nights, currency, channel, '
                 'status, cancelled_at, cancel_reason FROM vertex_yadoya_reservation WHERE '
                 'reservation_id = $1 LIMIT 1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[reservationId]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="reservationRows"/>\n'
                 '          <zeebe:output source="=rows[1]" target="reservation"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Lookup" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit read">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:yadoya.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;yadoya.reservation.read&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={reservationId: reservationId, found: '
                 'reservationRows[1] != null}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2697,
                 '00-contracts/bpmn/ai/gftd/yadoya/getReservation.bpmn',
                 '2026-04-28T14:01:00Z',
                 'did:web:yadoya.etzhayyim.com',
                 'did:web:yadoya.etzhayyim.com',
                 'sys.bpmn.seed.yadoya-lifecycle',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yadoya-get-reservation-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yadoya-cancelReservation-v1',
                 'did:web:yadoya.etzhayyim.com',
                 'ai.gftd.apps.yadoya.cancelReservation',
                 'yadoya_cancel_reservation',
                 30000,
                 '2026-04-28T14:01:00Z',
                 'did:web:yadoya.etzhayyim.com',
                 'did:web:yadoya.etzhayyim.com',
                 'sys.bpmn.seed.yadoya-lifecycle',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yadoya-cancelReservation-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yadoya-getReservation-v1',
                 'did:web:yadoya.etzhayyim.com',
                 'ai.gftd.apps.yadoya.getReservation',
                 'yadoya_get_reservation',
                 15000,
                 '2026-04-28T14:01:00Z',
                 'did:web:yadoya.etzhayyim.com',
                 'did:web:yadoya.etzhayyim.com',
                 'sys.bpmn.seed.yadoya-lifecycle',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yadoya-getReservation-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yadoya-cancelReservation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yadoya-getReservation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yadoya-cancel-reservation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yadoya-get-reservation-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
