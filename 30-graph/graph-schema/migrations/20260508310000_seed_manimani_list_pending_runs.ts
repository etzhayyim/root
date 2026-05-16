import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-2605080800 Phase 7 — bpmn-dispatcher binding for `listPendingRuns`
 * + MCP tool registry seed for the same lexicon. Mirrors the Phase 4
 * seed migration exactly (one new procedure / query → one binding row +
 * one MCP row).
 *
 * Why a separate file? Migrations are append-only by repo convention.
 * 20260508300000 was already applied (resumeRun + 6 prior MCP rows);
 * this file adds the 7th MCP row + the routing entry without
 * reapplying the prior INSERTs.
 *
 * Idempotency: relies on RisingWave's implicit PK upsert (re-insert
 * with the same vertex_id overwrites). No `ON CONFLICT DO NOTHING`
 * (ADR-2604241342 §rw-no-onconflict).
 */

type LexiconSeed = {
  nsid: string;
  bpmnProcessId: string;
  sourcePath: string;
  bindingTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const createdAt = "2026-05-08T16:30:00Z";
const ownerDid = "did:web:manimani.gftd.ai";
const actorHost = "manimani.gftd.ai";
const actorTag = "sys.manimani.seed.p7";
const langgraphUrl = "http://manimani-langgraph.mitama-udf.svc.cluster.local:8000";

const seeds: LexiconSeed[] = [
  {
    nsid: "ai.gftd.apps.manimani.listPendingRuns",
    bpmnProcessId: "manimani_list_pending_runs",
    sourcePath: "00-contracts/lexicons/ai/gftd/apps/manimani/listPendingRuns.json",
    bindingTimeoutMs: 5_000,
  },
];

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

function mcpVertexId(nsid: string): string {
  return `at://${ownerDid}/ai.gftd.mcp.toolDef/${nsid.replaceAll(".", "-")}`;
}

function bindingVertexId(nsid: string): string {
  return `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${nsid}`;
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

function readLexiconTool(seed: LexiconSeed): {
  lexiconType: string;
  description: string;
  inputSchema: string;
  outputSchema: string;
  schemaHash: string;
} {
  const raw = readContract(seed.sourcePath);
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
  return { lexiconType, description, inputSchema, outputSchema, schemaHash };
}

async function insertBinding(db: Kysely<unknown>, seed: LexiconSeed): Promise<void> {
  const vid = bindingVertexId(seed.nsid);
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, sensitivity_ord, owner_did,
      nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
      status, routing_target, langgraph_url, created_at)
    SELECT
      ${vid}, 1, ${ownerDid},
      ${seed.nsid}, ${seed.bpmnProcessId}, 1, CAST(${seed.bindingTimeoutMs} AS integer),
      'active', 'langgraph', ${langgraphUrl}, ${createdAt}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${vid})
  `.execute(db);
}

async function insertMcpToolDef(db: Kysely<unknown>, seed: LexiconSeed): Promise<void> {
  const tool = readLexiconTool(seed);
  const vid = mcpVertexId(seed.nsid);
  await sql`
    INSERT INTO vertex_mcp_tool_def (
      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,
      input_schema, output_schema, lxm_scope, visibility, version, enabled,
      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,
      actor_id, created_at)
    SELECT
      ${vid}, ${seed.nsid}, ${ownerDid}, ${actorHost}, ${tool.lexiconType},
      ${tool.description}, ${tool.inputSchema}, ${tool.outputSchema}, ${seed.nsid},
      'public', 1, TRUE, ${seed.sourcePath}, ${tool.schemaHash}, ${ownerDid}, 1,
      ${ownerDid}, ${ownerDid}, ${actorTag}, ${createdAt}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = ${vid})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
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
}
