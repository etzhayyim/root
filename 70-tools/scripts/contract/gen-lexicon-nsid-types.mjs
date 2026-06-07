#!/usr/bin/env node

// gen-lexicon-nsid-types.mjs — emit typed NSID helpers + input/output types from Lexicon JSON.
//
// F-Plan F2 (2026-04-13): extended beyond the original union-type output to provide:
//   1. KnownLexicon*NSID union types (original)
//   2. AssertCommandNSID / AssertQueryNSID guards (original)
//   3. LEXICON_NSID frozen record — typed string constants for auto-completion
//   4. nsid() tagged helper — enforces NSID existence at call site
//   5. LexiconInput<N> / LexiconOutput<N> — per-NSID I/O type maps from main.input/output schemas
//
// Output: 40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/generated/lexicon-nsid-types.ts

import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { jsonSchemaToTs, hasProperties } from "./lib/lexicon-scan.mjs";

const ROOT = process.cwd();
const OUT_FILE = path.join(
  ROOT,
  "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/generated/lexicon-nsid-types.ts",
);
const LEXICON_ROOTS = ["00-contracts/lexicons", "projects", "packages"].filter((dir) =>
  existsSync(path.join(ROOT, dir)),
);

function listLexiconFiles() {
  let out = "";
  try {
    out = execFileSync(
      "rg",
      ["-l", String.raw`"lexicon"\s*:\s*1`, "-g", "*.json", "-g", "!**/archive/**", "-g", "!**/_archive/**", ...LEXICON_ROOTS],
      { cwd: ROOT, encoding: "utf8" },
    );
  } catch (error) {
    if (error && typeof error === "object" && "status" in error && error.status === 1) {
      return [];
    }
    throw error;
  }
  out = out.trim();
  return out ? out.split("\n").filter(Boolean).sort() : [];
}

function quoteUnion(values) {
  if (values.length === 0) return "never";
  return values.map((v) => JSON.stringify(v)).join(" | ");
}

function extractInputType(lex) {
  const main = lex?.defs?.main;
  if (!main) return "unknown";
  if (main.type === "query" && hasProperties(main.parameters)) {
    return jsonSchemaToTs({ ...main.parameters, type: "object" });
  }
  if (main.type === "procedure" && hasProperties(main.input?.schema)) {
    return jsonSchemaToTs(main.input.schema);
  }
  return "unknown";
}

/**
 * Extract a runtime-serializable input schema descriptor for validation.
 * Returns null when there's no schema (typed as `unknown`).
 * Consumed by parseLexiconInput() in kotodama-host-sdk/src/lexicon-validator.ts.
 */
function extractInputSchemaRuntime(lex) {
  const main = lex?.defs?.main;
  if (!main) return null;
  if (main.type === "query" && hasProperties(main.parameters)) {
    return {
      properties: normalizeSchemaProps(main.parameters.properties),
      required: Array.isArray(main.parameters.required) ? main.parameters.required : [],
    };
  }
  if (main.type === "procedure" && hasProperties(main.input?.schema)) {
    return {
      properties: normalizeSchemaProps(main.input.schema.properties),
      required: Array.isArray(main.input.schema.required) ? main.input.schema.required : [],
    };
  }
  return null;
}

/** Flatten a JSON schema's properties into { name: type } for compact runtime storage. */
function normalizeSchemaProps(props) {
  const out = {};
  for (const [key, spec] of Object.entries(props || {})) {
    const t = spec?.type;
    if (t === "string" || t === "integer" || t === "number" || t === "boolean") {
      out[key] = t;
    } else if (t === "array") {
      out[key] = "array";
    } else if (t === "object") {
      out[key] = "object";
    } else {
      out[key] = "unknown";
    }
  }
  return out;
}

function extractOutputType(lex) {
  const main = lex?.defs?.main;
  if (!main) return "unknown";
  if (hasProperties(main.output?.schema)) {
    return jsonSchemaToTs(main.output.schema);
  }
  return "unknown";
}

function generate() {
  const query = [];
  const procedure = [];
  const subscription = [];
  const record = [];
  const permissionSet = [];
  /** @type {Map<string, { inputTs: string, outputTs: string, kind: string }>} */
  const ioByNsid = new Map();
  /** @type {Map<string, { properties: Record<string,string>, required: string[] }>} */
  const runtimeSchemaByNsid = new Map();

  for (const rel of listLexiconFiles()) {
    const full = path.join(ROOT, rel);
    let json;
    try {
      json = JSON.parse(readFileSync(full, "utf8"));
    } catch {
      continue;
    }
    const id = json?.id;
    const mainType = json?.defs?.main?.type;
    if (typeof id !== "string" || typeof mainType !== "string") continue;
    if (mainType === "query") query.push(id);
    else if (mainType === "procedure") procedure.push(id);
    else if (mainType === "subscription") subscription.push(id);
    else if (mainType === "record") record.push(id);
    else if (mainType === "permission-set") permissionSet.push(id);

    if (mainType === "query" || mainType === "procedure") {
      ioByNsid.set(id, {
        kind: mainType,
        inputTs: extractInputType(json),
        outputTs: extractOutputType(json),
      });
      const rs = extractInputSchemaRuntime(json);
      if (rs) runtimeSchemaByNsid.set(id, rs);
    }
  }

  query.sort();
  procedure.sort();
  subscription.sort();
  record.sort();
  permissionSet.sort();

  // LEXICON_NSID frozen record — keyed by the NSID string itself for zero cognitive overhead.
  // Consumers write LEXICON_NSID["com.etzhayyim.apps.oshikatsu.tip"] and get compile-time verification.
  const allXrpcNsids = [...new Set([...query, ...procedure])].sort();

  const lines = [];
  lines.push("/* AUTO-GENERATED by scripts/contract/gen-lexicon-nsid-types.mjs. DO NOT EDIT. */");
  lines.push("");
  lines.push(`export type KnownLexiconQueryNSID = ${quoteUnion(query)};`);
  lines.push(`export type KnownLexiconProcedureNSID = ${quoteUnion(procedure)};`);
  lines.push(`export type KnownLexiconSubscriptionNSID = ${quoteUnion(subscription)};`);
  lines.push(`export type KnownLexiconRecordNSID = ${quoteUnion(record)};`);
  lines.push(`export type KnownLexiconPermissionSetNSID = ${quoteUnion(permissionSet)};`);
  lines.push("");
  lines.push("export type KnownLexiconNSID =");
  lines.push("  | KnownLexiconQueryNSID");
  lines.push("  | KnownLexiconProcedureNSID");
  lines.push("  | KnownLexiconSubscriptionNSID");
  lines.push("  | KnownLexiconRecordNSID");
  lines.push("  | KnownLexiconPermissionSetNSID;");
  lines.push("");
  lines.push("// ── NSID guards (F-Plan F2 archive, 2026-04-13) ──");
  lines.push("// `sdk.app.command` / `sdk.app.query` enforce StrictCommandNSID / StrictQueryNSID.");
  lines.push("// Legacy loose AssertCommandNSID / AssertQueryNSID archived to");
  lines.push("// _archive/40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk-legacy-nsid-assert-260413/.");
  lines.push("");
  lines.push("type QueryAsCommandError<N extends string> = `NSID \"${N}\" is a lexicon query; register via app.query(...)`;");
  lines.push("type ProcedureAsQueryError<N extends string> = `NSID \"${N}\" is a lexicon procedure; register via app.command(...)`;");
  lines.push("type UnknownNsidError<N extends string> = `NSID \"${N}\" is not defined in 00-contracts/lexicons/. Create the lexicon JSON first (run bootstrap-app-lexicons.mjs or author by hand).`;");
  lines.push("");
  lines.push("// Strict variants — the only supported form after F-Plan F2 archive (2026-04-13).");
  lines.push("// `sdk.app.command` / `sdk.app.query` use these.");
  lines.push("export type StrictCommandNSID<N extends string> = N extends KnownLexiconProcedureNSID ? N");
  lines.push("  : N extends KnownLexiconQueryNSID ? QueryAsCommandError<N>");
  lines.push("  : UnknownNsidError<N>;");
  lines.push("export type StrictQueryNSID<N extends string> = N extends KnownLexiconQueryNSID ? N");
  lines.push("  : N extends KnownLexiconProcedureNSID ? ProcedureAsQueryError<N>");
  lines.push("  : UnknownNsidError<N>;");
  lines.push("");
  lines.push("// ── LEXICON_NSID frozen record ──");
  lines.push("// Typed string constants for auto-completion. Usage:");
  lines.push("//   sdk.app.lexiconCommand(LEXICON_NSID[\"com.etzhayyim.apps.foo.bar\"], handler)");
  lines.push("// The key IS the value, so no cognitive transformation is needed.");
  lines.push("");
  lines.push("export const LEXICON_NSID = {");
  for (const id of allXrpcNsids) {
    lines.push(`\t${JSON.stringify(id)}: ${JSON.stringify(id)},`);
  }
  lines.push("} as const;");
  lines.push("");
  lines.push("export type LexiconNsid = keyof typeof LEXICON_NSID;");
  lines.push("");
  lines.push("// ── nsid() tagged helper ──");
  lines.push("// Enforces that the NSID exists at call site. Usage:");
  lines.push("//   sdk.app.command(nsid(\"com.etzhayyim.apps.foo.bar\"), handler) // typo → compile error");
  lines.push("");
  lines.push("export function nsid<N extends LexiconNsid>(n: N): N {");
  lines.push("\treturn n;");
  lines.push("}");
  lines.push("");
  lines.push("// ── Per-NSID input / output type maps (F-Plan F2, 2026-04-13) ──");
  lines.push("// Handler can be declared as:");
  lines.push("//   async (ctx, body) => {");
  lines.push("//     const input = decodeJson<LexiconInput<\"com.etzhayyim.apps.foo.bar\">>(body);");
  lines.push("//     ...");
  lines.push("//     return {} as LexiconOutput<\"com.etzhayyim.apps.foo.bar\">;");
  lines.push("//   }");
  lines.push("// eliminating manual schema duplication in handler bodies.");
  lines.push("");
  lines.push("export interface LexiconInputMap {");
  const sortedEntries = [...ioByNsid.entries()].sort(([a], [b]) => a.localeCompare(b));
  for (const [id, { inputTs }] of sortedEntries) {
    lines.push(`\t${JSON.stringify(id)}: ${inputTs};`);
  }
  lines.push("}");
  lines.push("");
  lines.push("export interface LexiconOutputMap {");
  for (const [id, { outputTs }] of sortedEntries) {
    lines.push(`\t${JSON.stringify(id)}: ${outputTs};`);
  }
  lines.push("}");
  lines.push("");
  lines.push("export type LexiconInput<N extends LexiconNsid> = N extends keyof LexiconInputMap ? LexiconInputMap[N] : unknown;");
  lines.push("export type LexiconOutput<N extends LexiconNsid> = N extends keyof LexiconOutputMap ? LexiconOutputMap[N] : unknown;");
  lines.push("");
  lines.push("// ── Runtime input schema registry (F-Plan F2+6, 2026-04-13) ──");
  lines.push("// Compact per-NSID input schema used by parseLexiconInput() runtime validator in");
  lines.push("// kotodama-host-sdk/src/lexicon-validator.ts. Only properties + required are stored.");
  lines.push("");
  lines.push("export type LexiconPrimitiveType = 'string' | 'integer' | 'number' | 'boolean' | 'array' | 'object' | 'unknown';");
  lines.push("");
  lines.push("export interface LexiconRuntimeSchema {");
  lines.push("\treadonly properties: Readonly<Record<string, LexiconPrimitiveType>>;");
  lines.push("\treadonly required: ReadonlyArray<string>;");
  lines.push("}");
  lines.push("");
  lines.push("export const LEXICON_INPUT_SCHEMA: Readonly<Record<string, LexiconRuntimeSchema>> = Object.freeze({");
  const sortedRuntime = [...runtimeSchemaByNsid.entries()].sort(([a], [b]) => a.localeCompare(b));
  for (const [id, schema] of sortedRuntime) {
    const propsJson = JSON.stringify(schema.properties);
    const reqJson = JSON.stringify(schema.required);
    lines.push(`\t${JSON.stringify(id)}: Object.freeze({ properties: Object.freeze(${propsJson}), required: Object.freeze(${reqJson}) }),`);
  }
  lines.push("});");
  lines.push("");

  mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  writeFileSync(OUT_FILE, lines.join("\n"), "utf8");
  console.log(
    `generated lexicon nsid types: query=${query.length} procedure=${procedure.length} subscription=${subscription.length} record=${record.length} permission-set=${permissionSet.length} io-map=${ioByNsid.size}`,
  );
}

generate();
