"""Captured from Kysely migration 20260428120100_seed_yadoya_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428120100_seed_yadoya_bpmn_actors"
down_revision = 'r_20260428120100_seed_telecom_nfv_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/yadoya-create-reservation-v1',
                 'did:web:yadoya.etzhayyim.com',
                 'yadoya_create_reservation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_yadoya_create_reservation" '
                 'targetNamespace="https://etzhayyim.com/bpmn/yadoya" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="yadoya_create_reservation" name="createReservation" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_LookupHotel"/>\n'
                 '    <bpmn:serviceTask id="Task_LookupHotel" name="lookup hotel">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, name, status FROM '
                 'vertex_yadoya_hotel WHERE vertex_id = $1 LIMIT 1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[hotelId]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="hotelRows"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_I</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_I" sourceRef="Task_LookupHotel" '
                 'targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="insert reservation">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_yadoya_reservation&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: vertexId, sensitivity_ord: 3, '
                 'owner_did: &quot;did:web:yadoya.etzhayyim.com&quot;, reservation_id: reservationId, '
                 'hotel_vid: hotelId, guest_did: guestDid, guest_summary_signal_v1: '
                 'guestSummarySignalV1, checkin: checkin, checkout: checkout, guests: guests, '
                 'nights: nights, amount_bucket: amountBucket, currency: currency, channel: '
                 'channel, status: &quot;pending&quot;, created_at: createdAt, org_id: orgId, '
                 'user_id: userId, actor_id: &quot;did:web:yadoya.etzhayyim.com&quot;}" target="row"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/>\n'
                 '          <zeebe:output source="=reservationId" target="reservationId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_I</bpmn:incoming><bpmn:outgoing>Flow_E</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_E" sourceRef="Task_Insert" '
                 'targetRef="Task_Edge"/>\n'
                 '    <bpmn:serviceTask id="Task_Edge" name="link reservation to hotel">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_yadoya_reservation_for_hotel&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={edge_id: &quot;edge:&quot; + reservationId + '
                 '&quot;:hotel&quot;, sensitivity_ord: 1, owner_did: '
                 '&quot;did:web:yadoya.etzhayyim.com&quot;, src_vid: vertexId, dst_vid: hotelId, role: '
                 '&quot;for-hotel&quot;, created_at: createdAt, org_id: orgId, user_id: userId, '
                 'actor_id: &quot;did:web:yadoya.etzhayyim.com&quot;}" target="row"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_E</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Edge" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:yadoya.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;yadoya.reservation.create&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={reservationId: reservationId, hotelId: hotelId, '
                 'status: &quot;pending&quot;}" target="payload"/>\n'
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
                 4114,
                 '00-contracts/bpmn/com/etzhayyim/yadoya/createReservation.bpmn',
                 '2026-04-28T12:01:00Z',
                 'did:web:yadoya.etzhayyim.com',
                 'did:web:yadoya.etzhayyim.com',
                 'sys.bpmn.seed.yadoya',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/yadoya-create-reservation-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/yadoya-createReservation-v1',
                 'did:web:yadoya.etzhayyim.com',
                 'com.etzhayyim.apps.yadoya.createReservation',
                 'yadoya_create_reservation',
                 30000,
                 '2026-04-28T12:01:00Z',
                 'did:web:yadoya.etzhayyim.com',
                 'did:web:yadoya.etzhayyim.com',
                 'sys.bpmn.seed.yadoya',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/yadoya-createReservation-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/yadoya-createReservation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/yadoya-create-reservation-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
