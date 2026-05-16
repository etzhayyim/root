import type { Kysely } from "kysely";
import { sql } from "kysely";

// BPMN process definitions for Phase 2 science knowledge graph workers.
//
// Three new timer-start processes:
//   science_compound_seed  R/P30D  — PubChem compound batch (rotating CID range)
//   science_crystal_seed   R/P30D  — COD crystal structure seed for known minerals
//   science_protein_seed   R/P7D   — UniProt Swiss-Prot batch (weekly refresh)
//
// Also seeds science.paper.linkGraphPhase2 BPMN (compound + protein NER from papers).

const COMPOUND_SEED_BPMN = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  id="Definitions_compound_seed"
  targetNamespace="http://bpmn.io/schema/bpmn"
  exporter="Camunda Modeler" exporterVersion="2.0">
  <bpmn:process id="science_compound_seed" name="Science: PubChem Compound Seed" isExecutable="true">
    <bpmn:startEvent id="Start_Timer" name="Every 30 days">
      <bpmn:outgoing>Flow_to_seed</bpmn:outgoing>
      <bpmn:timerEventDefinition id="TimerDef_1">
        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/P30D</bpmn:timeCycle>
      </bpmn:timerEventDefinition>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_to_seed" sourceRef="Start_Timer" targetRef="Task_SeedCompounds"/>
    <bpmn:serviceTask id="Task_SeedCompounds" name="Seed PubChem Compounds">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="science.compound.seedPubchem" retries="3"/>
        <zeebe:ioMapping>
          <zeebe:input source="=200" target="batch_size"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_to_seed</bpmn:incoming>
      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_SeedCompounds" targetRef="End_Done"/>
    <bpmn:endEvent id="End_Done" name="Done">
      <bpmn:incoming>Flow_to_end</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>`;

const CRYSTAL_SEED_BPMN = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  id="Definitions_crystal_seed"
  targetNamespace="http://bpmn.io/schema/bpmn"
  exporter="Camunda Modeler" exporterVersion="2.0">
  <bpmn:process id="science_crystal_seed" name="Science: Crystal Structure Seed" isExecutable="true">
    <bpmn:startEvent id="Start_Timer" name="Every 30 days">
      <bpmn:outgoing>Flow_to_seed</bpmn:outgoing>
      <bpmn:timerEventDefinition id="TimerDef_1">
        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/P30D</bpmn:timeCycle>
      </bpmn:timerEventDefinition>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_to_seed" sourceRef="Start_Timer" targetRef="Task_SeedCrystal"/>
    <bpmn:serviceTask id="Task_SeedCrystal" name="Seed COD Crystal Structures">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="science.crystal.seedStructures" retries="3"/>
        <zeebe:ioMapping>
          <zeebe:input source="=50" target="batch_size"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_to_seed</bpmn:incoming>
      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_SeedCrystal" targetRef="End_Done"/>
    <bpmn:endEvent id="End_Done" name="Done">
      <bpmn:incoming>Flow_to_end</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>`;

const PROTEIN_SEED_BPMN = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  id="Definitions_protein_seed"
  targetNamespace="http://bpmn.io/schema/bpmn"
  exporter="Camunda Modeler" exporterVersion="2.0">
  <bpmn:process id="science_protein_seed" name="Science: UniProt Protein Seed" isExecutable="true">
    <bpmn:startEvent id="Start_Timer" name="Every 7 days">
      <bpmn:outgoing>Flow_to_seed</bpmn:outgoing>
      <bpmn:timerEventDefinition id="TimerDef_1">
        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>
      </bpmn:timerEventDefinition>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_to_seed" sourceRef="Start_Timer" targetRef="Task_SeedProtein"/>
    <bpmn:serviceTask id="Task_SeedProtein" name="Seed UniProt Proteins">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="science.protein.seedUniprot" retries="3"/>
        <zeebe:ioMapping>
          <zeebe:input source="=100" target="batch_size"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_to_seed</bpmn:incoming>
      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_SeedProtein" targetRef="End_Done"/>
    <bpmn:endEvent id="End_Done" name="Done">
      <bpmn:incoming>Flow_to_end</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>`;

const LINK_GRAPH_P2_BPMN = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  id="Definitions_link_graph_p2"
  targetNamespace="http://bpmn.io/schema/bpmn"
  exporter="Camunda Modeler" exporterVersion="2.0">
  <bpmn:process id="science_link_graph_phase2" name="Science: KG Link Phase2 (Compound+Protein)" isExecutable="true">
    <bpmn:startEvent id="Start_Timer" name="Every 2 hours">
      <bpmn:outgoing>Flow_to_link</bpmn:outgoing>
      <bpmn:timerEventDefinition id="TimerDef_1">
        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/PT2H</bpmn:timeCycle>
      </bpmn:timerEventDefinition>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_to_link" sourceRef="Start_Timer" targetRef="Task_LinkP2"/>
    <bpmn:serviceTask id="Task_LinkP2" name="Link Compound+Protein NER">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="science.paper.linkGraphPhase2" retries="2"/>
        <zeebe:ioMapping>
          <zeebe:input source="=&quot;chemistry&quot;" target="domain"/>
          <zeebe:input source="=2" target="max_replan"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_to_link</bpmn:incoming>
      <bpmn:outgoing>Flow_to_end</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_to_end" sourceRef="Task_LinkP2" targetRef="End_Done"/>
    <bpmn:endEvent id="End_Done" name="Done">
      <bpmn:incoming>Flow_to_end</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>`;

export async function up(db: Kysely<unknown>): Promise<void> {
  const processes = [
    {
      id: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/science-compound-seed-v1",
      bpmn_process_id: "science_compound_seed",
      xml: COMPOUND_SEED_BPMN,
      source_path: "30-graph/graph-schema/migrations/20260429110000_seed_compound_crystal_protein_bpmn.ts",
    },
    {
      id: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/science-crystal-seed-v1",
      bpmn_process_id: "science_crystal_seed",
      xml: CRYSTAL_SEED_BPMN,
      source_path: "30-graph/graph-schema/migrations/20260429110000_seed_compound_crystal_protein_bpmn.ts",
    },
    {
      id: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/science-protein-seed-v1",
      bpmn_process_id: "science_protein_seed",
      xml: PROTEIN_SEED_BPMN,
      source_path: "30-graph/graph-schema/migrations/20260429110000_seed_compound_crystal_protein_bpmn.ts",
    },
    {
      id: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/science-link-graph-phase2-v1",
      bpmn_process_id: "science_link_graph_phase2",
      xml: LINK_GRAPH_P2_BPMN,
      source_path: "30-graph/graph-schema/migrations/20260429110000_seed_compound_crystal_protein_bpmn.ts",
    },
  ];

  for (const p of processes) {
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml,
        xml_byte_size, source_path, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT
        ${p.id},
        'did:web:bpmn.gftd.ai',
        ${p.bpmn_process_id},
        1,
        ${p.xml},
        ${p.xml.length},
        ${p.source_path},
        'active',
        NOW()::VARCHAR,
        0,
        'bpmn.gftd.ai',
        'system',
        'did:web:bpmn.gftd.ai'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def
        WHERE bpmn_process_id = ${p.bpmn_process_id}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const id of [
    "science_compound_seed",
    "science_crystal_seed",
    "science_protein_seed",
    "science_link_graph_phase2",
  ]) {
    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id = ${id}
    `.execute(db);
  }
}
