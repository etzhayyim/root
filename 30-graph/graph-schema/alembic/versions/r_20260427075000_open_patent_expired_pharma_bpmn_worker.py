"""Captured from Kysely migration 20260427075000_open_patent_expired_pharma_bpmn_worker."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427075000_open_patent_expired_pharma_bpmn_worker"
down_revision = 'r_20260427074000_seed_pharma_policy_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_regulatory_blocker (\n'
         '      vertex_id          varchar PRIMARY KEY,\n'
         '      _seq               bigint,\n'
         '      created_date       date,\n'
         '      sensitivity_ord    int,\n'
         '      owner_did          varchar,\n'
         '      patent_vertex_id   varchar NOT NULL,\n'
         '      patent_number      varchar NOT NULL,\n'
         '      jurisdiction       varchar NOT NULL,\n'
         '      product_id         varchar,\n'
         '      blocker_type       varchar NOT NULL,\n'
         '      blocking_until     varchar NOT NULL,\n'
         '      source             varchar,\n'
         '      evidence_uri       varchar,\n'
         '      as_of              varchar NOT NULL,\n'
         '      active             boolean NOT NULL,\n'
         '      status             varchar NOT NULL,\n'
         '      created_at         varchar,\n'
         '      org_id             varchar,\n'
         '      user_id            varchar,\n'
         '      actor_id           varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_expiry_backlog_run (\n'
         '      vertex_id          varchar PRIMARY KEY,\n'
         '      _seq               bigint,\n'
         '      created_date       date,\n'
         '      sensitivity_ord    int,\n'
         '      owner_did          varchar,\n'
         '      as_of              varchar NOT NULL,\n'
         '      jurisdiction       varchar,\n'
         '      limit_count        int,\n'
         '      scanned_count      int NOT NULL,\n'
         '      candidate_count    int NOT NULL,\n'
         '      inserted_count     int NOT NULL,\n'
         '      status             varchar NOT NULL,\n'
         '      created_at         varchar,\n'
         '      org_id             varchar,\n'
         '      user_id            varchar,\n'
         '      actor_id           varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_drug_expiry (\n'
         '      vertex_id                    varchar PRIMARY KEY,\n'
         '      _seq                         bigint,\n'
         '      created_date                 date,\n'
         '      sensitivity_ord              int,\n'
         '      owner_did                    varchar,\n'
         '      patent_vertex_id             varchar NOT NULL,\n'
         '      patent_number                varchar NOT NULL,\n'
         '      jurisdiction                 varchar NOT NULL,\n'
         '      product_id                   varchar,\n'
         '      atc_code                     varchar,\n'
         '      ndc_code                     varchar,\n'
         '      expiry_date                  varchar NOT NULL,\n'
         '      blocking_exclusivity_until   varchar,\n'
         '      as_of                        varchar NOT NULL,\n'
         '      eligible                     boolean NOT NULL,\n'
         '      status                       varchar NOT NULL,\n'
         '      created_at                   varchar,\n'
         '      org_id                       varchar,\n'
         '      user_id                      varchar,\n'
         '      actor_id                     varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_generic_candidate (\n'
         '      vertex_id              varchar PRIMARY KEY,\n'
         '      _seq                   bigint,\n'
         '      created_date           date,\n'
         '      sensitivity_ord        int,\n'
         '      owner_did              varchar,\n'
         '      expiry_screen_vid      varchar NOT NULL,\n'
         '      product_id             varchar NOT NULL,\n'
         '      candidate_kind         varchar NOT NULL,\n'
         '      manufacturer_org_id    varchar,\n'
         '      plant_org_id           varchar,\n'
         '      dosage_form            varchar,\n'
         '      process_type           varchar,\n'
         '      target_market          varchar,\n'
         '      seiyaku_process_id     varchar NOT NULL,\n'
         '      status                 varchar NOT NULL,\n'
         '      created_at             varchar,\n'
         '      org_id                 varchar,\n'
         '      user_id                varchar,\n'
         '      actor_id               varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_handoff (\n'
         '      vertex_id               varchar PRIMARY KEY,\n'
         '      _seq                    bigint,\n'
         '      created_date            date,\n'
         '      sensitivity_ord         int,\n'
         '      owner_did               varchar,\n'
         '      generic_candidate_vid   varchar NOT NULL,\n'
         '      product_id              varchar NOT NULL,\n'
         '      seiyaku_process_id      varchar NOT NULL,\n'
         '      target_market           varchar,\n'
         '      manufacturer_org_id     varchar,\n'
         '      plant_org_id            varchar,\n'
         '      dosage_form             varchar,\n'
         '      batch_intent            varchar,\n'
         '      status                  varchar NOT NULL,\n'
         '      created_at              varchar,\n'
         '      org_id                  varchar,\n'
         '      user_id                 varchar,\n'
         '      actor_id                varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_batch_draft (\n'
         '      vertex_id               varchar PRIMARY KEY,\n'
         '      _seq                    bigint,\n'
         '      created_date            date,\n'
         '      sensitivity_ord         int,\n'
         '      owner_did               varchar,\n'
         '      handoff_vid             varchar NOT NULL,\n'
         '      product_id              varchar NOT NULL,\n'
         '      manufacturer_org_id     varchar NOT NULL,\n'
         '      plant_org_id            varchar NOT NULL,\n'
         '      product_code            varchar NOT NULL,\n'
         '      batch_number            varchar NOT NULL,\n'
         '      dosage_form             varchar,\n'
         '      target_market           varchar,\n'
         '      seiyaku_process_id      varchar NOT NULL,\n'
         '      batch_payload           jsonb,\n'
         '      status                  varchar NOT NULL,\n'
         '      created_at              varchar,\n'
         '      org_id                  varchar,\n'
         '      user_id                 varchar,\n'
         '      actor_id                varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_batch_validation (\n'
         '      vertex_id             varchar PRIMARY KEY,\n'
         '      _seq                  bigint,\n'
         '      created_date          date,\n'
         '      sensitivity_ord       int,\n'
         '      owner_did             varchar,\n'
         '      batch_draft_vid       varchar,\n'
         '      passed                boolean NOT NULL,\n'
         '      status                varchar NOT NULL,\n'
         '      findings              jsonb,\n'
         '      created_at            varchar,\n'
         '      org_id                varchar,\n'
         '      user_id               varchar,\n'
         '      actor_id              varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_start_request (\n'
         '      vertex_id          varchar PRIMARY KEY,\n'
         '      _seq               bigint,\n'
         '      created_date       date,\n'
         '      sensitivity_ord    int,\n'
         '      owner_did          varchar,\n'
         '      batch_draft_vid    varchar NOT NULL,\n'
         '      validation_vid     varchar,\n'
         '      start_nsid         varchar NOT NULL,\n'
         '      bpmn_process_id    varchar NOT NULL,\n'
         '      request_payload    jsonb,\n'
         '      status             varchar NOT NULL,\n'
         '      created_at         varchar,\n'
         '      org_id             varchar,\n'
         '      user_id            varchar,\n'
         '      actor_id           varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_start_ack (\n'
         '      vertex_id                 varchar PRIMARY KEY,\n'
         '      _seq                      bigint,\n'
         '      created_date              date,\n'
         '      sensitivity_ord           int,\n'
         '      owner_did                 varchar,\n'
         '      start_request_vid         varchar NOT NULL,\n'
         '      seiyaku_instance_key      bigint,\n'
         '      seiyaku_batch_vertex_id   varchar,\n'
         '      status                    varchar NOT NULL,\n'
         '      message                   varchar,\n'
         '      created_at                varchar,\n'
         '      org_id                    varchar,\n'
         '      user_id                   varchar,\n'
         '      actor_id                  varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_patent_seiyaku_progress (\n'
         '      vertex_id                 varchar PRIMARY KEY,\n'
         '      _seq                      bigint,\n'
         '      created_date              date,\n'
         '      sensitivity_ord           int,\n'
         '      owner_did                 varchar,\n'
         '      start_request_vid         varchar NOT NULL,\n'
         '      ack_vid                   varchar,\n'
         '      progress_status           varchar NOT NULL,\n'
         '      seiyaku_instance_key      bigint,\n'
         '      seiyaku_batch_vertex_id   varchar,\n'
         '      message                   varchar,\n'
         '      created_at                varchar,\n'
         '      org_id                    varchar,\n'
         '      user_id                   varchar,\n'
         '      actor_id                  varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-summarize-seiyaku-start-progress-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_summarize_seiyaku_start_progress',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_summarize_seiyaku_start_progress" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_summarize_seiyaku_start_progress" '
                 'name="summarizeSeiyakuStartProgress" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Summarize"/>\n'
                 '    <bpmn:serviceTask id="Task_Summarize" name="summarize seiyaku start '
                 'progress">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.genericManufacturing.summarizeSeiyakuStartProgress"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={startRequestVid: startRequestVid, '
                 'startRequestStatus: startRequestStatus, ackVid: ackVid, ackStatus: ackStatus, '
                 'seiyakuInstanceKey: seiyakuInstanceKey, seiyakuBatchVertexId: '
                 'seiyakuBatchVertexId, message: message, dryRun: dryRun}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=progressStatus" target="progressStatus"/><zeebe:output '
                 'source="=startRequestVid" target="startRequestVid"/><zeebe:output '
                 'source="=ackVid" target="ackVid"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Summarize" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.genericManufacturing.summarizeSeiyakuStartProgress&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, progressStatus: '
                 'progressStatus, startRequestVid: startRequestVid, ackVid: ackVid}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2477,
                 '00-contracts/bpmn/ai/gftd/open-patent/summarizeSeiyakuStartProgress.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-summarize-seiyaku-start-progress-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-acknowledge-seiyaku-batch-start-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_acknowledge_seiyaku_batch_start',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_acknowledge_seiyaku_batch_start" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_acknowledge_seiyaku_batch_start" '
                 'name="acknowledgeSeiyakuBatchStart" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Ack"/>\n'
                 '    <bpmn:serviceTask id="Task_Ack" name="acknowledge seiyaku batch start">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.genericManufacturing.ackSeiyakuBatchStart"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={startRequestVid: startRequestVid, '
                 'seiyakuInstanceKey: seiyakuInstanceKey, seiyakuBatchVertexId: '
                 'seiyakuBatchVertexId, status: status, message: message, dryRun: dryRun}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=status" target="status"/><zeebe:output source="=startRequestVid" '
                 'target="startRequestVid"/><zeebe:output source="=seiyakuInstanceKey" '
                 'target="seiyakuInstanceKey"/><zeebe:output source="=seiyakuBatchVertexId" '
                 'target="seiyakuBatchVertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Ack" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.genericManufacturing.ackSeiyakuBatchStart&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, status: status, '
                 'startRequestVid: startRequestVid, seiyakuInstanceKey: seiyakuInstanceKey, '
                 'seiyakuBatchVertexId: seiyakuBatchVertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2511,
                 '00-contracts/bpmn/ai/gftd/open-patent/acknowledgeSeiyakuBatchStart.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-acknowledge-seiyaku-batch-start-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-queue-seiyaku-batch-start-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_queue_seiyaku_batch_start',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_queue_seiyaku_batch_start" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_queue_seiyaku_batch_start" '
                 'name="queueSeiyakuBatchStart" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Queue"/>\n'
                 '    <bpmn:serviceTask id="Task_Queue" name="queue seiyaku batch start">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.genericManufacturing.queueSeiyakuBatchStart"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={batchDraftVid: batchDraftVid, validationVid: '
                 'validationVid, validationPassed: validationPassed, batchPayload: batchPayload, '
                 'dryRun: dryRun}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=startNsid" target="startNsid"/><zeebe:output source="=bpmnProcessId" '
                 'target="bpmnProcessId"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Queue" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.genericManufacturing.queueSeiyakuBatchStart&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, startNsid: '
                 'startNsid, bpmnProcessId: bpmnProcessId, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2305,
                 '00-contracts/bpmn/ai/gftd/open-patent/queueSeiyakuBatchStart.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-queue-seiyaku-batch-start-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-validate-seiyaku-batch-draft-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_validate_seiyaku_batch_draft',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_validate_seiyaku_batch_draft" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_validate_seiyaku_batch_draft" '
                 'name="validateSeiyakuBatchDraft" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Validate"/>\n'
                 '    <bpmn:serviceTask id="Task_Validate" name="validate seiyaku batch draft">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.genericManufacturing.validateSeiyakuBatchDraft"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={batchDraftVid: batchDraftVid, batchPayload: '
                 'batchPayload, manufacturerOrgId: manufacturerOrgId, plantOrgId: plantOrgId, '
                 'productCode: productCode, batchNumber: batchNumber, dosageForm: dosageForm, '
                 'targetMarket: targetMarket, dryRun: dryRun}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=passed" target="passed"/><zeebe:output source="=status" '
                 'target="status"/><zeebe:output source="=findings" target="findings"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Validate" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.genericManufacturing.validateSeiyakuBatchDraft&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, passed: passed, '
                 'status: status, findings: findings}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2400,
                 '00-contracts/bpmn/ai/gftd/open-patent/validateSeiyakuBatchDraft.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-validate-seiyaku-batch-draft-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-prepare-seiyaku-batch-draft-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_prepare_seiyaku_batch_draft',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_prepare_seiyaku_batch_draft" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_prepare_seiyaku_batch_draft" '
                 'name="prepareSeiyakuBatchDraft" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Prepare"/>\n'
                 '    <bpmn:serviceTask id="Task_Prepare" name="prepare seiyaku batch draft">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.genericManufacturing.prepareSeiyakuBatchDraft"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={handoffVid: handoffVid, productId: productId, '
                 'manufacturerOrgId: manufacturerOrgId, plantOrgId: plantOrgId, productCode: '
                 'productCode, batchNumber: batchNumber, dosageForm: dosageForm, targetMarket: '
                 'targetMarket, dryRun: dryRun}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=seiyakuProcessId" target="seiyakuProcessId"/><zeebe:output '
                 'source="=batchNumber" target="batchNumber"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Prepare" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.genericManufacturing.prepareSeiyakuBatchDraft&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, seiyakuProcessId: '
                 'seiyakuProcessId, batchNumber: batchNumber, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2431,
                 '00-contracts/bpmn/ai/gftd/open-patent/prepareSeiyakuBatchDraft.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-prepare-seiyaku-batch-draft-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-handoff-generic-candidate-to-seiyaku-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_handoff_generic_candidate_to_seiyaku',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_handoff_generic_candidate_to_seiyaku" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_handoff_generic_candidate_to_seiyaku" '
                 'name="handoffGenericCandidateToSeiyaku" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Handoff"/>\n'
                 '    <bpmn:serviceTask id="Task_Handoff" name="handoff generic candidate to '
                 'seiyaku">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.genericManufacturing.handoffSeiyaku"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={genericCandidateVid: genericCandidateVid, '
                 'productId: productId, seiyakuProcessId: seiyakuProcessId, targetMarket: '
                 'targetMarket, manufacturerOrgId: manufacturerOrgId, plantOrgId: plantOrgId, '
                 'dosageForm: dosageForm, batchIntent: batchIntent, dryRun: dryRun}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=seiyakuProcessId" target="seiyakuProcessId"/><zeebe:output '
                 'source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Handoff" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.genericManufacturing.handoffSeiyaku&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, seiyakuProcessId: '
                 'seiyakuProcessId, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2390,
                 '00-contracts/bpmn/ai/gftd/open-patent/handoffGenericCandidateToSeiyaku.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-handoff-generic-candidate-to-seiyaku-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-record-drug-regulatory-blocker-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_record_drug_regulatory_blocker',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_record_drug_regulatory_blocker" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_record_drug_regulatory_blocker" '
                 'name="recordDrugRegulatoryBlocker" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Record"/>\n'
                 '    <bpmn:serviceTask id="Task_Record" name="record drug regulatory blocker">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.expiredDrugPatent.recordBlocker"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={patentVertexId: patentVertexId, patentNumber: '
                 'patentNumber, jurisdiction: jurisdiction, productId: productId, blockerType: '
                 'blockerType, blockingUntil: blockingUntil, source: source, evidenceUri: '
                 'evidenceUri, asOf: asOf, dryRun: dryRun}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=active" target="active"/><zeebe:output source="=status" '
                 'target="status"/><zeebe:output source="=blockingUntil" target="blockingUntil"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Record" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.expiredDrugPatent.recordBlocker&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, active: active, '
                 'status: status, blockingUntil: blockingUntil}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2388,
                 '00-contracts/bpmn/ai/gftd/open-patent/recordDrugRegulatoryBlocker.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-record-drug-regulatory-blocker-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-run-expired-drug-patent-pipeline-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_run_expired_drug_patent_pipeline',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_run_expired_drug_patent_pipeline" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_run_expired_drug_patent_pipeline" '
                 'name="runExpiredDrugPatentPipeline" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="run expired drug patent pipeline">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.expiredDrugPatent.pipeline"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={asOf: asOf, limit: limit, jurisdiction: '
                 'jurisdiction, candidateKind: candidateKind, autoHandoffToSeiyaku: '
                 'autoHandoffToSeiyaku, autoPrepareSeiyakuBatchDraft: '
                 'autoPrepareSeiyakuBatchDraft, autoValidateSeiyakuBatchDraft: '
                 'autoValidateSeiyakuBatchDraft, autoQueueSeiyakuBatchStart: '
                 'autoQueueSeiyakuBatchStart, dryRun: dryRun, rows: rows}" target="payload"/>\n'
                 '          <zeebe:output source="=runVertexId" '
                 'target="runVertexId"/><zeebe:output source="=collectedCount" '
                 'target="collectedCount"/><zeebe:output source="=screenedCount" '
                 'target="screenedCount"/><zeebe:output source="=plannedCount" '
                 'target="plannedCount"/><zeebe:output source="=handoffCount" '
                 'target="handoffCount"/><zeebe:output source="=draftCount" '
                 'target="draftCount"/><zeebe:output source="=validationCount" '
                 'target="validationCount"/><zeebe:output source="=startRequestCount" '
                 'target="startRequestCount"/><zeebe:output source="=skippedPlanCount" '
                 'target="skippedPlanCount"/><zeebe:output source="=skippedDraftCount" '
                 'target="skippedDraftCount"/><zeebe:output source="=skippedQueueCount" '
                 'target="skippedQueueCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Run" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.expiredDrugPatent.pipeline&quot;" '
                 'target="action"/><zeebe:input source="={runVertexId: runVertexId, '
                 'collectedCount: collectedCount, screenedCount: screenedCount, plannedCount: '
                 'plannedCount, handoffCount: handoffCount, draftCount: draftCount, '
                 'validationCount: validationCount, startRequestCount: startRequestCount, '
                 'skippedPlanCount: skippedPlanCount, skippedDraftCount: skippedDraftCount, '
                 'skippedQueueCount: skippedQueueCount}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3238,
                 '00-contracts/bpmn/ai/gftd/open-patent/runExpiredDrugPatentPipeline.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-run-expired-drug-patent-pipeline-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-collect-expired-drug-patent-backlog-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_collect_expired_drug_patent_backlog',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_collect_expired_drug_patent_backlog" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_collect_expired_drug_patent_backlog" '
                 'name="collectExpiredDrugPatentBacklog" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Collect"/>\n'
                 '    <bpmn:serviceTask id="Task_Collect" name="collect expired drug patent '
                 'backlog">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.expiredDrugPatent.collect"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={asOf: asOf, limit: limit, jurisdiction: '
                 'jurisdiction, dryRun: dryRun, rows: rows}" target="payload"/>\n'
                 '          <zeebe:output source="=runVertexId" '
                 'target="runVertexId"/><zeebe:output source="=scannedCount" '
                 'target="scannedCount"/><zeebe:output source="=candidateCount" '
                 'target="candidateCount"/><zeebe:output source="=insertedCount" '
                 'target="insertedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Collect" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.expiredDrugPatent.collect&quot;" '
                 'target="action"/><zeebe:input source="={runVertexId: runVertexId, scannedCount: '
                 'scannedCount, candidateCount: candidateCount, insertedCount: insertedCount}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2312,
                 '00-contracts/bpmn/ai/gftd/open-patent/collectExpiredDrugPatentBacklog.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-collect-expired-drug-patent-backlog-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-screen-expired-drug-patent-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_screen_expired_drug_patent',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_screen_expired_drug_patent" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_screen_expired_drug_patent" '
                 'name="screenExpiredDrugPatent" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Screen"/>\n'
                 '    <bpmn:serviceTask id="Task_Screen" name="screen expired drug patent">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.expiredDrugPatent.screen"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={patentVertexId: patentVertexId, patentNumber: '
                 'patentNumber, jurisdiction: jurisdiction, productId: productId, atcCode: '
                 'atcCode, ndcCode: ndcCode, expiryDate: expiryDate, blockingExclusivityUntil: '
                 'blockingExclusivityUntil, asOf: asOf}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=eligible" target="eligible"/><zeebe:output source="=status" '
                 'target="status"/><zeebe:output source="=asOf" target="asOf"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Screen" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.expiredDrugPatent.screen&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, eligible: eligible, '
                 'status: status, asOf: asOf}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2328,
                 '00-contracts/bpmn/ai/gftd/open-patent/screenExpiredDrugPatent.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-screen-expired-drug-patent-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-start-generic-manufacturing-candidate-v1',
                 'did:web:open-patent.gftd.ai',
                 'open_patent_start_generic_manufacturing_candidate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_open_patent_start_generic_manufacturing_candidate" '
                 'targetNamespace="https://gftd.ai/bpmn/open-patent" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_patent_start_generic_manufacturing_candidate" '
                 'name="startGenericManufacturingCandidate" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Plan"/>\n'
                 '    <bpmn:serviceTask id="Task_Plan" name="plan generic manufacturing '
                 'candidate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="openPatent.genericManufacturing.plan"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={expiryScreenVid: expiryScreenVid, productId: '
                 'productId, candidateKind: candidateKind, manufacturerOrgId: manufacturerOrgId, '
                 'plantOrgId: plantOrgId, dosageForm: dosageForm, processType: processType, '
                 'targetMarket: targetMarket}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=seiyakuProcessId" target="seiyakuProcessId"/><zeebe:output '
                 'source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Plan" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-patent.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;openPatent.genericManufacturing.plan&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, seiyakuProcessId: '
                 'seiyakuProcessId, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2335,
                 '00-contracts/bpmn/ai/gftd/open-patent/startGenericManufacturingCandidate.bpmn',
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-start-generic-manufacturing-candidate-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-summarizeSeiyakuStartProgress-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.summarizeSeiyakuStartProgress',
                 'open_patent_summarize_seiyaku_start_progress',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-summarizeSeiyakuStartProgress-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-acknowledgeSeiyakuBatchStart-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.acknowledgeSeiyakuBatchStart',
                 'open_patent_acknowledge_seiyaku_batch_start',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-acknowledgeSeiyakuBatchStart-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-queueSeiyakuBatchStart-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.queueSeiyakuBatchStart',
                 'open_patent_queue_seiyaku_batch_start',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-queueSeiyakuBatchStart-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-validateSeiyakuBatchDraft-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.validateSeiyakuBatchDraft',
                 'open_patent_validate_seiyaku_batch_draft',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-validateSeiyakuBatchDraft-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-prepareSeiyakuBatchDraft-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.prepareSeiyakuBatchDraft',
                 'open_patent_prepare_seiyaku_batch_draft',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-prepareSeiyakuBatchDraft-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-handoffGenericCandidateToSeiyaku-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.handoffGenericCandidateToSeiyaku',
                 'open_patent_handoff_generic_candidate_to_seiyaku',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-handoffGenericCandidateToSeiyaku-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-recordDrugRegulatoryBlocker-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.recordDrugRegulatoryBlocker',
                 'open_patent_record_drug_regulatory_blocker',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-recordDrugRegulatoryBlocker-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-runExpiredDrugPatentPipeline-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.runExpiredDrugPatentPipeline',
                 'open_patent_run_expired_drug_patent_pipeline',
                 120000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-runExpiredDrugPatentPipeline-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-collectExpiredDrugPatentBacklog-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.collectExpiredDrugPatentBacklog',
                 'open_patent_collect_expired_drug_patent_backlog',
                 60000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-collectExpiredDrugPatentBacklog-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-screenExpiredDrugPatent-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.screenExpiredDrugPatent',
                 'open_patent_screen_expired_drug_patent',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-screenExpiredDrugPatent-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-startGenericManufacturingCandidate-v1',
                 'did:web:open-patent.gftd.ai',
                 'ai.gftd.apps.openPatent.startGenericManufacturingCandidate',
                 'open_patent_start_generic_manufacturing_candidate',
                 30000,
                 '2026-04-27T07:50:00Z',
                 'did:web:open-patent.gftd.ai',
                 'did:web:open-patent.gftd.ai',
                 'sys.bpmn.seed.open-patent-expired-pharma',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-startGenericManufacturingCandidate-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-summarizeSeiyakuStartProgress-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-acknowledgeSeiyakuBatchStart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-queueSeiyakuBatchStart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-validateSeiyakuBatchDraft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-prepareSeiyakuBatchDraft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-handoffGenericCandidateToSeiyaku-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-recordDrugRegulatoryBlocker-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-runExpiredDrugPatentPipeline-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-collectExpiredDrugPatentBacklog-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-screenExpiredDrugPatent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-patent-startGenericManufacturingCandidate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-summarize-seiyaku-start-progress-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-acknowledge-seiyaku-batch-start-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-queue-seiyaku-batch-start-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-validate-seiyaku-batch-draft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-prepare-seiyaku-batch-draft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-handoff-generic-candidate-to-seiyaku-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-record-drug-regulatory-blocker-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-run-expired-drug-patent-pipeline-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-collect-expired-drug-patent-backlog-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-screen-expired-drug-patent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-patent-start-generic-manufacturing-candidate-v1']},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_generic_candidate', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_seiyaku_progress', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_seiyaku_start_ack', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_seiyaku_start_request', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_seiyaku_batch_validation', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_seiyaku_batch_draft', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_seiyaku_handoff', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_drug_expiry', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_expiry_backlog_run', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_patent_regulatory_blocker', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
