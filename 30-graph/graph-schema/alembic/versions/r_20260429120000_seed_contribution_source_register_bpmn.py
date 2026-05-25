"""Captured from Kysely migration 20260429120000_seed_contribution_source_register_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429120000_seed_contribution_source_register_bpmn"
down_revision = 'r_20260429110100_seed_isin_bpmn_actors'
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
         "      $7, 1, $8, $9, 'sys.bpmn.seed.contribution'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/contribution-source-register-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'contribution_source_register',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  contributionSourceRegister — XRPC-triggered (ADR-2604281400 Phase 3).\n'
                 '\n'
                 '  Registers an OSS / media / dataset source for GCC royalties off-chain.\n'
                 '  Writes to vertex_contribution_source and computes sourceHash = '
                 'keccak256(canonicalId).\n'
                 '  Pending on-chain: Safe owner must call '
                 'ContributionRoyaltyRegistry.registerSource()\n'
                 '  separately; until then credits accumulate in pendingEarned.\n'
                 '\n'
                 '  NSID:      app.etzhayyim.authz.registerContributionSource\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/contribution-source-register-v1\n'
                 '-->\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_contribution_source_register" '
                 'targetNamespace="https://etzhayyim.com/bpmn/contribution" exporter="hand-written" '
                 'exporterVersion="2.0">\n'
                 '  <bpmn:process id="contribution_source_register" '
                 'name="registerContributionSource" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.authz.registerContributionSource", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Register" name="write '
                 'vertex_contribution_source">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="contribution.registerSource"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=canonicalId"     target="canonicalId"/>\n'
                 '          <zeebe:input source="=contributorAddr" target="contributorAddr"/>\n'
                 '          <zeebe:input source="=royaltyBps"      target="royaltyBps"/>\n'
                 '          <zeebe:input source="=sourceType"      target="sourceType"/>\n'
                 '          <zeebe:input source="=description"     target="description"/>\n'
                 '          <zeebe:input source="=license"         target="license"/>\n'
                 '          <zeebe:output source="=ok"             target="ok"/>\n'
                 '          <zeebe:output source="=sourceHash"     target="sourceHash"/>\n'
                 '          <zeebe:output source="=vertexId"       target="vertexId"/>\n'
                 '          <zeebe:output source="=pendingOnChain" target="pendingOnChain"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_S</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Register" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit contribution.source.register '
                 'OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:bpmn.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;contribution.source.register&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ok: ok, sourceHash: sourceHash, vertexId: '
                 'vertexId, pendingOnChain: pendingOnChain}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_A</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3344,
                 '00-contracts/bpmn/ai/gftd/contribution/contributionSourceRegister.bpmn',
                 '2026-04-29T12:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/contribution-source-register-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST(30000 AS integer), 'active',\n"
         "      $5, 1, $6, $7, 'sys.bpmn.seed.contribution'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/contribution-registerSource-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'app.etzhayyim.authz.registerContributionSource',
                 'contribution_source_register',
                 '2026-04-29T12:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/contribution-registerSource-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/contribution-registerSource-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/contribution-source-register-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
