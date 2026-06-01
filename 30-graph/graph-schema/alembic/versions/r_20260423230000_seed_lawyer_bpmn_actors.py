"""Captured from Kysely migration 20260423230000_seed_lawyer_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260423230000_seed_lawyer_bpmn_actors"
down_revision = 'r_20260423220000_seed_oshinobi_bpmn_actors'
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
         "      'sys.bpmn.seed.lawyer'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/lawyer-health-v1',
                 'did:web:lawyer.etzhayyim.com',
                 'lawyer_health',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Phase D pilot #1 (ADR-0056, 2026-04-23): lawyer.health — retire the\n'
                 '  38-LoC lawyer.etzhayyim.com Worker by mapping its single XRPC command to\n'
                 '  one `generic.audit.emit` task. No DB, no LLM, no HTTP.\n'
                 '\n'
                 '  Flow:\n'
                 '    Start → generic.audit.emit → End\n'
                 '\n'
                 '  Output variables (returned as XRPC response body by bpmn-dispatcher):\n'
                 '    ok        = true  (audit emitted)\n'
                 '    nanoid    = "334bbd5f"  (lawyer.etzhayyim.com worker nanoid, grandfathered)\n'
                 '    handle    = "lawyer.etzhayyim.com"\n'
                 '    tenant    = "etzhayyim"\n'
                 '    note      = "MVP stub — record writes delegate to lawfirm Worker via firmDid '
                 'scoping"\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_lawyer_health"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/lawyer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="lawyer_health" name="lawyer health" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="health">\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Start" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit: lawyer.health probe">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:lawyer.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;lawyer.health.probe&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ nanoid: &quot;334bbd5f&quot; }" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=true"                     target="ok"/>\n'
                 '          <zeebe:output source="=&quot;334bbd5f&quot;"                '
                 'target="nanoid"/>\n'
                 '          <zeebe:output source="=&quot;lawyer.etzhayyim.com&quot;"           '
                 'target="handle"/>\n'
                 '          <zeebe:output source="=&quot;etzhayyim&quot;"                 '
                 'target="tenant"/>\n'
                 '          <zeebe:output source="=&quot;MVP stub — record writes delegate to '
                 'lawfirm Worker via firmDid scoping&quot;" target="note"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="healthy">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2507,
                 '00-contracts/bpmn/ai/gftd/lawyer/health.bpmn',
                 '2026-04-23T23:00:00Z',
                 'did:web:lawyer.etzhayyim.com',
                 'did:web:lawyer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/lawyer-health-v1']},
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
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         "      'sys.bpmn.seed.lawyer'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/lawyer-health-v1',
                 'did:web:lawyer.etzhayyim.com',
                 'app.etzhayyim.apps.lawyer.health',
                 'lawyer_health',
                 5000,
                 '2026-04-23T23:00:00Z',
                 'did:web:lawyer.etzhayyim.com',
                 'did:web:lawyer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/lawyer-health-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/lawyer-health-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/lawyer-health-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
