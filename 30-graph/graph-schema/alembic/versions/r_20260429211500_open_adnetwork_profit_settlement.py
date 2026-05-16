"""Captured from Kysely migration 20260429211500_open_adnetwork_profit_settlement."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429211500_open_adnetwork_profit_settlement"
down_revision = 'r_20260429211000_seed_calendar_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_profit_settlement (\n'
         '      vertex_id                 VARCHAR PRIMARY KEY,\n'
         '      settlement_id             VARCHAR NOT NULL,\n'
         '      publisher_did             VARCHAR NOT NULL,\n'
         '      window_start_ms           BIGINT NOT NULL,\n'
         '      window_end_ms             BIGINT NOT NULL,\n'
         '      impressions               BIGINT NOT NULL DEFAULT 0,\n'
         '      publisher_count           INTEGER NOT NULL DEFAULT 0,\n'
         '      gross_revenue_usd         DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         '      publisher_share_pct       DOUBLE PRECISION NOT NULL DEFAULT 70.0,\n'
         '      publisher_profit_usd      DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         '      platform_profit_usd       DOUBLE PRECISION NOT NULL DEFAULT 0.0,\n'
         "      currency                  VARCHAR NOT NULL DEFAULT 'USD',\n"
         '      chain_id                  INTEGER NOT NULL DEFAULT 260425,\n'
         '      chain_receipt_submitted   BOOLEAN NOT NULL DEFAULT false,\n'
         '      chain_receipt_tx          VARCHAR,\n'
         '      chain_receipt_reason      VARCHAR,\n'
         "      status                    VARCHAR NOT NULL DEFAULT 'settled',\n"
         '      created_at                VARCHAR NOT NULL,\n'
         '      sensitivity_ord           INTEGER NOT NULL DEFAULT 0,\n'
         '      org_id                    VARCHAR,\n'
         '      user_id                   VARCHAR,\n'
         '      actor_id                  VARCHAR,\n'
         '      actor_did                 VARCHAR,\n'
         '      org_did                   VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1, $4,\n'
         "      4908, $5, 'active', $6, 1,\n"
         '      $7, $8, $9, $10, $11\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-adnetwork-settle-business-profit-v1',
                 'did:web:yoro.gftd.ai',
                 'open_adnetwork_settle_business_profit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Business actor autonomous profit settlement.\n'
                 '\n'
                 '  Cadence:\n'
                 '    - timer: every 1 hour\n'
                 '    - manual start: operator/API smoke\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. rw.health.probe\n'
                 '    2. business.profit.settleOpenAdnetwork\n'
                 '       - aggregates openAdNetwork impressions for the window\n'
                 '       - writes vertex_open_adnetwork_profit_settlement\n'
                 '       - submits an ActorRuntimeRegistry receipt when chain env is present\n'
                 '    3. generic.audit.emit\n'
                 '-->\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_settle_business_profit" '
                 'targetNamespace="https://gftd.ai/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_settle_business_profit" '
                 'name="settleBusinessProfit" isExecutable="true">\n'
                 '    <bpmn:startEvent id="StartManual" name="manual settle">\n'
                 '      <bpmn:outgoing>Flow_ManualToHealth</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ManualToHealth" sourceRef="StartManual" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="every 1 hour">\n'
                 '      <bpmn:outgoing>Flow_TimerToHealth</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_TimerToHealth" sourceRef="StartTimer" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rw.health.probe"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ManualToHealth</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_TimerToHealth</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToSettle</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSettle" sourceRef="Task_Health" '
                 'targetRef="Task_Settle"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Settle" name="settle adnetwork profit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="business.profit.settleOpenAdnetwork"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if settlementId != null then settlementId else '
                 '&quot;&quot;" target="settlementId"/>\n'
                 '          <zeebe:input source="=if windowHours != null then windowHours else 24" '
                 'target="windowHours"/>\n'
                 '          <zeebe:input source="=if publisherDid != null then publisherDid else '
                 '&quot;__all__&quot;" target="publisherDid"/>\n'
                 '          <zeebe:input source="=if publisherSharePct != null then '
                 'publisherSharePct else 70.0" target="publisherSharePct"/>\n'
                 '          <zeebe:input source="=if minGrossRevenueUsd != null then '
                 'minGrossRevenueUsd else 0.0" target="minGrossRevenueUsd"/>\n'
                 '          <zeebe:input source="=if submitReceipt != null then submitReceipt else '
                 'true" target="submitReceipt"/>\n'
                 '          <zeebe:output source="=settlementId" target="profitSettlementId"/>\n'
                 '          <zeebe:output source="=vertexId" target="profitVertexId"/>\n'
                 '          <zeebe:output source="=grossRevenueUsd" target="grossRevenueUsd"/>\n'
                 '          <zeebe:output source="=publisherProfitUsd" '
                 'target="publisherProfitUsd"/>\n'
                 '          <zeebe:output source="=platformProfitUsd" '
                 'target="platformProfitUsd"/>\n'
                 '          <zeebe:output source="=chainReceiptSubmitted" '
                 'target="chainReceiptSubmitted"/>\n'
                 '          <zeebe:output source="=chainReceiptTx" target="chainReceiptTx"/>\n'
                 '          <zeebe:output source="=status" target="profitStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSettle</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Settle" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit profit settlement">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:yoro.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;business.profit.settleOpenAdnetwork&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={settlementId: profitSettlementId, vertexId: '
                 'profitVertexId, status: profitStatus, grossRevenueUsd: grossRevenueUsd, '
                 'publisherProfitUsd: publisherProfitUsd, platformProfitUsd: platformProfitUsd, '
                 'chainReceiptSubmitted: chainReceiptSubmitted, chainReceiptTx: chainReceiptTx}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="settled">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/settleBusinessProfit.bpmn',
                 '2026-04-29T21:15:00+09:00',
                 'did:web:yoro.gftd.ai',
                 'did:web:yoro.gftd.ai',
                 'sys.bpmn.seed.business-profit',
                 'did:web:yoro.gftd.ai',
                 'did:web:yoro.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-adnetwork-settle-business-profit-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         '    SET "xml" = $1,\n'
         '        xml_byte_size = 4908,\n'
         '        source_path = $2,\n'
         "        status = 'active',\n"
         '        deployed_at = NULL,\n'
         '        deployed_zeebe_key = CAST(NULL AS BIGINT)\n'
         '    WHERE vertex_id = $3\n'
         '  ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Business actor autonomous profit settlement.\n'
                 '\n'
                 '  Cadence:\n'
                 '    - timer: every 1 hour\n'
                 '    - manual start: operator/API smoke\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. rw.health.probe\n'
                 '    2. business.profit.settleOpenAdnetwork\n'
                 '       - aggregates openAdNetwork impressions for the window\n'
                 '       - writes vertex_open_adnetwork_profit_settlement\n'
                 '       - submits an ActorRuntimeRegistry receipt when chain env is present\n'
                 '    3. generic.audit.emit\n'
                 '-->\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_settle_business_profit" '
                 'targetNamespace="https://gftd.ai/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_settle_business_profit" '
                 'name="settleBusinessProfit" isExecutable="true">\n'
                 '    <bpmn:startEvent id="StartManual" name="manual settle">\n'
                 '      <bpmn:outgoing>Flow_ManualToHealth</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ManualToHealth" sourceRef="StartManual" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="every 1 hour">\n'
                 '      <bpmn:outgoing>Flow_TimerToHealth</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_TimerToHealth" sourceRef="StartTimer" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rw.health.probe"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ManualToHealth</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_TimerToHealth</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToSettle</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSettle" sourceRef="Task_Health" '
                 'targetRef="Task_Settle"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Settle" name="settle adnetwork profit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="business.profit.settleOpenAdnetwork"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if settlementId != null then settlementId else '
                 '&quot;&quot;" target="settlementId"/>\n'
                 '          <zeebe:input source="=if windowHours != null then windowHours else 24" '
                 'target="windowHours"/>\n'
                 '          <zeebe:input source="=if publisherDid != null then publisherDid else '
                 '&quot;__all__&quot;" target="publisherDid"/>\n'
                 '          <zeebe:input source="=if publisherSharePct != null then '
                 'publisherSharePct else 70.0" target="publisherSharePct"/>\n'
                 '          <zeebe:input source="=if minGrossRevenueUsd != null then '
                 'minGrossRevenueUsd else 0.0" target="minGrossRevenueUsd"/>\n'
                 '          <zeebe:input source="=if submitReceipt != null then submitReceipt else '
                 'true" target="submitReceipt"/>\n'
                 '          <zeebe:output source="=settlementId" target="profitSettlementId"/>\n'
                 '          <zeebe:output source="=vertexId" target="profitVertexId"/>\n'
                 '          <zeebe:output source="=grossRevenueUsd" target="grossRevenueUsd"/>\n'
                 '          <zeebe:output source="=publisherProfitUsd" '
                 'target="publisherProfitUsd"/>\n'
                 '          <zeebe:output source="=platformProfitUsd" '
                 'target="platformProfitUsd"/>\n'
                 '          <zeebe:output source="=chainReceiptSubmitted" '
                 'target="chainReceiptSubmitted"/>\n'
                 '          <zeebe:output source="=chainReceiptTx" target="chainReceiptTx"/>\n'
                 '          <zeebe:output source="=status" target="profitStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSettle</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Settle" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit profit settlement">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:yoro.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;business.profit.settleOpenAdnetwork&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={settlementId: profitSettlementId, vertexId: '
                 'profitVertexId, status: profitStatus, grossRevenueUsd: grossRevenueUsd, '
                 'publisherProfitUsd: publisherProfitUsd, platformProfitUsd: platformProfitUsd, '
                 'chainReceiptSubmitted: chainReceiptSubmitted, chainReceiptTx: chainReceiptTx}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="settled">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/settleBusinessProfit.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-adnetwork-settle-business-profit-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      180000, 'vertex_open_adnetwork_profit_settlement',\n"
         "      'active', $5, 1, $6, $7, $8,\n"
         '      $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-adnetwork-settle-business-profit-v1',
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.openAdnetwork.settleBusinessProfit',
                 'open_adnetwork_settle_business_profit',
                 '2026-04-29T21:15:00+09:00',
                 'did:web:yoro.gftd.ai',
                 'did:web:yoro.gftd.ai',
                 'sys.bpmn.seed.business-profit',
                 'did:web:yoro.gftd.ai',
                 'did:web:yoro.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-adnetwork-settle-business-profit-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         "    SET write_table_allowlist = 'vertex_open_adnetwork_profit_settlement',\n"
         '        result_timeout_ms = 180000,\n'
         "        status = 'active'\n"
         '    WHERE bpmn_process_id = $1\n'
         '      AND nsid = $2\n'
         '  ',
  'parameters': ['open_adnetwork_settle_business_profit',
                 'ai.gftd.apps.openAdnetwork.settleBusinessProfit']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-adnetwork-settle-business-profit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-adnetwork-settle-business-profit-v1']},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_adnetwork_profit_settlement', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
