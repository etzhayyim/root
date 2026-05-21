"""Captured from Kysely migration 20260427130100_seed_flight_offer_phase3_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427130100_seed_flight_offer_phase3_bpmn"
down_revision = 'r_20260427130000_vertex_flight_offer_watch'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         "             1, $4, CAST($5 AS integer), $6, 'active',\n"
         '             $7, 1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-add-watch-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'flight_offer_add_watch',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_add_watch"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_add_watch" name="addWatch" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Add</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Add" sourceRef="Start" targetRef="Task_Add"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Add" name="upsert watch row">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.addWatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=originIata" target="originIata"/>\n'
                 '          <zeebe:input source="=destinationIata" target="destinationIata"/>\n'
                 '          <zeebe:input source="=outboundDate" target="outboundDate"/>\n'
                 '          <zeebe:input source="=if returnDate != null then returnDate else '
                 '&quot;&quot;" target="returnDate"/>\n'
                 '          <zeebe:input source="=if currency != null and currency != &quot;&quot; '
                 'then currency else &quot;USD&quot;" target="currency"/>\n'
                 '          <zeebe:input source="=if thresholdPct != null then thresholdPct else '
                 '10.0" target="thresholdPct"/>\n'
                 '          <zeebe:input source="=if cadenceMinutes != null then cadenceMinutes '
                 'else 360" target="cadenceMinutes"/>\n'
                 '          <zeebe:input source="=if providerHint != null then providerHint else '
                 '&quot;&quot;" target="providerHint"/>\n'
                 '          <zeebe:input source="=if maxOffers != null then maxOffers else 20" '
                 'target="maxOffers"/>\n'
                 '          <zeebe:input source="=if notifyDid != null then notifyDid else '
                 '&quot;&quot;" target="notifyDid"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/>\n'
                 '          <zeebe:output source="=created" target="created"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Add</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Add" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit add watch">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:flight-offer.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;flight.offer.addWatch&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, created: created, '
                 'originIata: originIata, destinationIata: destinationIata, outboundDate: '
                 'outboundDate}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3101,
                 '00-contracts/bpmn/ai/gftd/flight-offer/addWatch.bpmn',
                 '2026-04-27T13:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-add-watch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         "             $4, 1, CAST($5 AS integer), 'active',\n"
         '             $6, 1, $7, $8, $9\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$10)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-add-watch-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'ai.gftd.apps.flightOffer.addWatch',
                 'flight_offer_add_watch',
                 15000,
                 '2026-04-27T13:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-add-watch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         "             1, $4, CAST($5 AS integer), $6, 'active',\n"
         '             $7, 1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-poll-watchlist-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'flight_offer_poll_watchlist',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — refreshes vertex_flight_offer_watch entries every 6 hours.\n'
                 '\n'
                 '  flight.offer.pollWatchlist primitive:\n'
                 '    - SELECTs active watch rows where next_due_at <= now\n'
                 '    - per row: _do_search() then _do_check_drop()\n'
                 '    - bumps last_polled_at + next_due_at = now + cadence_minutes\n'
                 '    - returns { watchesRead, offersWritten, alertsFired, errors, dropAlerts[] }\n'
                 '\n'
                 '  AT post fan-out for individual drop alerts is handled by the\n'
                 '  flight_offer_check_price_drop BPMN when invoked directly via XRPC.\n'
                 '  Within this poll, the alert row is written to vertex_flight_offer_alert\n'
                 '  (downstream consumers can subscribe).\n'
                 '\n'
                 '  NSID: ai.gftd.apps.flightOffer.pollWatchlist\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-poll-watchlist-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_poll_watchlist"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_poll_watchlist" name="pollWatchlist" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.flightOffer.pollWatchlist", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 6 hours">\n'
                 '      <bpmn:outgoing>Flow_Health_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT6H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT6H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_Health_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_Timer" sourceRef="Start_Timer" '
                 'targetRef="Task_Health"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="rw.health.probe"/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Health_Timer</bpmn:incoming><bpmn:incoming>Flow_Health_Manual</bpmn:incoming><bpmn:outgoing>Flow_Poll</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Poll" sourceRef="Task_Health" '
                 'targetRef="Task_Poll"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Poll" name="poll watchlist">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.pollWatchlist"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if limit != null then limit else 50" '
                 'target="limit"/>\n'
                 '          <zeebe:input source="=if force != null then force else false" '
                 'target="force"/>\n'
                 '          <zeebe:output source="=watchesRead" target="watchesRead"/>\n'
                 '          <zeebe:output source="=offersWritten" target="offersWritten"/>\n'
                 '          <zeebe:output source="=alertsFired" target="alertsFired"/>\n'
                 '          <zeebe:output source="=errors" target="errors"/>\n'
                 '          <zeebe:output source="=dropAlerts" target="dropAlerts"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Poll</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Poll" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit poll">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:flight-offer.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;flight.offer.pollWatchlist&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={watchesRead: watchesRead, offersWritten: '
                 'offersWritten, alertsFired: alertsFired, errors: errors}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4304,
                 '00-contracts/bpmn/ai/gftd/flight-offer/pollWatchlist.bpmn',
                 '2026-04-27T13:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-poll-watchlist-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         "             $4, 1, CAST($5 AS integer), 'active',\n"
         '             $6, 1, $7, $8, $9\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$10)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-poll-watchlist-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'ai.gftd.apps.flightOffer.pollWatchlist',
                 'flight_offer_poll_watchlist',
                 300000,
                 '2026-04-27T13:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-poll-watchlist-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-add-watch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-add-watch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-poll-watchlist-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-poll-watchlist-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
