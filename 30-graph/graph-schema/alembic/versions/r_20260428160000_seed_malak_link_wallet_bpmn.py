"""Captured from Kysely migration 20260428160000_seed_malak_link_wallet_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428160000_seed_malak_link_wallet_bpmn"
down_revision = 'r_20260428150100_seed_yadoya_confirm_bpmn'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-link-wallet-to-actor-v1',
                 'did:web:malak.gftd.ai',
                 'malak_link_wallet_to_actor',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.linkWalletToActor — migrates cmdLinkWalletToActor.\n'
                 '\n'
                 '  Replaces sdk.pds.createRecord("ai.gftd.apps.malak.walletAddress") with\n'
                 '  Hyperdrive-direct INSERT into vertex_malak_wallet_address (ADR-0036).\n'
                 '  Also inserts CONTROLS_WALLET edge (ThreatActor → WalletAddress) directly.\n'
                 '\n'
                 '  Flow:\n'
                 '    Start (actorId, address, chain?, label?, confidence?, evidence?)\n'
                 '      → scriptTask: derive rkey + vertexIds\n'
                 '      → generic.db.insert (vertex_malak_wallet_address)\n'
                 '      → generic.db.insert (edge_malak_controls_wallet)\n'
                 '      → generic.audit.emit\n'
                 '      → End\n'
                 '\n'
                 '  NSID derivation (sync-bpmn-actors.py convention):\n'
                 '    path = 00-contracts/bpmn/ai/gftd/malak/linkWalletToActor.bpmn\n'
                 '    NSID = ai.gftd.apps.malak.linkWalletToActor\n'
                 '    vid  = '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-link-wallet-to-actor-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_link_wallet_to_actor"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="malak_link_wallet_to_actor" name="malak linkWalletToActor" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.linkWalletToActor", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToDerive</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToDerive" sourceRef="Start" '
                 'targetRef="Task_Derive"/>\n'
                 '\n'
                 '    <!-- Step 1: derive stable rkey + vertex IDs from actorId + chain + address '
                 '-->\n'
                 '    <bpmn:scriptTask id="Task_Derive" name="derive rkey + vertexIds">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:script\n'
                 "            expression='={\n"
                 '              resolvedChain:    if chain = null or string(chain) = "" then "btc" '
                 'else string(chain),\n'
                 '              rkey:             string join(["wallet-", if chain = null or '
                 'string(chain) = "" then "btc" else string(chain), "-", string(address)], ""),\n'
                 '              walletVertexId:   string '
                 'join(["at://did:web:malak.gftd.ai/ai.gftd.apps.malak.walletAddress/wallet-", if '
                 'chain = null or string(chain) = "" then "btc" else string(chain), "-", '
                 'string(address)], ""),\n'
                 '              actorVertexId:    string '
                 'join(["at://did:web:malak.gftd.ai/ai.gftd.apps.malak.threatActor/", '
                 'string(actorId)], ""),\n'
                 '              edgeId:           string join(["malak:edge:controls_wallet:", '
                 'string(actorId), ":", if chain = null or string(chain) = "" then "btc" else '
                 'string(chain), ":", string(address)], ""),\n'
                 '              resolvedConf:     if confidence = null then 70 else if confidence '
                 '> 100 then 100 else confidence\n'
                 "            }'\n"
                 '            resultVariable="derived"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToDerive</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToWalletInsert</bpmn:outgoing>\n'
                 '    </bpmn:scriptTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToWalletInsert" sourceRef="Task_Derive" '
                 'targetRef="Task_WalletInsert"/>\n'
                 '\n'
                 '    <!-- Step 2: INSERT wallet address vertex (Hyperdrive-direct, ADR-0036) -->\n'
                 '    <bpmn:serviceTask id="Task_WalletInsert" name="vertex_malak_wallet_address '
                 'INSERT">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_malak_wallet_address&quot;" '
                 'target="table"/>\n'
                 "          <zeebe:input source='={\n"
                 '              vertex_id:       derived.walletVertexId,\n'
                 '              rkey:            derived.rkey,\n'
                 '              repo:            "did:web:malak.gftd.ai",\n'
                 '              did:             "did:web:malak.gftd.ai",\n'
                 '              chain:           derived.resolvedChain,\n'
                 '              address:         string(address),\n'
                 '              actor_node_id:   string join(["intel:", string(actorId)], ""),\n'
                 '              label:           if label = null then "" else string(label),\n'
                 '              confidence:      derived.resolvedConf,\n'
                 '              evidence:        if evidence = null then "" else '
                 'string(evidence),\n'
                 '              linked_at:       string(now()),\n'
                 '              sensitivity_ord: 100,\n'
                 '              owner_did:       "did:web:malak.gftd.ai",\n'
                 '              created_date:    substring(string(now()), 1, 10)\n'
                 '          }\' target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=inserted" target="walletInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToWalletInsert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEdgeInsert</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEdgeInsert" sourceRef="Task_WalletInsert" '
                 'targetRef="Task_EdgeInsert"/>\n'
                 '\n'
                 '    <!-- Step 3: INSERT CONTROLS_WALLET edge (ThreatActor → WalletAddress) -->\n'
                 '    <bpmn:serviceTask id="Task_EdgeInsert" name="edge_malak_controls_wallet '
                 'INSERT">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_malak_controls_wallet&quot;" '
                 'target="table"/>\n'
                 "          <zeebe:input source='={\n"
                 '              edge_id:         derived.edgeId,\n'
                 '              src_vid:         derived.actorVertexId,\n'
                 '              dst_vid:         derived.walletVertexId,\n'
                 '              sensitivity_ord: 100,\n'
                 '              owner_did:       "did:web:malak.gftd.ai",\n'
                 '              created_date:    substring(string(now()), 1, 10)\n'
                 '          }\' target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=inserted" target="edgeInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToEdgeInsert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_EdgeInsert" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <!-- Step 4: OCEL audit -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit: malak.wallet.linked">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:malak.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;malak.wallet.linked&quot;"   '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ actorId: string(actorId), chain: '
                 'derived.resolvedChain, address: string(address), walletInserted: walletInserted, '
                 'edgeInserted: edgeInserted }" target="payload"/>\n'
                 '          <zeebe:output source="=emitted" target="auditEmitted"/>\n'
                 '          <zeebe:output source="=rkey"    target="auditRkey"/>\n'
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
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7040,
                 '00-contracts/bpmn/ai/gftd/malak/linkWalletToActor.bpmn',
                 '2026-04-28T16:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-link-wallet-to-actor-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-linkWalletToActor-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.linkWalletToActor',
                 'malak_link_wallet_to_actor',
                 15000,
                 '2026-04-28T16:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-linkWalletToActor-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-linkWalletToActor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-link-wallet-to-actor-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
