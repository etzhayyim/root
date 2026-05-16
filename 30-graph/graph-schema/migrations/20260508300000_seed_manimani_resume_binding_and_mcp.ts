import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-2605080800 Phase 4 — bpmn-dispatcher binding for `resumeRun`
 * + MCP tool registry seed for all 7 manimani lexicons (the original
 * 6 from Phase 1 + resumeRun added in Phase 4).
 *
 * Why a single migration? The resumeRun binding mirrors the 6 rows from
 * 20260508290000_seed_manimani_xrpc_bindings and the MCP registry seed
 * follows the canonical pattern documented in
 * 20260507141300_seed_gov_bol_bpmn_mcp_registry — both touch the
 * `vertex_bpmn_lexicon_binding` and `vertex_mcp_tool_def` tables, so
 * one rev folds in cleanly.
 *
 * MCP exposure: rows in `vertex_mcp_tool_def` are read at runtime by
 * the canonical `mcp.gftd.ai/xrpc/ai.gftd.mcp.message` `tools/list`
 * handler (ADR-0087 + ADR-2604261000) — no per-actor deploy needed.
 * Auth path: `tools/call` requires AT Protocol session JWT or ES256
 * Service Auth with `lxm` claim equal to the NSID.
 *
 * Idempotency: relies on RisingWave's implicit PK upsert (re-insert
 * with the same vertex_id overwrites). No `ON CONFLICT DO NOTHING`
 * (ADR-2604241342 §rw-no-onconflict).
 */

type LexiconSeed = {
  nsid: string;
  bpmnProcessId: string;
  sourcePath: string;
  // Optional binding override — when null this lexicon is NOT routed
  // by bpmn-dispatcher (e.g., already bound by the prior migration).
  bindingTimeoutMs: number | null;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const createdAt = "2026-05-08T15:30:00Z";
const ownerDid = "did:web:manimani.gftd.ai";
const actorHost = "manimani.gftd.ai";
const actorTag = "sys.manimani.seed.p4";
const langgraphUrl = "http://manimani-langgraph.mitama-udf.svc.cluster.local:8000";

const seeds: LexiconSeed[] = [
  // Phase 1 surface — already bound in 20260508290000; we only seed MCP
  // rows here. bindingTimeoutMs=null skips the binding INSERT.
  { nsid: "ai.gftd.apps.manimani.ingest",        bpmnProcessId: "manimani_ingest",        sourcePath: "00-contracts/lexicons/ai/gftd/apps/manimani/ingest.json",        bindingTimeoutMs: null },
  { nsid: "ai.gftd.apps.manimani.classify",      bpmnProcessId: "manimani_classify",      sourcePath: "00-contracts/lexicons/ai/gftd/apps/manimani/classify.json",      bindingTimeoutMs: null },
  { nsid: "ai.gftd.apps.manimani.process",       bpmnProcessId: "manimani_process",       sourcePath: "00-contracts/lexicons/ai/gftd/apps/manimani/process.json",       bindingTimeoutMs: null },
  { nsid: "ai.gftd.apps.manimani.getProject",    bpmnProcessId: "manimani_get_project",   sourcePath: "00-contracts/lexicons/ai/gftd/apps/manimani/getProject.json",    bindingTimeoutMs: null },
  { nsid: "ai.gftd.apps.manimani.listProjects",  bpmnProcessId: "manimani_list_projects", sourcePath: "00-contracts/lexicons/ai/gftd/apps/manimani/listProjects.json",  bindingTimeoutMs: null },
  { nsid: "ai.gftd.apps.manimani.coverage",      bpmnProcessId: "manimani_coverage",      sourcePath: "00-contracts/lexicons/ai/gftd/apps/manimani/coverage.json",      bindingTimeoutMs: null },
  // Phase 4 — resumeRun (new). Bind the dispatcher row and add MCP entry.
  { nsid: "ai.gftd.apps.manimani.resumeRun",     bpmnProcessId: "manimani_resume_run",    sourcePath: "00-contracts/lexicons/ai/gftd/apps/manimani/resumeRun.json",     bindingTimeoutMs: 10_000 },
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

async function insertResumeBinding(db: Kysely<unknown>, seed: LexiconSeed): Promise<void> {
  if (seed.bindingTimeoutMs === null) return;
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
  for (const seed of seeds) await insertResumeBinding(db, seed);
  for (const seed of seeds) await insertMcpToolDef(db, seed);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_mcp_tool_def WHERE vertex_id = ${mcpVertexId(seed.nsid)}`.execute(db);
  }
  for (const seed of seeds) {
    if (seed.bindingTimeoutMs === null) continue;
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed.nsid)}`.execute(db);
  }
}
