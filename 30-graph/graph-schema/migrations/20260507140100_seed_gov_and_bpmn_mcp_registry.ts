import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type ProcessSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  sourcePath: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-05-07T14:01:00Z";
const ownerDid = "did:web:and-state.gftd.ai";
const actorHost = "and-state.gftd.ai";
const actorTag = "sys.bpmn.seed.gov-and";
const writeTableAllowlist = [
  "vertex_gov_org",
  "edge_gov_org_site_dependency",
].join(",");

const seeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-seedOrgs-v1",
    nsid: "ai.gftd.govAnd.seedOrgs",
    bpmnProcessId: "gov_and_seed_orgs",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/seedOrgs.bpmn",
    resultTimeoutMs: 90_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-registerDIDs-v1",
    nsid: "ai.gftd.govAnd.registerDIDs",
    bpmnProcessId: "gov_and_register_dids",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/registerDIDs.bpmn",
    resultTimeoutMs: 90_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-followSiteDeps-v1",
    nsid: "ai.gftd.govAnd.followSiteDeps",
    bpmnProcessId: "gov_and_follow_site_deps",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/followSiteDeps.bpmn",
    resultTimeoutMs: 90_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-resolveOrgPath-v1",
    nsid: "ai.gftd.govAnd.resolveOrgPath",
    bpmnProcessId: "gov_and_resolve_org_path",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/resolveOrgPath.bpmn",
    resultTimeoutMs: 60_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-listOrgs-v1",
    nsid: "ai.gftd.govAnd.listOrgs",
    bpmnProcessId: "gov_and_list_orgs",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/listOrgs.bpmn",
    resultTimeoutMs: 60_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-syncWetUpdates-v1",
    nsid: "ai.gftd.govAnd.syncWetUpdates",
    bpmnProcessId: "gov_and_sync_wet_updates",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/syncWetUpdates.bpmn",
    resultTimeoutMs: 180_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-shinka-v1",
    nsid: "ai.gftd.govAnd.shinka",
    bpmnProcessId: "gov_and_shinka",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/shinka.bpmn",
    resultTimeoutMs: 180_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-heartbeatTick-v1",
    nsid: "ai.gftd.govAnd.heartbeatTick",
    bpmnProcessId: "gov_and_heartbeat_tick",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/heartbeatTick.bpmn",
    resultTimeoutMs: 180_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-seed-orgs-v1",
    nsid: "ai.gftd.govAnd.seedOrgs",
    bpmnProcessId: "gov_and_seed_orgs",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/seedOrgs.bpmn",
    resultTimeoutMs: 90_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-register-dids-v1",
    nsid: "ai.gftd.govAnd.registerDIDs",
    bpmnProcessId: "gov_and_register_dids",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/registerDIDs.bpmn",
    resultTimeoutMs: 90_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-follow-site-deps-v1",
    nsid: "ai.gftd.govAnd.followSiteDeps",
    bpmnProcessId: "gov_and_follow_site_deps",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/followSiteDeps.bpmn",
    resultTimeoutMs: 90_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-resolve-org-path-v1",
    nsid: "ai.gftd.govAnd.resolveOrgPath",
    bpmnProcessId: "gov_and_resolve_org_path",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/resolveOrgPath.bpmn",
    resultTimeoutMs: 60_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-list-orgs-v1",
    nsid: "ai.gftd.govAnd.listOrgs",
    bpmnProcessId: "gov_and_list_orgs",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/listOrgs.bpmn",
    resultTimeoutMs: 60_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-sync-wet-updates-v1",
    nsid: "ai.gftd.govAnd.syncWetUpdates",
    bpmnProcessId: "gov_and_sync_wet_updates",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/syncWetUpdates.bpmn",
    resultTimeoutMs: 180_000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gov-and-heartbeat-tick-v1",
    nsid: "ai.gftd.govAnd.heartbeatTick",
    bpmnProcessId: "gov_and_heartbeat_tick",
    sourcePath: "00-contracts/bpmn/ai/gftd/govAnd/heartbeatTick.bpmn",
    resultTimeoutMs: 180_000,
  },
];

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

function lexiconPath(nsid: string): string {
  return `00-contracts/lexicons/${nsid.replaceAll(".", "/") }.json`;
}

function mcpVertexId(nsid: string): string {
  return `at://${ownerDid}/ai.gftd.mcp.toolDef/${nsid.replaceAll(".", "-")}`;
}

function bindingVertexId(nsid: string): string {
  return `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${nsid.replaceAll(".", "-")}-v1`;
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${(value as unknown[]).map((item) => stableStringify(item)).join(",")}]`;
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`)
    .join(",")}}`;
}

function readLexiconTool(seed: ProcessSeed): {
  lexiconType: string;
  description: string;
  inputSchema: string;
  outputSchema: string;
  schemaHash: string;
  sourcePath: string;
} {
  const sourcePath = lexiconPath(seed.nsid);
  const raw = readContract(sourcePath);
  const doc = JSON.parse(raw) as {
    defs?: {
      main?: {
        type?: string;
        description?: string;
        parameters?: unknown;
        input?: { schema?: unknown };
        output?: { schema?: unknown };
      };
    };
  };
  const main = doc.defs?.main ?? {};
  const lexiconType = main.type ?? "procedure";
  const input = lexiconType === "query" ? main.parameters ?? {} : main.input?.schema ?? {};
  const output = main.output?.schema ?? {};
  const description = main.description ?? "";
  const inputSchema = stableStringify(input);
  const outputSchema = stableStringify(output);
  const schemaHash = createHash("sha256")
    .update(`${description}\0${inputSchema}\0${outputSchema}`)
    .digest("hex")
    .slice(0, 16);
  return { lexiconType, description, inputSchema, outputSchema, schemaHash, sourcePath };
}

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${seed.vertexId}, ${ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${xmlByteSize} AS integer), ${seed.sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const vertexId = bindingVertexId(seed.nsid);
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,
      actor_id, write_table_allowlist
    )
    SELECT
      ${vertexId}, ${ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1,
      CAST(${seed.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1,
      ${ownerDid}, ${ownerDid}, ${actorTag}, ${writeTableAllowlist}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${vertexId}
    )
  `.execute(db);
}

async function insertMcpToolDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const tool = readLexiconTool(seed);
  const vertexId = mcpVertexId(seed.nsid);
  await sql`
    INSERT INTO vertex_mcp_tool_def (
      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,
      input_schema, output_schema, lxm_scope, visibility, version, enabled,
      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,
      actor_id, created_at
    )
    SELECT
      ${vertexId}, ${seed.nsid}, ${ownerDid}, ${actorHost}, ${tool.lexiconType},
      ${tool.description}, ${tool.inputSchema}, ${tool.outputSchema}, ${seed.nsid},
      'public', 1, TRUE, ${tool.sourcePath}, ${tool.schemaHash}, ${ownerDid}, 1,
      ${ownerDid}, ${ownerDid}, ${actorTag}, ${createdAt}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = ${vertexId}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) await insertProcessDef(db, seed);
  for (const seed of seeds) await insertBinding(db, seed);
  for (const seed of seeds) await insertMcpToolDef(db, seed);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_mcp_tool_def WHERE vertex_id = ${mcpVertexId(seed.nsid)}`.execute(db);
  }
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed.nsid)}`.execute(db);
  }
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
}
