import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  project: string;
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  ownerDid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-04-27T07:30:00Z";
const actorTag = "sys.bpmn.seed.extended-infra";

const seeds: Seed[] = [
  {
    project: "open-electricity-market",
    proc: "recordMechanism",
    bpmnProcessId: "open_electricity_market_record_mechanism",
    nsid: "com.etzhayyim.apps.electricityMarket.recordMechanism",
    ownerDid: "did:web:open-electricity-market.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-electricity-market",
    proc: "flagMissingMoney",
    bpmnProcessId: "open_electricity_market_flag_missing_money",
    nsid: "com.etzhayyim.apps.electricityMarket.flagMissingMoney",
    ownerDid: "did:web:open-electricity-market.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-power-grid-interconnect",
    proc: "recordCrossBorderFlow",
    bpmnProcessId: "open_power_grid_interconnect_record_cross_border_flow",
    nsid: "com.etzhayyim.apps.powerGridInterconnect.recordCrossBorderFlow",
    ownerDid: "did:web:open-power-grid-interconnect.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-power-grid-interconnect",
    proc: "flagCurtailment",
    bpmnProcessId: "open_power_grid_interconnect_flag_curtailment",
    nsid: "com.etzhayyim.apps.powerGridInterconnect.flagCurtailment",
    ownerDid: "did:web:open-power-grid-interconnect.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-water-scarcity",
    proc: "recordBasinMetric",
    bpmnProcessId: "open_water_scarcity_record_basin_metric",
    nsid: "com.etzhayyim.apps.waterScarcity.recordBasinMetric",
    ownerDid: "did:web:open-water-scarcity.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-water-scarcity",
    proc: "flagTreatyDispute",
    bpmnProcessId: "open_water_scarcity_flag_treaty_dispute",
    nsid: "com.etzhayyim.apps.waterScarcity.flagTreatyDispute",
    ownerDid: "did:web:open-water-scarcity.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-water-stewardship",
    proc: "recordStewardshipPlan",
    bpmnProcessId: "open_water_stewardship_record_stewardship_plan",
    nsid: "com.etzhayyim.apps.waterStewardship.recordStewardshipPlan",
    ownerDid: "did:web:open-water-stewardship.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-water-stewardship",
    proc: "flagBasinStress",
    bpmnProcessId: "open_water_stewardship_flag_basin_stress",
    nsid: "com.etzhayyim.apps.waterStewardship.flagBasinStress",
    ownerDid: "did:web:open-water-stewardship.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-wastewater-reuse",
    proc: "registerFacility",
    bpmnProcessId: "open_wastewater_reuse_register_facility",
    nsid: "com.etzhayyim.apps.wastewaterReuse.registerFacility",
    ownerDid: "did:web:open-wastewater-reuse.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-wastewater-reuse",
    proc: "recordMonitoringMetric",
    bpmnProcessId: "open_wastewater_reuse_record_monitoring_metric",
    nsid: "com.etzhayyim.apps.wastewaterReuse.recordMonitoringMetric",
    ownerDid: "did:web:open-wastewater-reuse.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-telecom-infra",
    proc: "registerCable",
    bpmnProcessId: "open_telecom_infra_register_cable",
    nsid: "com.etzhayyim.apps.telecomInfra.registerCable",
    ownerDid: "did:web:open-telecom-infra.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-telecom-infra",
    proc: "flagCableFault",
    bpmnProcessId: "open_telecom_infra_flag_cable_fault",
    nsid: "com.etzhayyim.apps.telecomInfra.flagCableFault",
    ownerDid: "did:web:open-telecom-infra.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-rural-broadband",
    proc: "registerDeployment",
    bpmnProcessId: "open_rural_broadband_register_deployment",
    nsid: "com.etzhayyim.apps.ruralBroadband.registerDeployment",
    ownerDid: "did:web:open-rural-broadband.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-rural-broadband",
    proc: "flagDigitalDivideGap",
    bpmnProcessId: "open_rural_broadband_flag_digital_divide_gap",
    nsid: "com.etzhayyim.apps.ruralBroadband.flagDigitalDivideGap",
    ownerDid: "did:web:open-rural-broadband.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-rail-cross-border",
    proc: "recordCorridorFlow",
    bpmnProcessId: "open_rail_cross_border_record_corridor_flow",
    nsid: "com.etzhayyim.apps.railCrossBorder.recordCorridorFlow",
    ownerDid: "did:web:open-rail-cross-border.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-rail-cross-border",
    proc: "flagInteropFailure",
    bpmnProcessId: "open_rail_cross_border_flag_interop_failure",
    nsid: "com.etzhayyim.apps.railCrossBorder.flagInteropFailure",
    ownerDid: "did:web:open-rail-cross-border.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
];

function sourcePath(seed: Seed): string {
  return `00-contracts/bpmn/com/etzhayyim/${seed.project}/${seed.proc}.bpmn`;
}

function processVertexId(seed: Seed): string {
  return `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${seed.project}-${seed.proc}-v1`;
}

function bindingVertexId(seed: Seed): string {
  return `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${seed.project}-${seed.proc}-v1`;
}

async function insertProcessDef(db: Kysely<unknown>, seed: Seed): Promise<void> {
  const relPath = sourcePath(seed);
  const xml = readContract(relPath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId(seed)}, ${seed.ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${xmlByteSize} AS integer), ${relPath}, 'active',
      ${createdAt}, 1, ${seed.ownerDid}, ${seed.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(seed)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId(seed)}, ${seed.ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1,
      CAST(${seed.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${seed.ownerDid}, ${seed.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed)}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) await insertProcessDef(db, seed);
  for (const seed of seeds) await insertBinding(db, seed);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed)}`.execute(db);
  }
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(seed)}`.execute(db);
  }
}
