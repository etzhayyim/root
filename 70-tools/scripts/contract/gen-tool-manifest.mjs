#!/usr/bin/env node

/**
 * gen-tool-manifest.mjs — Lexicon JSON → per-app tool-manifest/{app}.ts
 *
 * ADR-0042. Scans 00-contracts/lexicons/com/etzhayyim/apps/{app}/**.json and emits one
 * TypeScript manifest per app with:
 *
 *   - Zod schemas (@hono/zod-openapi v4):
 *       Input_{Method}, Output_{Method}  — per-NSID, .openapi() registered
 *   - OpenAPI routes:
 *       Route_{Method} = createRoute({...})
 *       ROUTES, ROUTE_BY_NSID  — bulk iteration helpers
 *   - MCP_TOOLS:
 *       raw JSON Schema per MCP tools/list spec ({name, description, inputSchema})
 *   - TOOL_MANIFEST:
 *       runtime dispatcher lookup (nsid, description, method:'query'|'procedure',
 *       inputSchema, outputSchema)
 *
 * Lexicon JSON (00-contracts/lexicons/com/etzhayyim/apps) is the Single Source of Truth
 * (ADR-0005). Zod and OpenAPI are derived artifacts — no hand editing.
 *
 * Per-app files (not one global) keep each Worker bundle small: the SDK is imported
 * by every Worker, and 1660 tools × avg 3 KB = several MB if globally emitted.
 *
 * Usage:
 *   node gen-tool-manifest.mjs            # generate for all apps
 *   node gen-tool-manifest.mjs --dry-run  # print first app's output, don't write
 *   node gen-tool-manifest.mjs --app=<n>  # regenerate only one app
 */

import { existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { scanLexicons, filterXrpcLexicons } from "./lib/lexicon-scan.mjs";

const ROOT = process.cwd();
const LEXICON_ROOT = path.join(ROOT, "00-contracts/lexicons/com/etzhayyim/apps");
const OUT_DIR = path.join(
	ROOT,
	"40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/generated/tool-manifest",
);

const args = process.argv.slice(2);
const isDryRun = args.includes("--dry-run");
const appFilter = (args.find((a) => a.startsWith("--app=")) || "").slice(6) || null;

// ── naming helpers ────────────────────────────────────────

function appFromNsid(nsid) {
	return nsid.split(".")[3] || "app";
}

function methodFromNsid(nsid) {
	return nsid.split(".").slice(4).join(".") || "main";
}

function capitalize(s) {
	return s.length === 0 ? s : s[0].toUpperCase() + s.slice(1);
}

function pascal(s) {
	return s
		.split(/[^A-Za-z0-9]/)
		.filter(Boolean)
		.map((part) => capitalize(part))
		.join("");
}

/** OpenAPI components schema name — globally unique across apps. */
function openapiRefName(nsid, suffix) {
	return `${capitalize(appFromNsid(nsid))}${pascal(methodFromNsid(nsid))}${suffix}`;
}

/** Per-app local identifier for a Zod schema / Route constant. */
function localIdent(prefix, nsid) {
	return `${prefix}${pascal(methodFromNsid(nsid))}`;
}

function safeKey(k) {
	return /^[A-Za-z_$][\w$]*$/.test(k) ? k : JSON.stringify(k);
}

// ── lexicon → JSON Schema extraction ──────────────────────

function paramsToObjectSchema(params) {
	if (!params || !params.properties) return null;
	const out = { type: "object", properties: params.properties };
	if (params.required && params.required.length) out.required = params.required;
	if (params.description) out.description = params.description;
	return out;
}

function getInputSchema(lex) {
	const main = lex.defs.main;
	if (main.type === "procedure") {
		const s = main.input?.schema;
		if (s && s.type === "object") return s;
		return { type: "object", properties: {} };
	}
	if (main.type === "query") {
		return paramsToObjectSchema(main.parameters) || { type: "object", properties: {} };
	}
	return { type: "object", properties: {} };
}

function getOutputSchema(lex) {
	const s = lex.defs.main.output?.schema;
	if (s && s.type === "object") return s;
	return { type: "object", properties: {} };
}

// ── JSON Schema → Zod expression emitter ──────────────────
//
// Emits a TS code *string* (not a runtime Zod object) so the output can be
// written to a .ts file and consumed by @hono/zod-openapi at runtime.
//
// Supported shapes (covers >99% of lexicon usage):
//   - object with properties + required
//   - array with items
//   - string (+ enum, format=datetime, pattern, minLength, maxLength, description, default)
//   - number / integer (+ minimum, maximum, description, default)
//   - boolean (+ default)
//   - const → z.literal(value)
//   - type omitted → z.unknown() (ref, union — rare in our lexicons)

function zodExpr(schema) {
	if (!schema || typeof schema !== "object") return "z.unknown()";

	if (schema.const !== undefined) {
		return `z.literal(${JSON.stringify(schema.const)})`;
	}

	if (Array.isArray(schema.type)) {
		// `type: ["string", "null"]` → nullable base
		const nonNull = schema.type.filter((t) => t !== "null");
		const nullable = schema.type.includes("null");
		const base = zodExpr({ ...schema, type: nonNull.length === 1 ? nonNull[0] : undefined });
		return nullable ? `${base}.nullable()` : base;
	}

	switch (schema.type) {
		case "object":
			return zodObject(schema);
		case "array":
			return zodArray(schema);
		case "string":
			return zodString(schema);
		case "integer":
		case "number":
			return zodNumber(schema);
		case "boolean":
			return zodBoolean(schema);
		default:
			return withDescribe("z.unknown()", schema);
	}
}

function zodObject(schema) {
	const props = schema.properties || {};
	const required = new Set(schema.required || []);
	const keys = Object.keys(props);
	if (keys.length === 0) return withDescribe("z.object({}).passthrough()", schema);
	const lines = keys.map((k) => {
		let expr = zodExpr(props[k]);
		if (!required.has(k)) expr = `${expr}.optional()`;
		return `${safeKey(k)}: ${expr}`;
	});
	return withDescribe(`z.object({ ${lines.join(", ")} })`, schema);
}

function zodArray(schema) {
	const items = schema.items ? zodExpr(schema.items) : "z.unknown()";
	let expr = `z.array(${items})`;
	if (typeof schema.minItems === "number") expr += `.min(${schema.minItems})`;
	if (typeof schema.maxItems === "number") expr += `.max(${schema.maxItems})`;
	return withDescribe(expr, schema);
}

function zodString(schema) {
	let expr;
	if (Array.isArray(schema.enum) && schema.enum.length > 0) {
		expr = `z.enum([${schema.enum.map((v) => JSON.stringify(v)).join(", ")}] as const)`;
	} else {
		expr = "z.string()";
		if (schema.format === "datetime") expr += ".datetime({ offset: true })";
		if (schema.format === "uri") expr += ".url()";
		if (typeof schema.pattern === "string") {
			expr += `.regex(new RegExp(${JSON.stringify(schema.pattern)}))`;
		}
		if (typeof schema.minLength === "number") expr += `.min(${schema.minLength})`;
		if (typeof schema.maxLength === "number") expr += `.max(${schema.maxLength})`;
	}
	if (schema.default !== undefined) expr += `.default(${JSON.stringify(schema.default)})`;
	return withDescribe(expr, schema);
}

function zodNumber(schema) {
	let expr = schema.type === "integer" ? "z.number().int()" : "z.number()";
	if (typeof schema.minimum === "number") expr += `.min(${schema.minimum})`;
	if (typeof schema.maximum === "number") expr += `.max(${schema.maximum})`;
	if (schema.default !== undefined) expr += `.default(${JSON.stringify(schema.default)})`;
	return withDescribe(expr, schema);
}

function zodBoolean(schema) {
	let expr = "z.boolean()";
	if (schema.default !== undefined) expr += `.default(${schema.default})`;
	return withDescribe(expr, schema);
}

function withDescribe(expr, schema) {
	if (typeof schema.description === "string" && schema.description.length > 0) {
		return `${expr}.describe(${JSON.stringify(schema.description)})`;
	}
	return expr;
}

// ── manifest emission ─────────────────────────────────────

function emitAppManifest(appName, lexicons) {
	const xrpc = filterXrpcLexicons(lexicons);
	if (xrpc.length === 0) return null;

	const manifest = [];
	const mcpTools = [];

	const zodDecls = [];
	const routeDecls = [];
	const routeNames = [];
	const routeByNsidEntries = [];

	for (const lex of xrpc) {
		const nsid = lex.id;
		const main = lex.defs.main;
		const description = main.description || nsid;
		const inputSchema = getInputSchema(lex);
		const outputSchema = getOutputSchema(lex);
		const methodType = main.type; // 'query' | 'procedure'

		// Runtime manifests (raw JSON Schema)
		manifest.push({ nsid, description, inputSchema, outputSchema, method: methodType });
		mcpTools.push({ name: nsid, description, inputSchema });

		// Zod schemas
		const inputIdent = localIdent("Input", nsid);
		const outputIdent = localIdent("Output", nsid);
		const inputRef = openapiRefName(nsid, "Input");
		const outputRef = openapiRefName(nsid, "Output");

		zodDecls.push(
			`export const ${inputIdent} = ${zodExpr(inputSchema)}.openapi(${JSON.stringify(inputRef)});`,
		);
		zodDecls.push(
			`export const ${outputIdent} = ${zodExpr(outputSchema)}.openapi(${JSON.stringify(outputRef)});`,
		);

		// createRoute config
		const routeIdent = localIdent("Route", nsid);
		const routeExpr = buildRouteExpr({
			nsid,
			description,
			methodType,
			inputIdent,
			outputIdent,
		});
		routeDecls.push(`export const ${routeIdent} = createRoute(${routeExpr});`);
		routeNames.push(routeIdent);
		routeByNsidEntries.push(`${JSON.stringify(nsid)}: ${routeIdent}`);
	}

	// Assemble output file
	const L = [];
	L.push(`// tool-manifest/${appName}.ts — Auto-generated. DO NOT EDIT.`);
	L.push("// Regenerate with: node 70-tools/scripts/contract/gen-tool-manifest.mjs");
	L.push("//");
	L.push("// ADR-0042 — lexicon JSON is the SSoT; this file projects it into:");
	L.push("//   - Zod schemas + createRoute configs (for @hono/zod-openapi)");
	L.push("//   - MCP tools/list entries (raw JSON Schema per MCP spec)");
	L.push("//   - TOOL_MANIFEST (runtime dispatcher lookup)");
	L.push("");
	L.push('import { z, createRoute } from "@hono/zod-openapi";');
	L.push('import type { ToolManifestEntry, McpTool } from "./_types";');
	L.push("");
	L.push(`export const APP_NAME = ${JSON.stringify(appName)} as const;`);
	L.push("");
	L.push("// ── Zod schemas ──");
	L.push("");
	L.push(zodDecls.join("\n\n"));
	L.push("");
	L.push("// ── OpenAPI routes (createRoute configs) ──");
	L.push("");
	L.push(routeDecls.join("\n\n"));
	L.push("");
	L.push("// ── Bulk iteration helpers ──");
	L.push("");
	L.push(`export const ROUTES = [${routeNames.join(", ")}] as const;`);
	L.push("");
	L.push("export const ROUTE_BY_NSID = {");
	for (const entry of routeByNsidEntries) L.push(`\t${entry},`);
	L.push("} as const;");
	L.push("");
	L.push("// ── MCP tools/list (raw JSON Schema, per MCP spec) ──");
	L.push("");
	L.push("export const MCP_TOOLS: readonly McpTool[] = Object.freeze(");
	L.push(stringifyLiteral(mcpTools, 0));
	L.push(") as readonly McpTool[];");
	L.push("");
	L.push("// ── Runtime manifest (dispatcher lookup) ──");
	L.push("");
	L.push("export const TOOL_MANIFEST: readonly ToolManifestEntry[] = Object.freeze(");
	L.push(stringifyLiteral(manifest, 0));
	L.push(") as readonly ToolManifestEntry[];");
	L.push("");

	return L.join("\n");
}

function buildRouteExpr({ nsid, description, methodType, inputIdent, outputIdent }) {
	const httpMethod = methodType === "query" ? "get" : "post";
	const operationId = nsid.replace(/\./g, "_");
	const tag = appFromNsid(nsid);
	const desc = JSON.stringify(description);

	const requestBlock =
		methodType === "query"
			? `request: { query: ${inputIdent} }`
			: `request: { body: { content: { "application/json": { schema: ${inputIdent} } }, required: true } }`;

	return `{
\tmethod: ${JSON.stringify(httpMethod)},
\tpath: ${JSON.stringify(`/xrpc/${nsid}`)},
\toperationId: ${JSON.stringify(operationId)},
\ttags: [${JSON.stringify(tag)}],
\tsummary: ${desc},
\t${requestBlock},
\tresponses: {
\t\t200: {
\t\t\tdescription: "ok",
\t\t\tcontent: { "application/json": { schema: ${outputIdent} } },
\t\t},
\t\tdefault: {
\t\t\tdescription: "error",
\t\t\tcontent: { "application/json": { schema: z.object({ error: z.string(), message: z.string().optional() }).openapi("XrpcError") } },
\t\t},
\t},
}`;
}

function emitTypesFile() {
	return `// tool-manifest/_types.ts — Auto-generated. DO NOT EDIT.
// Regenerate with: node 70-tools/scripts/contract/gen-tool-manifest.mjs
//
// Shared type definitions for per-app tool manifests (ADR-0042).

export type LexiconMainType = "query" | "procedure";

export interface JsonSchemaLike {
	type?: string;
	properties?: Record<string, unknown>;
	required?: string[];
	description?: string;
	[key: string]: unknown;
}

export interface ToolManifestEntry {
	nsid: string;
	description: string;
	inputSchema: JsonSchemaLike;
	outputSchema: JsonSchemaLike;
	method: LexiconMainType;
}

export interface McpTool {
	name: string;
	description: string;
	inputSchema: JsonSchemaLike;
}
`;
}

/** Deterministic, diff-friendly JSON → TS literal. Tabs for indent (matches repo codegen). */
function stringifyLiteral(value, depth) {
	const pad = (n) => "\t".repeat(n);
	if (value === null) return "null";
	if (typeof value !== "object") return JSON.stringify(value);
	if (Array.isArray(value)) {
		if (value.length === 0) return "[]";
		const items = value
			.map((v) => pad(depth + 1) + stringifyLiteral(v, depth + 1))
			.join(",\n");
		return `[\n${items},\n${pad(depth)}]`;
	}
	const entries = Object.entries(value);
	if (entries.length === 0) return "{}";
	const items = entries
		.map(([k, v]) => `${pad(depth + 1)}${safeKey(k)}: ${stringifyLiteral(v, depth + 1)}`)
		.join(",\n");
	return `{\n${items},\n${pad(depth)}}`;
}

// ── main ──────────────────────────────────────────────────

function listAppDirs() {
	if (!existsSync(LEXICON_ROOT)) return [];
	return readdirSync(LEXICON_ROOT, { withFileTypes: true })
		.filter((e) => e.isDirectory() && !e.name.startsWith("_") && e.name !== "archive")
		.map((e) => e.name)
		.sort();
}

const appDirs = listAppDirs().filter((a) => !appFilter || a === appFilter);

if (appDirs.length === 0) {
	console.error(
		appFilter
			? `app '${appFilter}' not found under ${LEXICON_ROOT}`
			: `no app directories under ${LEXICON_ROOT}`,
	);
	process.exit(1);
}

if (!isDryRun) {
	if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });
	writeFileSync(path.join(OUT_DIR, "_types.ts"), emitTypesFile(), "utf8");
}

let emitted = 0;
let skipped = 0;
let firstDryOutput = null;
for (const appName of appDirs) {
	const appDir = path.join(LEXICON_ROOT, appName);
	const lexicons = scanLexicons(appDir);
	const output = emitAppManifest(appName, lexicons);
	if (output === null) {
		skipped++;
		continue;
	}
	if (isDryRun) {
		if (firstDryOutput === null) firstDryOutput = { appName, output };
	} else {
		writeFileSync(path.join(OUT_DIR, `${appName}.ts`), output, "utf8");
	}
	emitted++;
}

if (isDryRun) {
	console.log(`dry-run: would emit ${emitted} files, skip ${skipped}`);
	if (firstDryOutput) {
		console.log(`\n── first app: ${firstDryOutput.appName}.ts ──\n`);
		console.log(firstDryOutput.output);
	}
} else {
	console.log(
		`wrote ${emitted} per-app manifest(s) + _types.ts to ${path.relative(ROOT, OUT_DIR)} (${skipped} app(s) skipped — no xrpc lexicons)`,
	);
}
