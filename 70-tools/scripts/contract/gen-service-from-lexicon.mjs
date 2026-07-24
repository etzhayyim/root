#!/usr/bin/env node

/**
 * gen-service-from-lexicon.mjs — Lexicon JSON → service-generated.ts
 *
 * Lexicon JSON is the Single Source of Truth for XRPC client type generation.
 * F-Plan F2 (2026-04-13): legacy `--bootstrap` mode removed — use
 * `70-tools/scripts/contract/bootstrap-app-lexicons.mjs` for app lexicon bootstrap
 * (or `bootstrap-host-lexicons.mjs` for host capability lexicons).
 *
 * Usage:
 *   node gen-service-from-lexicon.mjs              # generate service-generated.ts
 *   node gen-service-from-lexicon.mjs --dry-run    # print to stdout
 */

import { writeFileSync } from "node:fs";
import path from "node:path";
import { scanLexicons, jsonSchemaToTs, hasProperties, filterXrpcLexicons } from "./lib/lexicon-scan.mjs";

const ROOT = process.cwd();
const LEXICON_DIR = path.join(ROOT, "00-contracts/lexicons");
const OUT_FILE = path.join(ROOT, "../com-etzhayyim-xrpc/src/lexicon-types.gen.ts");

const args = process.argv.slice(2);
const isDryRun = args.includes("--dry-run");

// ── NSID → method name derivation ──

function nsidToMethodName(nsid) {
  const parts = nsid.split(".");
  return parts[parts.length - 1];
}

function namespaceQualifiedMethodName(nsid) {
  const parts = nsid.split(".");
  const base = parts[parts.length - 1];
  const prefixParts = parts.slice(2, -1);
  const prefix = prefixParts.map((part, index) => (
    index === 0 ? part : part[0].toUpperCase() + part.slice(1)
  )).join("");
  return prefix
    ? `${prefix}${base[0].toUpperCase()}${base.slice(1)}`
    : base;
}

function fullyQualifiedMethodName(nsid) {
  const parts = nsid.split(".");
  const base = parts[parts.length - 1];
  const prefixParts = parts.slice(0, -1);
  const prefix = prefixParts.map((part, index) => (
    index === 0 ? part : part[0].toUpperCase() + part.slice(1)
  )).join("");
  return `${prefix}${base[0].toUpperCase()}${base.slice(1)}`;
}

function classifyMethod(nsid, lexiconType) {
  if (lexiconType === "query") return "query";
  if (lexiconType === "procedure") return "procedure";
  // fallback: classify by name prefix
  const method = nsidToMethodName(nsid);
  if (/^(get|list|search|resolve|check)/.test(method)) return "query";
  return "procedure";
}

// ── JSON Schema → TypeScript type (jsonSchemaToTs / hasProperties imported from lib) ──

function extractParamsType(lexicon) {
  const main = lexicon.defs?.main;
  if (!main) return "{ params: string }";

  // query: parameters field — only use typed params if properties are defined
  if (main.type === "query" && hasProperties(main.parameters)) {
    return jsonSchemaToTs(main.parameters);
  }
  // procedure: input.schema — only use typed params if properties are defined
  if (main.type === "procedure" && hasProperties(main.input?.schema)) {
    return jsonSchemaToTs(main.input.schema);
  }
  // fallback: string params passthrough (legacy-compatible)
  return "{ params: string }";
}

function extractResponseType(lexicon) {
  const main = lexicon.defs?.main;
  if (!main) return "string";

  if (hasProperties(main.output?.schema)) {
    return jsonSchemaToTs(main.output.schema);
  }
  // fallback: string (legacy-compatible)
  return "string";
}

// ── Code Generator ──

function generateServiceTs(lexicons) {
  const lines = [];

  lines.push("// service-generated.ts — Auto-generated XRPC client from Lexicon JSON definitions.");
  lines.push("// DO NOT EDIT. Regenerate with: node 70-tools/scripts/contract/gen-service-from-lexicon.mjs");
  lines.push("// Lexicon JSON (00-contracts/lexicons/) is the Single Source of Truth.");
  lines.push("// Hand-written overrides go in service-overrides.ts.");
  lines.push("");
  lines.push("import { atQuery, atProcedure } from './client.js';");
  lines.push("import type { WFeedItem, WPost, WPostAuthor, WFollow, WAuthorProfile, WNotification, Convo, ConvoMember, WEnvelope } from './types.js';");
  lines.push("");

  let prevNs = "";
  const methodEntries = [];
  const methodCounts = new Map();
  for (const lex of lexicons) {
    const methodName = nsidToMethodName(lex.id);
    methodCounts.set(methodName, (methodCounts.get(methodName) ?? 0) + 1);
  }

  // Second-pass: compute namespace-qualified names and detect remaining collisions.
  // Colliders fall back to fully-qualified names (TLD included) to guarantee uniqueness.
  const resolvedNames = new Map();
  const nsQualifiedCounts = new Map();
  for (const lex of lexicons) {
    const simple = nsidToMethodName(lex.id);
    const name = (methodCounts.get(simple) ?? 0) > 1
      ? namespaceQualifiedMethodName(lex.id)
      : simple;
    nsQualifiedCounts.set(name, (nsQualifiedCounts.get(name) ?? 0) + 1);
  }
  for (const lex of lexicons) {
    const simple = nsidToMethodName(lex.id);
    let name;
    if ((methodCounts.get(simple) ?? 0) <= 1) {
      name = simple;
    } else {
      const nsq = namespaceQualifiedMethodName(lex.id);
      name = (nsQualifiedCounts.get(nsq) ?? 0) > 1
        ? fullyQualifiedMethodName(lex.id)
        : nsq;
    }
    resolvedNames.set(lex.id, name);
  }

  for (const lex of lexicons) {
    const nsid = lex.id;
    const parts = nsid.split(".");
    const ns = parts.length >= 3 ? parts.slice(0, 3).join(".") : nsid;

    if (ns !== prevNs) {
      if (prevNs !== "") lines.push("");
      lines.push(`// ── ${ns} ──`);
      lines.push("");
      prevNs = ns;
    }

    const methodName = resolvedNames.get(nsid);
    const kind = classifyMethod(nsid, lex.defs.main.type);
    const paramsType = extractParamsType(lex);
    const responseType = extractResponseType(lex);

    methodEntries.push({ nsid, methodName, kind, paramsType, responseType, description: lex.defs.main.description });
  }

  // Export functions
  prevNs = "";
  for (const entry of methodEntries) {
    const parts = entry.nsid.split(".");
    const ns = parts.length >= 3 ? parts.slice(0, 3).join(".") : entry.nsid;

    if (ns !== prevNs) {
      if (prevNs !== "") lines.push("");
      lines.push(`// ── ${ns} ──`);
      lines.push("");
      prevNs = ns;
    }

    if (entry.description) {
      lines.push(`/** ${entry.description} */`);
    }

    const hasParams = entry.paramsType !== "void";
    const paramsSig = hasParams ? `params: ${entry.paramsType}` : "";
    const callArgs = hasParams ? "params" : "";

    // For legacy { params: string } style, wrap in object
    const isLegacyStringParams = entry.paramsType === "{ params: string }";
    const rpcFn = entry.kind === "query" ? "atQuery" : "atProcedure";
    const callExpr = isLegacyStringParams
      ? `${rpcFn}<${entry.responseType}>('${entry.nsid}', { params })`
      : hasParams
        ? `${rpcFn}<${entry.responseType}>('${entry.nsid}', params as Record<string, unknown> | undefined)`
        : `${rpcFn}<${entry.responseType}>('${entry.nsid}')`;

    if (isLegacyStringParams) {
      lines.push(`export async function ${entry.methodName}(params: string): Promise<${entry.responseType}> {`);
    } else {
      lines.push(`export async function ${entry.methodName}(${paramsSig}): Promise<${entry.responseType}> {`);
    }
    lines.push(`\treturn ${callExpr};`);
    lines.push("}");
    lines.push("");
  }

  return lines.join("\n");
}

// ── Main ──

const lexicons = scanLexicons(LEXICON_DIR);
if (lexicons.length === 0) {
  console.error(`No lexicon files found under ${LEXICON_DIR}. Run bootstrap-app-lexicons.mjs or bootstrap-host-lexicons.mjs first.`);
  process.exit(1);
}

// Filter to only query/procedure (not record/subscription)
const xrpcLexicons = filterXrpcLexicons(lexicons);

console.log(`found ${xrpcLexicons.length} XRPC lexicons (${lexicons.length} total)`);

const output = generateServiceTs(xrpcLexicons);

if (isDryRun) {
  console.log(output);
} else {
  writeFileSync(OUT_FILE, output, "utf8");
  console.log(`wrote ${OUT_FILE}`);
}
