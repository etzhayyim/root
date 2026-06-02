import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// M1 (ADR-0056 + ADR-2604251801 §4-A): retire CF Worker triggers.crons for 8
// Google Workspace apps. Each wrangler.jsonc had `triggers.crons: */15 or */30`;
// this migration registers per-app timer-start BPMN definitions in the
// vertex_bpmn_process_def + vertex_bpmn_lexicon_binding tables, which the F5
// watcher (`bpmn-dispatcher`) deploys to Zeebe. The dispatcher then invokes
// each app's `cronTick` XRPC endpoint on the configured cadence (R/PT15M for
// gmail/calendar, R/PT30M for the other six).

type ProcessSeed = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
  ownerDid: string;
};

type BindingSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  ownerDid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const createdAt = "2026-04-27T18:00:00Z";

const APPS: ReadonlyArray<{ app: string; cadence: "R/PT15M" | "R/PT30M" }> = [
  { app: "gmail",    cadence: "R/PT15M" },
  { app: "calendar", cadence: "R/PT15M" },
  { app: "contacts", cadence: "R/PT30M" },
  { app: "meet",     cadence: "R/PT30M" },
  { app: "sheets",   cadence: "R/PT30M" },
  { app: "slides",   cadence: "R/PT30M" },
  { app: "tasks",    cadence: "R/PT30M" },
  { app: "docs",     cadence: "R/PT30M" },
  { app: "drive",    cadence: "R/PT30M" },
];

const processSeeds: ProcessSeed[] = APPS.map(({ app }) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${app}-cron-tick-v1`,
  bpmnProcessId: `${app}_cron_tick`,
  sourcePath: `00-contracts/bpmn/com/etzhayyim/${app}/cronTick.bpmn`,
  ownerDid: `did:web:${app}.etzhayyim.com`,
}));

const bindingSeeds: BindingSeed[] = APPS.map(({ app }) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${app}-cronTick-v1`,
  nsid: `com.etzhayyim.apps.${app}.cronTick`,
  bpmnProcessId: `${app}_cron_tick`,
  ownerDid: `did:web:${app}.etzhayyim.com`,
  resultTimeoutMs: 60_000,
}));

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id,
      owner_did,
      bpmn_process_id,
      version,
      xml,
      xml_byte_size,
      source_path,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${seed.vertexId},
      ${seed.ownerDid},
      ${seed.bpmnProcessId},
      1,
      ${xml},
      CAST(${xmlByteSize} AS integer),
      ${seed.sourcePath},
      'active',
      ${createdAt},
      1,
      ${seed.ownerDid},
      ${seed.ownerDid},
      'sys.bpmn.seed.gworkspace_cron'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: BindingSeed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id,
      owner_did,
      nsid,
      bpmn_process_id,
      bpmn_version,
      result_timeout_ms,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${seed.vertexId},
      ${seed.ownerDid},
      ${seed.nsid},
      ${seed.bpmnProcessId},
      1,
      CAST(${seed.resultTimeoutMs} AS integer),
      'active',
      ${createdAt},
      1,
      ${seed.ownerDid},
      ${seed.ownerDid},
      'sys.bpmn.seed.gworkspace_cron'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const seed of processSeeds) {
    await insertProcessDef(db, seed);
  }
  for (const seed of bindingSeeds) {
    await insertBinding(db, seed);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of bindingSeeds) {
    await sql`
      DELETE FROM vertex_bpmn_lexicon_binding
      WHERE vertex_id = ${seed.vertexId}
    `.execute(db);
  }
  for (const seed of processSeeds) {
    await sql`
      DELETE FROM vertex_bpmn_process_def
      WHERE vertex_id = ${seed.vertexId}
    `.execute(db);
  }
}
