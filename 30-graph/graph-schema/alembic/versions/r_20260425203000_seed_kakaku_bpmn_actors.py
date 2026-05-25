"""Captured from Kysely migration 20260425203000_seed_kakaku_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425203000_seed_kakaku_bpmn_actors"
down_revision = 'r_20260425200000_mangaka_typed_per_kind'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-upsertOffer-v1',
                 'did:web:kakaku.etzhayyim.com',
                 'kakaku_upsert_offer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_kakaku_upsert_offer"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kakaku"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="kakaku_upsert_offer" name="kakaku upsert offer" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="offer submitted">\n'
                 '      <bpmn:outgoing>Flow_Upsert</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Upsert" sourceRef="Start" '
                 'targetRef="Task_Upsert"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Upsert" name="upsert offer">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kakaku.upsertOffer"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=status" target="status"/>\n'
                 '          <zeebe:output source="=productId" target="productId"/>\n'
                 '          <zeebe:output source="=productDid" target="productDid"/>\n'
                 '          <zeebe:output source="=globalProductId" target="globalProductId"/>\n'
                 '          <zeebe:output source="=globalProductDid" target="globalProductDid"/>\n'
                 '          <zeebe:output source="=merchantId" target="merchantId"/>\n'
                 '          <zeebe:output source="=merchantDid" target="merchantDid"/>\n'
                 '          <zeebe:output source="=offerId" target="offerId"/>\n'
                 '          <zeebe:output source="=offerDid" target="offerDid"/>\n'
                 '          <zeebe:output source="=historyWritten" target="historyWritten"/>\n'
                 '          <zeebe:output source="=matchCandidateCreated" '
                 'target="matchCandidateCreated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Upsert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Upsert" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="offer upserted">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1998,
                 '00-contracts/bpmn/ai/gftd/kakaku/upsertOffer.bpmn',
                 '2026-04-25T20:30:00Z',
                 'did:web:kakaku.etzhayyim.com',
                 'did:web:kakaku.etzhayyim.com',
                 'sys.bpmn.seed.kakaku',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-upsertOffer-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-ingestOfferFromUrl-v1',
                 'did:web:kakaku.etzhayyim.com',
                 'kakaku_ingest_offer_from_url',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_kakaku_ingest_offer_from_url"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kakaku"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="kakaku_ingest_offer_from_url" name="kakaku ingest offer from '
                 'URL" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="URL submitted">\n'
                 '      <bpmn:outgoing>Flow_Fetch</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fetch" sourceRef="Start" '
                 'targetRef="Task_Fetch"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch product page">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=string(productUrl)" target="url"/>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:input source="=20" target="timeoutSec"/>\n'
                 '          <zeebe:output source="=status" target="fetchStatus"/>\n'
                 '          <zeebe:output source="=bodyText" target="fetchedBody"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Fetch</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="Task_Fetch" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="extract and upsert offer">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="xrpc.app.etzhayyim.apps.kakaku.ingestOfferFromUrl"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=status" target="status"/>\n'
                 '          <zeebe:output source="=fetchedTitle" target="fetchedTitle"/>\n'
                 '          <zeebe:output source="=extractedName" target="extractedName"/>\n'
                 '          <zeebe:output source="=extractedPrice" target="extractedPrice"/>\n'
                 '          <zeebe:output source="=currency" target="currency"/>\n'
                 '          <zeebe:output source="=availability" target="availability"/>\n'
                 '          <zeebe:output source="=extractionMethod" target="extractionMethod"/>\n'
                 '          <zeebe:output source="=barcodeSource" target="barcodeSource"/>\n'
                 '          <zeebe:output source="=canonicalGtin14" target="canonicalGtin14"/>\n'
                 '          <zeebe:output source="=productId" target="productId"/>\n'
                 '          <zeebe:output source="=globalProductId" target="globalProductId"/>\n'
                 '          <zeebe:output source="=globalProductDid" target="globalProductDid"/>\n'
                 '          <zeebe:output source="=offerId" target="offerId"/>\n'
                 '          <zeebe:output source="=offerDid" target="offerDid"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Ingest" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="offer ingested">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3026,
                 '00-contracts/bpmn/ai/gftd/kakaku/ingestOfferFromUrl.bpmn',
                 '2026-04-25T20:30:00Z',
                 'did:web:kakaku.etzhayyim.com',
                 'did:web:kakaku.etzhayyim.com',
                 'sys.bpmn.seed.kakaku',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-ingestOfferFromUrl-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-compareOffers-v1',
                 'did:web:kakaku.etzhayyim.com',
                 'kakaku_compare_offers',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_kakaku_compare_offers"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/kakaku"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="kakaku_compare_offers" name="kakaku compare offers" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="compare requested">\n'
                 '      <bpmn:outgoing>Flow_Compare</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Compare" sourceRef="Start" '
                 'targetRef="Task_Compare"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Compare" name="rank product offers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.kakaku.compareOffers"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=productId" target="productId"/>\n'
                 '          <zeebe:output source="=bestOverall" target="bestOverall"/>\n'
                 '          <zeebe:output source="=cheapest" target="cheapest"/>\n'
                 '          <zeebe:output source="=fastest" target="fastest"/>\n'
                 '          <zeebe:output source="=offers" target="offers"/>\n'
                 '          <zeebe:output source="=suspiciousOffers" target="suspiciousOffers"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Compare</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Compare" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="offers ranked">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1645,
                 '00-contracts/bpmn/ai/gftd/kakaku/compareOffers.bpmn',
                 '2026-04-25T20:30:00Z',
                 'did:web:kakaku.etzhayyim.com',
                 'did:web:kakaku.etzhayyim.com',
                 'sys.bpmn.seed.kakaku',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-compareOffers-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-upsertOffer-v1',
                 'did:web:kakaku.etzhayyim.com',
                 'app.etzhayyim.apps.kakaku.upsertOffer',
                 'kakaku_upsert_offer',
                 90000,
                 '2026-04-25T20:30:00Z',
                 'did:web:kakaku.etzhayyim.com',
                 'did:web:kakaku.etzhayyim.com',
                 'sys.bpmn.seed.kakaku',
                 'vertex_kakaku_product,vertex_kakaku_merchant,vertex_kakaku_offer,vertex_kakaku_price_history,vertex_kakaku_match_candidate',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-upsertOffer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-ingestOfferFromUrl-v1',
                 'did:web:kakaku.etzhayyim.com',
                 'app.etzhayyim.apps.kakaku.ingestOfferFromUrl',
                 'kakaku_ingest_offer_from_url',
                 120000,
                 '2026-04-25T20:30:00Z',
                 'did:web:kakaku.etzhayyim.com',
                 'did:web:kakaku.etzhayyim.com',
                 'sys.bpmn.seed.kakaku',
                 'vertex_kakaku_product,vertex_kakaku_merchant,vertex_kakaku_offer,vertex_kakaku_price_history,vertex_kakaku_match_candidate',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-ingestOfferFromUrl-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-compareOffers-v1',
                 'did:web:kakaku.etzhayyim.com',
                 'app.etzhayyim.apps.kakaku.compareOffers',
                 'kakaku_compare_offers',
                 60000,
                 '2026-04-25T20:30:00Z',
                 'did:web:kakaku.etzhayyim.com',
                 'did:web:kakaku.etzhayyim.com',
                 'sys.bpmn.seed.kakaku',
                 'vertex_kakaku_product,vertex_kakaku_merchant,vertex_kakaku_offer,vertex_kakaku_price_history,vertex_kakaku_match_candidate',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-compareOffers-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-upsertOffer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-ingestOfferFromUrl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-compareOffers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-upsertOffer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-ingestOfferFromUrl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-compareOffers-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
