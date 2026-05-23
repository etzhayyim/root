// mcp.ts — `/mcp` Streamable HTTP facade (ADR-2605080000 §D20 + ADR-2605091400).
//
// Cell-membrane: this is the SOLE external surface for AI agents / external
// principals that have not been onboarded via XRPC + atproto OAuth. Cypher /
// Bolt / SPARQL / PostgREST / GraphQL are ecosystem-tool compatibility envelopes;
// MCP is the canonical AI-facing API.
//
// Wire: JSON-RPC 2.0 over POST /mcp. SSE streaming is reserved for tools/call
// long-runners (P4e); MVP returns a single JSON response.
//
// Auth gates:
//   - public (no auth):     initialize, ping, tools/list, resources/list,
//                           prompts/list, notifications/initialized
//   - authenticated:        tools/call, resources/read, prompts/get
//                           (Bearer sk_live_yata_* OR ES256 atproto session JWT)
//
// Tool surface is auto-derived from `surfaceMap` below + the existing yata
// XRPC NSIDs. Each tool declaration lists the underlying XRPC NSID it
// dispatches to. tools/call → dispatchYataXrpc → bpmn-dispatcher LangServer.

import type { DispatcherCallerContext } from "./dispatcher";
import { dispatchYataXrpc } from "./dispatcher";

export interface McpEnv {
  YATA_VERSION?: string;
  YATA_ACTOR_DID?: string;
  BPMN_DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string;
}

export interface McpAuthResolver {
  (req: Request): Promise<DispatcherCallerContext | null>;
}

interface JsonRpcRequest {
  jsonrpc?: string;
  id?: number | string | null;
  method?: string;
  params?: Record<string, unknown>;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: number | string | null;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

const PROTOCOL_VERSION = "2025-06-18";

// Tool registry. Adding a tool here is the only place that needs editing
// when a new yata XRPC NSID becomes externally visible. Keep in sync with
// 00-contracts/lexicons/ai/gftd/apps/yata/*.json.
interface ToolDef {
  name: string;
  description: string;
  nsid: string;
  inputSchema: Record<string, unknown>;
  authRequired: boolean;
}

const TOOLS: ToolDef[] = [
  {
    name: "yata.graph.sparql",
    description:
      "Execute a SPARQL 1.1 SELECT/CONSTRUCT/ASK query against the caller's tenant graph. Translated via v_rdf_triple to RisingWave SQL.",
    nsid: "ai.gftd.apps.yata.runSparql",
    inputSchema: {
      type: "object",
      required: ["query"],
      properties: {
        query: { type: "string" },
        format: { type: "string", enum: ["json", "csv", "tsv"], default: "json" },
        limit: { type: "integer", minimum: 1, maximum: 100000, default: 1000 },
        timeoutMs: { type: "integer", minimum: 100, maximum: 30000, default: 25000 },
      },
    },
    authRequired: true,
  },
  {
    name: "yata.graph.cypher",
    description:
      "Execute a READ-only openCypher query (MATCH/WITH/RETURN/WHERE/ORDER BY/LIMIT/SKIP/UNION). WRITE clauses are rejected in P4a.",
    nsid: "ai.gftd.apps.yata.runCypher",
    inputSchema: {
      type: "object",
      required: ["statement"],
      properties: {
        statement: { type: "string" },
        parametersJson: { type: "string" },
        format: { type: "string", enum: ["row", "graph", "rest"], default: "row" },
        limit: { type: "integer", minimum: 1, maximum: 100000, default: 1000 },
        timeoutMs: { type: "integer", minimum: 100, maximum: 30000, default: 25000 },
      },
    },
    authRequired: true,
  },
  {
    name: "yata.storage.list_buckets",
    description: "List buckets owned by the caller's org.",
    nsid: "ai.gftd.apps.yata.listBuckets",
    inputSchema: { type: "object", properties: {} },
    authRequired: true,
  },
  {
    name: "yata.storage.list_objects",
    description: "List blob objects within a bucket. Pagination via cursor + limit.",
    nsid: "ai.gftd.apps.yata.listObjects",
    inputSchema: {
      type: "object",
      required: ["bucket"],
      properties: {
        bucket: { type: "string" },
        prefix: { type: "string", default: "" },
        limit: { type: "integer", minimum: 1, maximum: 1000, default: 100 },
        cursor: { type: "string" },
      },
    },
    authRequired: true,
  },
  {
    name: "yata.storage.head_object",
    description: "HEAD a blob (size / etag / content-type / last-modified).",
    nsid: "ai.gftd.apps.yata.headObject",
    inputSchema: {
      type: "object",
      required: ["bucket", "key"],
      properties: { bucket: { type: "string" }, key: { type: "string" } },
    },
    authRequired: true,
  },
  {
    name: "yata.storage.presign",
    description: "Mint a presigned URL for time-limited blob GET / PUT.",
    nsid: "ai.gftd.apps.yata.presignUrl",
    inputSchema: {
      type: "object",
      required: ["bucket", "key", "verb"],
      properties: {
        bucket: { type: "string" },
        key: { type: "string" },
        verb: { type: "string", enum: ["GET", "PUT"] },
        expiresInSec: { type: "integer", minimum: 60, maximum: 86400, default: 3600 },
      },
    },
    authRequired: true,
  },
  {
    name: "yata.storage.delete_object",
    description: "Delete a blob from a bucket. Hard delete (no soft-delete in RW).",
    nsid: "ai.gftd.apps.yata.deleteObject",
    inputSchema: {
      type: "object",
      required: ["bucket", "key"],
      properties: { bucket: { type: "string" }, key: { type: "string" } },
    },
    authRequired: true,
  },
  {
    name: "yata.coverage.report",
    description: "Return tenant usage coverage for the active billing window.",
    nsid: "ai.gftd.apps.yata.coverage",
    inputSchema: { type: "object", properties: {} },
    authRequired: true,
  },
];

// Resources are read-only structured documents the client can pull. We expose
// the Lexicon registry + the well-known agent / mcp metadata as MCP resources
// so the client can introspect without hard-coding URLs.
interface ResourceDef {
  uri: string;
  name: string;
  description: string;
  mimeType: string;
}

const RESOURCES: ResourceDef[] = [
  {
    uri: "yatabase://meta/agent",
    name: "agent.json",
    description: "Yatabase agent card (a2a compatible).",
    mimeType: "application/json",
  },
  {
    uri: "yatabase://meta/mcp",
    name: "mcp.json",
    description: "Yatabase MCP server metadata.",
    mimeType: "application/json",
  },
  {
    uri: "yatabase://meta/surfaces",
    name: "surfaces.json",
    description: "All public yatabase surfaces with auth + billing metadata.",
    mimeType: "application/json",
  },
];

const PUBLIC_METHODS = new Set([
  "initialize",
  "ping",
  "tools/list",
  "resources/list",
  "prompts/list",
  "notifications/initialized",
]);

function jsonRpcResult(id: number | string | null, result: unknown): JsonRpcResponse {
  return { jsonrpc: "2.0", id: id ?? null, result };
}

function jsonRpcError(id: number | string | null, code: number, message: string, data?: unknown): JsonRpcResponse {
  return { jsonrpc: "2.0", id: id ?? null, error: { code, message, ...(data !== undefined ? { data } : {}) } };
}

function jsonResponse(body: JsonRpcResponse, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      "x-yatabase-surface": "mcp",
      "x-yatabase-protocol-version": PROTOCOL_VERSION,
    },
  });
}

function badRequestPlain(): Response {
  return new Response(
    JSON.stringify(jsonRpcError(null, -32700, "Parse error: request body must be JSON-RPC 2.0")),
    { status: 400, headers: { "content-type": "application/json" } },
  );
}

export async function handleMcpRequest(
  req: Request,
  env: McpEnv,
  resolveAuth: McpAuthResolver,
): Promise<Response> {
  if (req.method === "GET") {
    // Lightweight discovery: GET /mcp returns server info as JSON.
    const info = {
      protocolVersion: PROTOCOL_VERSION,
      serverInfo: { name: "yatabase", version: env.YATA_VERSION ?? "0.0.0" },
      capabilities: { tools: { listChanged: false }, resources: { subscribe: false, listChanged: false } },
      transport: "streamable-http",
      authoritativeAdr: "ADR-2605080000 §D20",
    };
    return new Response(JSON.stringify(info), {
      status: 200,
      headers: { "content-type": "application/json", "x-yatabase-surface": "mcp" },
    });
  }
  if (req.method !== "POST") {
    return new Response("MCP requires POST or GET", { status: 405 });
  }

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return badRequestPlain();
  }

  // Batch support (JSON-RPC array). Process serially so that auth resolution
  // stays consistent across the batch.
  if (Array.isArray(raw)) {
    const out: JsonRpcResponse[] = [];
    for (const item of raw) {
      const resp = await dispatchOne(item, req, env, resolveAuth);
      if (resp) out.push(resp);
    }
    return new Response(JSON.stringify(out), {
      status: 200,
      headers: { "content-type": "application/json", "x-yatabase-surface": "mcp" },
    });
  }

  const single = raw as JsonRpcRequest;
  const resp = await dispatchOne(single, req, env, resolveAuth);
  if (!resp) {
    // Notification — no response body, MCP spec says return 204.
    return new Response(null, { status: 204 });
  }
  return jsonResponse(resp);
}

async function dispatchOne(
  rpc: JsonRpcRequest,
  req: Request,
  env: McpEnv,
  resolveAuth: McpAuthResolver,
): Promise<JsonRpcResponse | null> {
  if (!rpc || typeof rpc !== "object" || rpc.jsonrpc !== "2.0" || typeof rpc.method !== "string") {
    return jsonRpcError(rpc?.id ?? null, -32600, "Invalid Request");
  }

  const method = rpc.method;
  const params = (rpc.params ?? {}) as Record<string, unknown>;

  // Notifications (id === undefined) return null per JSON-RPC.
  const isNotification = rpc.id === undefined;

  if (PUBLIC_METHODS.has(method)) {
    if (isNotification && method === "notifications/initialized") return null;
    const result = await handlePublicMethod(method, params, env);
    if (isNotification) return null;
    return jsonRpcResult(rpc.id ?? null, result);
  }

  // Authenticated methods.
  const caller = await resolveAuth(req);
  if (!caller) {
    return jsonRpcError(rpc.id ?? null, -32001, "Unauthorized: tools/call requires Bearer sk_live_yata_* or atproto JWT");
  }

  if (method === "tools/call") {
    const result = await handleToolsCall(params, env, caller);
    if (isNotification) return null;
    if ("error" in result) {
      return jsonRpcError(rpc.id ?? null, result.error.code, result.error.message, result.error.data);
    }
    return jsonRpcResult(rpc.id ?? null, result.value);
  }

  if (method === "resources/read") {
    const result = handleResourcesRead(params);
    if (isNotification) return null;
    if ("error" in result) return jsonRpcError(rpc.id ?? null, result.error.code, result.error.message);
    return jsonRpcResult(rpc.id ?? null, result.value);
  }

  return jsonRpcError(rpc.id ?? null, -32601, `Method not found: ${method}`);
}

async function handlePublicMethod(method: string, params: Record<string, unknown>, env: McpEnv): Promise<unknown> {
  switch (method) {
    case "initialize":
      return {
        protocolVersion: PROTOCOL_VERSION,
        serverInfo: { name: "yatabase", version: env.YATA_VERSION ?? "0.0.0" },
        capabilities: {
          tools: { listChanged: false },
          resources: { subscribe: false, listChanged: false },
          prompts: { listChanged: false },
        },
        instructions:
          "yatabase MCP — graph + storage cell-membrane facade. Authenticate with Bearer sk_live_yata_* before tools/call.",
      };
    case "ping":
      return { ok: true, ts: new Date().toISOString() };
    case "tools/list":
      return {
        tools: TOOLS.map((t) => ({
          name: t.name,
          description: t.description,
          inputSchema: t.inputSchema,
        })),
      };
    case "resources/list":
      return { resources: RESOURCES };
    case "prompts/list":
      return { prompts: [] };
    default:
      return { ok: false, message: "method not implemented yet" };
  }
}

interface ToolsCallOk {
  value: { content: Array<{ type: "text"; text: string }>; isError?: boolean };
}
interface ToolsCallErr {
  error: { code: number; message: string; data?: unknown };
}

async function handleToolsCall(
  params: Record<string, unknown>,
  env: McpEnv,
  caller: DispatcherCallerContext,
): Promise<ToolsCallOk | ToolsCallErr> {
  const name = typeof params["name"] === "string" ? (params["name"] as string) : "";
  const args = (params["arguments"] as Record<string, unknown> | undefined) ?? {};
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) {
    return { error: { code: -32602, message: `tool not found: ${name}` } };
  }
  // P64: KV-backed fallback for yata.graph.cypher → ai.gftd.apps.yata.runCypher.
  // Same engine the REST /cypher uses. Falls through to dispatcher when KV
  // can't serve (e.g. multi-pattern queries).
  if (tool.nsid === "ai.gftd.apps.yata.runCypher") {
    const stmt = typeof args["query"] === "string" ? (args["query"] as string)
      : typeof args["statement"] === "string" ? (args["statement"] as string)
      : "";
    if (stmt) {
      const { tryServeCypherFromKv } = await import("./cypher-kv");
      const kvResult = await tryServeCypherFromKv(env as never, caller.orgDid, stmt);
      if (kvResult) {
        const text = JSON.stringify({ results: [{ columns: kvResult.columns, data: kvResult.data }], errors: [] }, null, 2);
        return { value: { content: [{ type: "text", text }] } };
      }
    }
  }
  const result = await dispatchYataXrpc<Record<string, unknown>>(env, tool.nsid, args, caller, { timeoutMs: 60_000 });
  if (!result.ok) {
    return {
      error: {
        code: -32000,
        message: result.error ?? `dispatcher status ${result.status}`,
        data: { nsid: tool.nsid, status: result.status },
      },
    };
  }
  const text = JSON.stringify(result.data ?? {}, null, 2);
  return { value: { content: [{ type: "text", text }] } };
}

interface ResourcesReadOk {
  value: { contents: Array<{ uri: string; mimeType: string; text: string }> };
}
interface ResourcesReadErr {
  error: { code: number; message: string };
}

function handleResourcesRead(params: Record<string, unknown>): ResourcesReadOk | ResourcesReadErr {
  const uri = typeof params["uri"] === "string" ? (params["uri"] as string) : "";
  const resource = RESOURCES.find((r) => r.uri === uri);
  if (!resource) return { error: { code: -32602, message: `resource not found: ${uri}` } };

  // MVP: surfaces.json points at /_app/meta; agent / mcp point at /.well-known/*.
  // We return JSON pointers rather than echoing the body so the client uses the
  // canonical HTTPS URL.
  const pointer = {
    pointsTo:
      resource.uri === "yatabase://meta/agent"
        ? "https://yatabase.etzhayyim.com/.well-known/agent.json"
        : resource.uri === "yatabase://meta/mcp"
          ? "https://yatabase.etzhayyim.com/.well-known/mcp.json"
          : "https://yatabase.etzhayyim.com/_app/meta",
  };
  return {
    value: {
      contents: [{ uri: resource.uri, mimeType: resource.mimeType, text: JSON.stringify(pointer) }],
    },
  };
}

export function listMcpTools(): Array<{ name: string; nsid: string }> {
  return TOOLS.map((t) => ({ name: t.name, nsid: t.nsid }));
}
