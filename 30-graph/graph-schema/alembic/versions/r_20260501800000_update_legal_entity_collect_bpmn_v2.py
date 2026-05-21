"""Captured from Kysely migration 20260501800000_update_legal_entity_collect_bpmn_v2."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501800000_update_legal_entity_collect_bpmn_v2"
down_revision = 'r_20260501800000_mv_world_vertex_oil_coverage'
branch_labels = None
depends_on = None

UP = [{'sql': 'UPDATE vertex_bpmn_process_def SET "version" = 2 WHERE bpmn_process_id = $1',
  'parameters': ['legal_entity_collect_cze']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET "xml" = $1 WHERE bpmn_process_id = $2',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_cze" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_cze" name="legal '
                 'entity collect CZE registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="CZE registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit CZE registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectCze"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=query" target="query"/><zeebe:output '
                 'source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit CZE registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectCze&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, query: query, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="CZE registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>',
                 'legal_entity_collect_cze']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET xml_byte_size = $1 WHERE bpmn_process_id = $2',
  'parameters': [2104, 'legal_entity_collect_cze']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET deployed_at = $1 WHERE bpmn_process_id = $2',
  'parameters': ['2026-05-08T00:43:14.489Z', 'legal_entity_collect_cze']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET "version" = 2 WHERE bpmn_process_id = $1',
  'parameters': ['legal_entity_collect_dnk']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET "xml" = $1 WHERE bpmn_process_id = $2',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_dnk" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_dnk" name="legal '
                 'entity collect DNK registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="DNK registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit DNK registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectDnk"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=search" target="search"/><zeebe:output '
                 'source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit DNK registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectDnk&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, search: search, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="DNK registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>',
                 'legal_entity_collect_dnk']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET xml_byte_size = $1 WHERE bpmn_process_id = $2',
  'parameters': [2108, 'legal_entity_collect_dnk']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET deployed_at = $1 WHERE bpmn_process_id = $2',
  'parameters': ['2026-05-08T00:43:14.489Z', 'legal_entity_collect_dnk']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET "version" = 2 WHERE bpmn_process_id = $1',
  'parameters': ['legal_entity_collect_nld']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET "xml" = $1 WHERE bpmn_process_id = $2',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_entity_collect_nld" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-entity" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="legal_entity_collect_nld" name="legal '
                 'entity collect NLD registry" isExecutable="true"><bpmn:startEvent id="Start" '
                 'name="NLD registry collection '
                 'requested"><bpmn:outgoing>Flow_Fetch</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_Fetch" sourceRef="Start" targetRef="Task_Fetch"/><bpmn:serviceTask '
                 'id="Task_Fetch" name="fetch and commit NLD registry '
                 'pages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legalEntity.registry.collectNld"/><zeebe:ioMapping><zeebe:input '
                 'source="=pages" target="pages"/><zeebe:input source="=pageSize" '
                 'target="pageSize"/><zeebe:input source="=startPage" '
                 'target="startPage"/><zeebe:input source="=query" target="query"/><zeebe:output '
                 'source="=result" '
                 'target="result"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_Audit" sourceRef="Task_Fetch" targetRef="Task_Audit"/><bpmn:serviceTask '
                 'id="Task_Audit" name="audit NLD registry '
                 'collection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-entity.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-entity.collectNld&quot;" target="action"/><zeebe:input '
                 'source="={ pages: pages, pageSize: pageSize, query: query, result: result }" '
                 'target="payload"/><zeebe:output source="=rkey" '
                 'target="auditRkey"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_End" sourceRef="Task_Audit" targetRef="End"/><bpmn:endEvent id="End" '
                 'name="NLD registry collection '
                 'committed"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>',
                 'legal_entity_collect_nld']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET xml_byte_size = $1 WHERE bpmn_process_id = $2',
  'parameters': [2104, 'legal_entity_collect_nld']},
 {'sql': 'UPDATE vertex_bpmn_process_def SET deployed_at = $1 WHERE bpmn_process_id = $2',
  'parameters': ['2026-05-08T00:43:14.489Z', 'legal_entity_collect_nld']}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
