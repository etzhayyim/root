import type { Kysely } from "kysely";
import { sql } from "kysely";

// Connect vertex_mineral → vertex_periodic_element so mineral
// compositions can be traversed from the knowledge graph.
// Also adds the IMA mineral seeder BPMN process def.
//
// edge_mineral_element columns:
//   edge_id         — sha256(:mineral_did::element_sym)[:24]
//   mineral_did     — FK → vertex_mineral.vertex_id
//   element_sym     — 1-3 char symbol (e.g. "Fe", "Si", "O")
//   element_did     — FK → vertex_periodic_element.vertex_id
//   mass_pct        — elemental weight percent in the mineral (nullable)
//   role            — "major" | "minor" | "trace" | "essential"
//   created_at      — ISO8601 timestamp

export async function up(db: Kysely<unknown>): Promise<void> {
  // Edge table: mineral → periodic element
  await sql`
    CREATE TABLE IF NOT EXISTS edge_mineral_element (
      edge_id         VARCHAR PRIMARY KEY,
      mineral_did     VARCHAR NOT NULL,
      element_sym     VARCHAR NOT NULL,
      element_did     VARCHAR,
      mass_pct        FLOAT,
      role            VARCHAR DEFAULT 'major',
      created_at      VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_mineral_element_mineral
      ON edge_mineral_element (mineral_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_mineral_element_sym
      ON edge_mineral_element (element_sym)
  `.execute(db);

  // MV: for each mineral, aggregate its element composition as JSON array
  // so maps can fetch mineral color/composition in a single query.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mineral_element_composition AS
    SELECT
      em.mineral_did,
      COUNT(*)                        AS element_count,
      MIN(em.created_at)              AS first_edge_at
    FROM edge_mineral_element em
    GROUP BY em.mineral_did
  `.execute(db);

  // IMA mineral seeder BPMN — timer-start R/P90D (quarterly refresh).
  // F5 watcher auto-deploys once this row is present.
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml,
      xml_byte_size, source_path, status, created_at,
      sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/science-mineral-seed-v1',
      'did:web:bpmn.gftd.ai',
      'science_mineral_seed',
      1,
      ${IMA_MINERAL_SEED_BPMN},
      ${IMA_MINERAL_SEED_BPMN.length},
      '30-graph/graph-schema/migrations/20260428310000_edge_mineral_element.ts',
      'active',
      NOW()::VARCHAR,
      0,
      'bpmn.gftd.ai',
      'system',
      'did:web:bpmn.gftd.ai'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def
      WHERE bpmn_process_id = 'science_mineral_seed'
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_mineral_element_composition`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_mineral_element`.execute(db);
  await sql`
    DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id = 'science_mineral_seed'
  `.execute(db);
}

// Minimal BPMN 2.0 for IMA mineral seed — timer R/P90D, single service task.
const IMA_MINERAL_SEED_BPMN = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  id="Definitions_mineral_seed"
  targetNamespace="http://bpmn.io/schema/bpmn"
  exporter="Camunda Modeler" exporterVersion="2.0">
  <bpmn:process id="science_mineral_seed" name="Science: IMA Mineral Seed" isExecutable="true">
    <bpmn:startEvent id="Start_Timer" name="Every 90 days">
      <bpmn:outgoing>Flow_to_seed</bpmn:outgoing>
      <bpmn:timerEventDefinition id="TimerDef_1">
        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/P90D</bpmn:timeCycle>
      </bpmn:timerEventDefinition>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_to_seed" sourceRef="Start_Timer" targetRef="Task_SeedMinerals"/>
    <bpmn:serviceTask id="Task_SeedMinerals" name="Seed IMA Minerals">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="science.mineral.seedIma" retries="3"/>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_to_seed</bpmn:incoming>
      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_SeedMinerals" targetRef="End_Done"/>
    <bpmn:endEvent id="End_Done" name="Done">
      <bpmn:incoming>Flow_to_end</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>`;
