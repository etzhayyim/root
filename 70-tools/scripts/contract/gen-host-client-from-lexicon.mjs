#!/usr/bin/env node

/**
 * gen-host-client-from-lexicon.mjs — Lexicon JSON → host-client.ts
 *
 * Sister script to gen-service-from-lexicon.mjs. Scans com.etzhayyim.host.* lexicons
 * and emits a typed in-process host capability client for kotodama-host-sdk.
 *
 * F-Plan (Lexicon SSoT) Phase 1: replaces WIT-defined host imports with Lexicon-defined
 * host capabilities. Generated client calls a user-provided HostDispatcher (BindingTransport
 * pattern) which routes NSIDs to host implementation functions in host-imports.ts.
 *
 * Usage:
 *   node gen-host-client-from-lexicon.mjs            # generate host-client.ts
 *   node gen-host-client-from-lexicon.mjs --dry-run  # print to stdout
 */

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { scanLexicons, jsonSchemaToTs, hasProperties, filterXrpcLexicons } from "./lib/lexicon-scan.mjs";

const ROOT = process.cwd();
const LEXICON_DIR = path.join(ROOT, "00-contracts/lexicons/com/etzhayyim/host");
const OUT_DIR = path.join(ROOT, "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/generated");
const OUT_FILE = path.join(OUT_DIR, "host-client.ts");

const args = process.argv.slice(2);
const isDryRun = args.includes("--dry-run");

// com.etzhayyim.host.secrets.get → secretsGet
// com.etzhayyim.host.sql.query → sqlQuery
// com.etzhayyim.host.llm.converse → llmConverse
function nsidToCamelMethod(nsid) {
  const parts = nsid.split(".");
  // strip com.etzhayyim.host prefix → [domain, action, ...]
  const tail = parts.slice(3);
  if (tail.length === 0) return parts[parts.length - 1];
  return tail
    .map((p, i) => (i === 0 ? p : p[0].toUpperCase() + p.slice(1)))
    .join("");
}

function extractInputType(lex) {
  const main = lex.defs.main;
  if (main.type === "query" && hasProperties(main.parameters)) {
    // Lexicon params block uses type:"params"; normalize to object for TS emission.
    return jsonSchemaToTs({ ...main.parameters, type: "object" });
  }
  if (main.type === "procedure" && hasProperties(main.input?.schema)) {
    return jsonSchemaToTs(main.input.schema);
  }
  return "Record<string, unknown>";
}

function extractOutputType(lex) {
  const main = lex.defs.main;
  if (hasProperties(main.output?.schema)) {
    return jsonSchemaToTs(main.output.schema);
  }
  return "Record<string, unknown>";
}

function generateHostClient(lexicons) {
  const lines = [];
  lines.push("// host-client.ts — Auto-generated typed host capability client.");
  lines.push("// DO NOT EDIT. Regenerate with: node 70-tools/scripts/contract/gen-host-client-from-lexicon.mjs");
  lines.push("//");
  lines.push("// Lexicon JSON (00-contracts/lexicons/com/etzhayyim/host/) is the Single Source of Truth");
  lines.push("// for host capability surface. F-Plan Phase 1: replaces WIT-defined host imports.");
  lines.push("//");
  lines.push("// Runtime contract: each function forwards to a HostDispatcher supplied at SDK init.");
  lines.push("// The dispatcher routes NSIDs to host implementation functions (in-process, BindingTransport).");
  lines.push("");
  lines.push("export interface HostDispatcher {");
  lines.push("\tdispatch<T>(nsid: string, input: unknown): Promise<T>;");
  lines.push("}");
  lines.push("");
  lines.push("let _dispatcher: HostDispatcher | null = null;");
  lines.push("");
  lines.push("export function setHostDispatcher(dispatcher: HostDispatcher): void {");
  lines.push("\t_dispatcher = dispatcher;");
  lines.push("}");
  lines.push("");
  lines.push("function requireDispatcher(): HostDispatcher {");
  lines.push("\tif (!_dispatcher) {");
  lines.push("\t\tthrow new Error('HostDispatcher not set. Call setHostDispatcher() during SDK init.');");
  lines.push("\t}");
  lines.push("\treturn _dispatcher;");
  lines.push("}");
  lines.push("");
  lines.push("// ── NSID constants (frozen Single Source) ──");
  lines.push("");
  lines.push("export const HOST_NSID = {");
  for (const lex of lexicons) {
    const method = nsidToCamelMethod(lex.id);
    lines.push(`\t${method}: '${lex.id}' as const,`);
  }
  lines.push("} as const;");
  lines.push("");
  lines.push("// ── Typed capability functions ──");
  lines.push("");

  let prevDomain = "";
  for (const lex of lexicons) {
    const parts = lex.id.split(".");
    const domain = parts[3] ?? "root";
    if (domain !== prevDomain) {
      if (prevDomain !== "") lines.push("");
      lines.push(`// ── ${domain} ──`);
      lines.push("");
      prevDomain = domain;
    }
    const method = nsidToCamelMethod(lex.id);
    const inputType = extractInputType(lex);
    const outputType = extractOutputType(lex);
    const desc = lex.defs.main.description;
    if (desc) {
      lines.push(`/** ${desc} */`);
    }
    lines.push(`export async function ${method}(input: ${inputType}): Promise<${outputType}> {`);
    lines.push(`\treturn requireDispatcher().dispatch<${outputType}>(HOST_NSID.${method}, input);`);
    lines.push("}");
    lines.push("");
  }

  return lines.join("\n");
}

// ── Main ──

const lexicons = scanLexicons(LEXICON_DIR);
if (lexicons.length === 0) {
  console.error(`No host lexicons found under ${LEXICON_DIR}`);
  process.exit(1);
}

const xrpcLexicons = filterXrpcLexicons(lexicons);

console.log(`found ${xrpcLexicons.length} host lexicons (${lexicons.length} total)`);

const output = generateHostClient(xrpcLexicons);

if (isDryRun) {
  console.log(output);
} else {
  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(OUT_FILE, output, "utf8");
  console.log(`wrote ${OUT_FILE}`);
}
