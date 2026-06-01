import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:copyright.etzhayyim.com";
const actorHost = "copyright.etzhayyim.com";
const actorId = "sys.mcp.seed.copyright";
const createdAt = "2026-04-30T15:00:00+09:00";

const nsids = [
  "app.etzhayyim.apps.copyright.resolve",
  "app.etzhayyim.apps.copyright.list",
  "app.etzhayyim.apps.copyright.coverage",
  "app.etzhayyim.apps.copyright.ingestCrossref",
  "app.etzhayyim.apps.copyright.ingestDatacite",
  "app.etzhayyim.apps.copyright.socialCoverageReport",
  "app.etzhayyim.apps.copyright.chat",
];

function lexiconPath(nsid: string): string {
  const parts = nsid.split(".");
  const action = parts[parts.length - 1];
  return `00-contracts/lexicons/ai/gftd/apps/copyright/${action}.json`;
}

function mcpVertexId(nsid: string): string {
  return `at://did:web:copyright.etzhayyim.com/app.etzhayyim.mcp.toolDef/${nsid.replaceAll(".", "-")}`;
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

function readLexiconTool(nsid: string): {
  lexiconType: string;
  description: string;
  inputSchema: string;
  outputSchema: string;
  schemaHash: string;
} {
  const filePath = path.resolve(repoRoot, lexiconPath(nsid));
  const raw = readFileSync(filePath, "utf8");
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
  const input = lexiconType === "query" ? main.parameters ?? {} : (main.input as Record<string, unknown>)?.schema ?? {};
  const output = (main.output as Record<string, unknown>)?.schema ?? {};
  const description = main.description ?? "";
  const inputSchema = stableStringify(input);
  const outputSchema = stableStringify(output);
  const schemaHash = createHash("sha256")
    .update(`${description}\0${inputSchema}\0${outputSchema}`)
    .digest("hex")
    .slice(0, 16);
  return { lexiconType, description, inputSchema, outputSchema, schemaHash };
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const nsid of nsids) {
    const tool = readLexiconTool(nsid);
    const vertexId = mcpVertexId(nsid);
    await sql`
      INSERT INTO vertex_mcp_tool_def (
        vertex_id, nsid, actor_did, actor_host, lexicon_type, description,
        input_schema, output_schema, lxm_scope, visibility, version, enabled,
        source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,
        actor_id, created_at
      )
      SELECT
        ${vertexId}, ${nsid}, ${ownerDid}, ${actorHost}, ${tool.lexiconType},
        ${tool.description}, ${tool.inputSchema}, ${tool.outputSchema}, ${nsid},
        'public', 1, TRUE, ${lexiconPath(nsid)}, ${tool.schemaHash},
        ${ownerDid}, 100, ${ownerDid}, ${ownerDid}, ${actorId}, ${createdAt}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = ${vertexId}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const nsid of nsids) {
    await sql`DELETE FROM vertex_mcp_tool_def WHERE vertex_id = ${mcpVertexId(nsid)}`.execute(db);
  }
}
