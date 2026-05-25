"""Captured from Kysely migration 20260427150200_seed_flight_offer_phase6_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427150200_seed_flight_offer_phase6_bpmn"
down_revision = 'r_20260427150100_seed_telecom_supplier_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-fetch-from-source-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'flight_offer_fetch_from_source',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_fetch_from_source"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_fetch_from_source" name="fetchFromSource" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Health</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health" sourceRef="Start" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="rw.health.probe"/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Health</bpmn:incoming><bpmn:outgoing>Flow_Fetch</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fetch" sourceRef="Task_Health" '
                 'targetRef="Task_Fetch"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch from registered source">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.fetchFromSource"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=sourceId" target="sourceId"/>\n'
                 '          <zeebe:input source="=originIata" target="originIata"/>\n'
                 '          <zeebe:input source="=destinationIata" target="destinationIata"/>\n'
                 '          <zeebe:input source="=outboundDate" target="outboundDate"/>\n'
                 '          <zeebe:input source="=if returnDate != null then returnDate else '
                 '&quot;&quot;" target="returnDate"/>\n'
                 '          <zeebe:input source="=if currency != null and currency != &quot;&quot; '
                 'then currency else &quot;USD&quot;" target="currency"/>\n'
                 '          <zeebe:input source="=if maxOffers != null then maxOffers else 20" '
                 'target="maxOffers"/>\n'
                 '          <zeebe:output source="=resolvedSource" target="resolvedSource"/>\n'
                 '          <zeebe:output source="=offersFetched" target="offersFetched"/>\n'
                 '          <zeebe:output source="=offersWritten" target="offersWritten"/>\n'
                 '          <zeebe:output source="=providerObservedAt" '
                 'target="providerObservedAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Fetch" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit fetch from source">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:flight-offer.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;flight.offer.fetchFromSource&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={sourceId: sourceId, resolvedSource: '
                 'resolvedSource, originIata: originIata, destinationIata: destinationIata, '
                 'outboundDate: outboundDate, offersFetched: offersFetched, offersWritten: '
                 'offersWritten}" target="payload"/>\n'
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
                 3408,
                 '00-contracts/bpmn/ai/gftd/flight-offer/fetchFromSource.bpmn',
                 '2026-04-27T15:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-fetch-from-source-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-fetch-from-source-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'app.etzhayyim.apps.flightOffer.fetchFromSource',
                 'flight_offer_fetch_from_source',
                 30000,
                 '2026-04-27T15:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-fetch-from-source-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-list-sources-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'flight_offer_list_sources',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_list_sources"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_list_sources" name="listSources" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_List</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_List" sourceRef="Start" targetRef="Task_List"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_List" name="select sources">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.listSources"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if status != null then status else &quot;&quot;" '
                 'target="status"/>\n'
                 '          <zeebe:input source="=if limit != null then limit else 100" '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=items" target="items"/>\n'
                 '          <zeebe:output source="=count" target="count"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_List</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_List" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1497,
                 '00-contracts/bpmn/ai/gftd/flight-offer/listSources.bpmn',
                 '2026-04-27T15:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-list-sources-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-list-sources-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'app.etzhayyim.apps.flightOffer.listSources',
                 'flight_offer_list_sources',
                 10000,
                 '2026-04-27T15:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-list-sources-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-list-airlines-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'flight_offer_list_airlines',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_list_airlines"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_list_airlines" name="listAirlines" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_List</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_List" sourceRef="Start" targetRef="Task_List"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_List" name="select airlines">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.listAirlines"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if countryCode != null then countryCode else '
                 '&quot;&quot;" target="countryCode"/>\n'
                 '          <zeebe:input source="=if alliance != null then alliance else '
                 '&quot;&quot;" target="alliance"/>\n'
                 '          <zeebe:input source="=if limit != null then limit else 200" '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=items" target="items"/>\n'
                 '          <zeebe:output source="=count" target="count"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_List</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_List" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1622,
                 '00-contracts/bpmn/ai/gftd/flight-offer/listAirlines.bpmn',
                 '2026-04-27T15:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-list-airlines-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-list-airlines-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 'app.etzhayyim.apps.flightOffer.listAirlines',
                 'flight_offer_list_airlines',
                 10000,
                 '2026-04-27T15:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-list-airlines-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-fetch-from-source-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-fetch-from-source-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-list-sources-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-list-sources-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-list-airlines-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-list-airlines-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
