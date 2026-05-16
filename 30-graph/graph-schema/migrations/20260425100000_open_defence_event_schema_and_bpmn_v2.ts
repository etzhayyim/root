import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-04-25T10:00:00Z";
const actorTag = "sys.bpmn.seed.open-defence";

type Entry = { project: string; bpmnProcessId: string; proc: string };

const entries: Entry[] = [
  { project: "open-airplane", bpmnProcessId: "open_airplane_flag_airspace_violation", proc: "flagAirspaceViolation" },
  { project: "open-airplane", bpmnProcessId: "open_airplane_notify_no_fly_zone",     proc: "notifyNoFlyZone" },
  { project: "open-ports",    bpmnProcessId: "open_ports_screen_vessel_sanctions",   proc: "screenVesselSanctions" },
  { project: "open-ports",    bpmnProcessId: "open_ports_flag_dark_fleet",           proc: "flagDarkFleet" },
  { project: "open-rail",     bpmnProcessId: "open_rail_flag_critical_asset_incident", proc: "flagCriticalAssetIncident" },
  { project: "open-network",  bpmnProcessId: "open_network_report_cyber_incident",   proc: "reportCyberIncident" },
  { project: "open-network",  bpmnProcessId: "open_network_escalate_ddos",           proc: "escalateDdos" },
  { project: "open-power",    bpmnProcessId: "open_power_report_grid_attack",        proc: "reportGridAttack" },
  { project: "open-gas",      bpmnProcessId: "open_gas_report_pipeline_sabotage",    proc: "reportPipelineSabotage" },
  { project: "open-water",    bpmnProcessId: "open_water_report_infra_sabotage",     proc: "reportInfraSabotage" },
  { project: "open-swift",    bpmnProcessId: "open_swift_screen_sanctions",          proc: "screenSanctions" },
  { project: "open-banking",  bpmnProcessId: "open_banking_flag_suspicious_transaction", proc: "flagSuspiciousTransaction" },
  { project: "open-jpn-gov",  bpmnProcessId: "open_jpn_gov_resolve_boei_sho_procurement", proc: "resolveBoeiShoProcurement" },
  { project: "open-jpn-gov",  bpmnProcessId: "open_jpn_gov_check_tokutei_himitsu",   proc: "checkTokuteiHimitsu" },
  { project: "open-cofog",    bpmnProcessId: "open_cofog_classify_defence_function", proc: "classifyDefenceFunction" },
  { project: "open-isic",     bpmnProcessId: "open_isic_flag_dual_use_industry",     proc: "flagDualUseIndustry" },
  { project: "open-seiyaku",  bpmnProcessId: "open_seiyaku_screen_export_control",   proc: "screenExportControl" },
  { project: "open-unispsc",  bpmnProcessId: "open_unispsc_flag_dual_use_commodity", proc: "flagDualUseCommodity" },
];

const kebabToSlug = (kebab: string, proc: string): string =>
  `${kebab}-${proc.replace(/([A-Z])/g, "-$1").toLowerCase()}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  // 1. Defence event landing table — single shared sink for all 18 processes.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_defence_event (
      vertex_id        varchar PRIMARY KEY,
      owner_did        varchar NOT NULL,
      bpmn_process_id  varchar NOT NULL,
      nsid             varchar NOT NULL,
      project          varchar NOT NULL,
      subject_vid      varchar,
      action_class     varchar NOT NULL,
      severity         varchar NOT NULL,
      detected_at      varchar,
      created_at       varchar NOT NULL,
      sensitivity_ord  integer NOT NULL,
      org_id           varchar NOT NULL,
      user_id          varchar NOT NULL,
      actor_id         varchar NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_project_class_at ON vertex_open_defence_event (project, action_class, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_subject ON vertex_open_defence_event (subject_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_defence_event_severity_at ON vertex_open_defence_event (severity, created_at)`.execute(db);

  // 2. Refresh process_def rows in place (delete-then-insert per RW write semantics)
  //    Reading regenerated XML from disk; bumps version to 2, clears deployed_at so F5 redeploys.
  for (const e of entries) {
    const vertexId = `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${kebabToSlug(e.project, e.proc)}`;
    const sourcePath = `00-contracts/bpmn/ai/gftd/${e.project}/${e.proc}.bpmn`;
    const xml = readContract(sourcePath);
    const size = Buffer.byteLength(xml, "utf8");
    const ownerDid = `did:web:${e.project}.gftd.ai:ops`;

    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${vertexId}`.execute(db);
    await sql`
      INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      VALUES (${vertexId}, ${ownerDid}, ${e.bpmnProcessId}, 2, ${xml}, CAST(${size} AS integer), ${sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_defence_event`.execute(db);
}
