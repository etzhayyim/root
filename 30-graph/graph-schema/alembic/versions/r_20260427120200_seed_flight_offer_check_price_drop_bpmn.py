"""Captured from Kysely migration 20260427120200_seed_flight_offer_check_price_drop_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427120200_seed_flight_offer_check_price_drop_bpmn"
down_revision = 'r_20260427120100_vertex_flight_offer_alert'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'flight_offer_check_price_drop',\n"
         "           1, $3, CAST($4 AS integer), $5, 'active',\n"
         '           $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-check-price-drop-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_check_price_drop"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_check_price_drop" name="checkPriceDrop" '
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
                 '<bpmn:incoming>Flow_Health</bpmn:incoming><bpmn:outgoing>Flow_Check</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Check" sourceRef="Task_Health" '
                 'targetRef="Task_Check"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Check" name="check drop vs last alert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.checkDrop"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=originIata" target="originIata"/>\n'
                 '          <zeebe:input source="=destinationIata" target="destinationIata"/>\n'
                 '          <zeebe:input source="=outboundDate" target="outboundDate"/>\n'
                 '          <zeebe:input source="=if currency != null and currency != &quot;&quot; '
                 'then currency else &quot;USD&quot;" target="currency"/>\n'
                 '          <zeebe:input source="=if thresholdPct != null then thresholdPct else '
                 '10.0" target="thresholdPct"/>\n'
                 '          <zeebe:output source="=alerted" target="alerted"/>\n'
                 '          <zeebe:output source="=newPrice" target="newPrice"/>\n'
                 '          <zeebe:output source="=previousPrice" target="previousPrice"/>\n'
                 '          <zeebe:output source="=dropPct" target="dropPct"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/>\n'
                 '          <zeebe:output source="=provider" target="provider"/>\n'
                 '          <zeebe:output source="=bookingUrl" target="bookingUrl"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Check</bpmn:incoming><bpmn:outgoing>Flow_Gateway</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gateway" sourceRef="Task_Check" '
                 'targetRef="Gateway_Alert"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gateway_Alert" name="alerted?">\n'
                 '      <bpmn:incoming>Flow_Gateway</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Post</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_NoPost</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Post" sourceRef="Gateway_Alert" '
                 'targetRef="Task_PostDrop">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=alerted = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_NoPost" sourceRef="Gateway_Alert" '
                 'targetRef="Gateway_Join">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=alerted != '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_PostDrop" name="app.bsky.feed.post drop alert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;app.bsky.feed.post&quot;" '
                 'target="collection"/>\n'
                 '          <zeebe:input source="=if notifyDid != null and notifyDid != '
                 '&quot;&quot; then notifyDid else &quot;did:web:flight-offer.etzhayyim.com&quot;" '
                 'target="repo"/>\n'
                 '          <zeebe:input source="={\n'
                 '              text: &quot;✈️ &quot; + originIata + &quot; → &quot; + '
                 'destinationIata + &quot; on &quot; + substring(outboundDate, 1, 10) + &quot;: '
                 '&quot; + string(round half up(newPrice, 0)) + &quot; &quot; + currency + &quot; '
                 '(down &quot; + string(round half up(dropPct, 1)) + &quot;% from &quot; + '
                 'string(round half up(previousPrice, 0)) + &quot;) &quot; + bookingUrl,\n'
                 '              createdAt: string(now()),\n'
                 '              langs: [&quot;en&quot;]\n'
                 '          }" target="record"/>\n'
                 '          <zeebe:input source="=&quot;dropPostResult&quot;" '
                 'target="resultKey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Post</bpmn:incoming><bpmn:outgoing>Flow_PostJoin</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_PostJoin" sourceRef="Task_PostDrop" '
                 'targetRef="Gateway_Join"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gateway_Join">\n'
                 '      <bpmn:incoming>Flow_NoPost</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_PostJoin</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Gateway_Join" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit drop check">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:flight-offer.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;flight.offer.checkPriceDrop&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={originIata: originIata, destinationIata: '
                 'destinationIata, outboundDate: outboundDate, currency: currency, alerted: '
                 'alerted, newPrice: newPrice, previousPrice: previousPrice, dropPct: dropPct, '
                 'vertexId: vertexId}" target="payload"/>\n'
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
                 5712,
                 '00-contracts/bpmn/ai/gftd/flight-offer/checkPriceDrop.bpmn',
                 '2026-04-27T12:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-check-price-drop-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'ai.gftd.apps.flightOffer.checkPriceDrop',\n"
         "           'flight_offer_check_price_drop', 1, CAST(15000 AS integer), 'active',\n"
         '           $3, 1, $4, $5, $6\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $7)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-check-price-drop-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 '2026-04-27T12:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-check-price-drop-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-check-price-drop-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-check-price-drop-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
