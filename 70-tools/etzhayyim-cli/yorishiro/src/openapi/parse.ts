// openapi/parse.ts — minimal OpenAPI v3 reader.
//
// Phase 1 scope: read a JSON OpenAPI 3.x spec from a local path or http(s) URL
// and project it into a normalized OpType[] that the emitter layer consumes.
// YAML support and $ref chasing into external files are deferred.

import { readFileSync } from "node:fs";
import { resolve as resolvePath } from "node:path";

export interface OpenApiSpec {
  openapi: string;
  info: { title: string; version: string; description?: string };
  servers?: Array<{ url: string; description?: string }>;
  paths: Record<string, Record<string, OpenApiOperation>>;
  components?: { schemas?: Record<string, JsonSchema> };
}

export interface OpenApiOperation {
  operationId?: string;
  summary?: string;
  description?: string;
  parameters?: Array<OpenApiParameter>;
  requestBody?: {
    required?: boolean;
    content?: Record<string, { schema?: JsonSchema }>;
  };
  responses?: Record<string, { description?: string; content?: Record<string, { schema?: JsonSchema }> }>;
}

export interface OpenApiParameter {
  name: string;
  in: "query" | "header" | "path" | "cookie";
  required?: boolean;
  description?: string;
  schema?: JsonSchema;
}

export interface JsonSchema {
  type?: string;
  format?: string;
  enum?: unknown[];
  default?: unknown;
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  description?: string;
  items?: JsonSchema;
  properties?: Record<string, JsonSchema>;
  required?: string[];
  $ref?: string;
}

export interface NormalizedOp {
  opName: string;
  httpMethod: string;
  pathTemplate: string;
  summary: string;
  description: string;
  parameters: NormalizedParam[];
  requestBodySchema?: JsonSchema;
  responseSchema: JsonSchema;
  responseContentType: string;
}

export interface NormalizedParam {
  name: string;
  in: "query" | "path" | "header" | "cookie";
  required: boolean;
  description: string;
  schema: JsonSchema;
}

export async function readOpenApi(sourceUrlOrPath: string): Promise<OpenApiSpec> {
  let raw: string;
  if (sourceUrlOrPath.startsWith("http://") || sourceUrlOrPath.startsWith("https://")) {
    const res = await fetch(sourceUrlOrPath);
    if (!res.ok) throw new Error(`fetch OpenAPI spec failed: ${res.status} ${res.statusText}`);
    raw = await res.text();
  } else {
    raw = readFileSync(resolvePath(process.cwd(), sourceUrlOrPath), "utf-8");
  }
  const parsed = JSON.parse(raw) as OpenApiSpec;
  if (!parsed.openapi || !parsed.openapi.startsWith("3.")) {
    throw new Error(`unsupported OpenAPI version: ${parsed.openapi ?? "<missing>"} (Phase 1 requires 3.x)`);
  }
  return parsed;
}

const HTTP_METHODS = ["get", "post", "put", "patch", "delete", "head", "options"] as const;

export function normalize(spec: OpenApiSpec): NormalizedOp[] {
  const ops: NormalizedOp[] = [];
  for (const [pathTemplate, pathItem] of Object.entries(spec.paths ?? {})) {
    for (const method of HTTP_METHODS) {
      const op = pathItem[method];
      if (!op) continue;

      const opName = op.operationId ?? deriveOpName(method, pathTemplate);
      const parameters = (op.parameters ?? []).map((p): NormalizedParam => ({
        name: p.name,
        in: p.in,
        required: p.required ?? p.in === "path",
        description: p.description ?? "",
        schema: p.schema ?? { type: "string" },
      }));

      const requestBodySchema = pickJsonSchema(op.requestBody?.content);
      const respJson = op.responses?.["200"] ?? op.responses?.["201"] ?? op.responses?.default;
      const responseSchema =
        pickJsonSchema(respJson?.content) ?? ({ type: "object" } as JsonSchema);
      const responseContentType = firstContentType(respJson?.content) ?? "application/json";

      ops.push({
        opName,
        httpMethod: method.toUpperCase(),
        pathTemplate,
        summary: op.summary ?? "",
        description: op.description ?? op.summary ?? "",
        parameters,
        requestBodySchema,
        responseSchema,
        responseContentType,
      });
    }
  }
  return ops;
}

function deriveOpName(method: string, path: string): string {
  // /search/foo-bar/{id} → searchFooBarById  (very lightweight; the spec
  //   author is encouraged to set operationId explicitly)
  const segs = path
    .split("/")
    .filter((s) => s.length > 0)
    .map((s) => (s.startsWith("{") ? `By${capitalize(s.slice(1, -1))}` : s));
  const tail = segs
    .join("-")
    .replace(/[^a-zA-Z0-9-]/g, "")
    .split("-")
    .map((s, i) => (i === 0 ? s : capitalize(s)))
    .join("");
  return `${method}${capitalize(tail || "root")}`;
}

function capitalize(s: string): string {
  return s.length === 0 ? s : s[0]!.toUpperCase() + s.slice(1);
}

function pickJsonSchema(
  content: Record<string, { schema?: JsonSchema }> | undefined,
): JsonSchema | undefined {
  if (!content) return undefined;
  // Prefer application/json, then anything that has a schema, else fall back
  //   to a generic string for raw/binary responses (e.g. atom+xml).
  const json = content["application/json"]?.schema;
  if (json) return json;
  for (const v of Object.values(content)) {
    if (v.schema) return v.schema;
  }
  return { type: "string" };
}

function firstContentType(
  content: Record<string, { schema?: JsonSchema }> | undefined,
): string | undefined {
  if (!content) return undefined;
  if (content["application/json"]) return "application/json";
  return Object.keys(content)[0];
}
