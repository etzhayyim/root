#!/usr/bin/env node

/**
 * gen-pds-lexicon-registry.mjs — Lexicon JSON → PDS typed NSID registry
 *
 * Generates `pds-lexicon-registry.gen.ts` for server-side type-safe XRPC dispatch.
 * Provides: NSID literal union types, per-NSID Input/Output types, typed method map,
 * record types, $ref resolution, union types, and runtime schema validation.
 *
 * Usage:
 *   node gen-pds-lexicon-registry.mjs              # generate to PDS src/
 *   node gen-pds-lexicon-registry.mjs --dry-run     # print to stdout
 */

import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const LEXICON_DIR = path.join(ROOT, "00-contracts/lexicons");
const OUT_FILE = path.join(ROOT, "50-infra/cloudflare/workers/atproto/src/generated/lexicon-registry.gen.ts");
const CLIENT_OUT_FILE = path.join(ROOT, "../com-etzhayyim-xrpc/src/lexicon-types.gen.ts");

const isDryRun = process.argv.includes("--dry-run");

// ── Lexicon Scanner ──

/**
 * Scan all lexicon JSON files. Includes defs-only lexicons (no main def)
 * so their named defs are available for $ref resolution.
 */
function scanLexicons(dir) {
  const results = [];
  if (!existsSync(dir)) return results;
  function walk(d) {
    for (const entry of readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "archive" || entry.name === "_archive") continue;
        walk(full);
      }
      else if (entry.name.endsWith(".json")) {
        try {
          const json = JSON.parse(readFileSync(full, "utf8"));
          // Accept any lexicon v1 with an id and defs (not just those with main.type)
          if (json.lexicon === 1 && json.id && json.defs) {
            results.push(json);
          }
        } catch { /* skip malformed JSON */ }
      }
    }
  }
  walk(dir);
  return results.sort((a, b) => a.id.localeCompare(b.id));
}

// ── $ref Resolution Index ──

/** @type {Map<string, object>} */
let defIndex = new Map();

function buildDefIndex(lexicons) {
  defIndex = new Map();
  for (const lex of lexicons) {
    if (!lex.defs) continue;
    for (const [defName, defSchema] of Object.entries(lex.defs)) {
      const key = defName === "main" ? lex.id : `${lex.id}#${defName}`;
      defIndex.set(key, defSchema);
    }
  }
}

/**
 * Resolve a $ref string to its schema.
 * Formats:
 *   "#localDef"                         → current lexicon's def
 *   "com.atproto.label.defs#label"      → cross-namespace def
 *   "app.bsky.richtext.facet"           → main def of another lexicon
 */
function resolveRef(ref, currentLexiconId) {
  if (!ref) return null;
  if (ref.startsWith("#")) {
    return defIndex.get(`${currentLexiconId}#${ref.slice(1)}`) ?? null;
  }
  if (ref.includes("#")) {
    return defIndex.get(ref) ?? null;
  }
  return defIndex.get(ref) ?? null;
}

// ── Schema → TypeScript Conversion ──

function hasProperties(schema) {
  return schema?.properties && Object.keys(schema.properties).length > 0;
}

const _resolving = new Set();

/**
 * Convert a Lexicon schema to TypeScript type string.
 * Handles: string, integer, number, boolean, array, object, ref, union, bytes, blob, unknown, params.
 */
function jsonSchemaToTs(schema, currentLexiconId = "", depth = 0) {
  if (!schema) return "Record<string, unknown>";
  if (depth > 8) return "Record<string, unknown>";

  switch (schema.type) {
    case "string": return "string";
    case "integer": return "number";
    case "number": return "number";
    case "boolean": return "boolean";
    case "bytes": return "Uint8Array";
    case "blob": return "Blob";
    case "unknown": return "unknown";
    case "cid-link": return "string";

    case "array": {
      if (schema.items) return `(${jsonSchemaToTs(schema.items, currentLexiconId, depth + 1)})[]`;
      return "unknown[]";
    }

    case "ref": {
      const refStr = schema.ref;
      if (!refStr) return "unknown";
      const resolveKey = `${currentLexiconId}>${refStr}`;
      if (_resolving.has(resolveKey)) return "Record<string, unknown>";
      _resolving.add(resolveKey);
      try {
        const resolved = resolveRef(refStr, currentLexiconId);
        if (!resolved) return "unknown";
        const refLexId = refStr.startsWith("#") ? currentLexiconId : (refStr.includes("#") ? refStr.split("#")[0] : refStr);
        return jsonSchemaToTs(resolved, refLexId, depth + 1);
      } finally {
        _resolving.delete(resolveKey);
      }
    }

    case "union": {
      const refs = schema.refs;
      if (!refs || refs.length === 0) return "unknown";
      const types = refs.map((r) => {
        const resolveKey = `${currentLexiconId}>${r}`;
        if (_resolving.has(resolveKey)) return "Record<string, unknown>";
        _resolving.add(resolveKey);
        try {
          const resolved = resolveRef(r, currentLexiconId);
          if (!resolved) return "unknown";
          const refLexId = r.includes("#") ? r.split("#")[0] : r;
          return jsonSchemaToTs(resolved, refLexId, depth + 1);
        } finally {
          _resolving.delete(resolveKey);
        }
      });
      const unique = [...new Set(types)];
      return unique.length === 1 ? unique[0] : `(${unique.join(" | ")})`;
    }

    case "object": {
      if (!hasProperties(schema)) return "Record<string, unknown>";
      const props = Object.entries(schema.properties).map(([key, val]) => {
        const optional = !(schema.required || []).includes(key) ? "?" : "";
        const safeKey = /^[A-Za-z_$][\w$]*$/.test(key) ? key : JSON.stringify(key);
        const tsType = jsonSchemaToTs(val, currentLexiconId, depth + 1);
        return `${safeKey}${optional}: ${tsType}`;
      });
      return `{ ${props.join("; ")} }`;
    }

    case "params": {
      if (!hasProperties(schema)) return "Record<string, unknown>";
      const props = Object.entries(schema.properties).map(([key, val]) => {
        const optional = !(schema.required || []).includes(key) ? "?" : "";
        const safeKey = /^[A-Za-z_$][\w$]*$/.test(key) ? key : JSON.stringify(key);
        const tsType = jsonSchemaToTs(val, currentLexiconId, depth + 1);
        return `${safeKey}${optional}: ${tsType}`;
      });
      return `{ ${props.join("; ")} }`;
    }

    default: return "unknown";
  }
}

// ── Type Extractors ──

function extractInputType(lex) {
  const main = lex.defs?.main;
  if (!main) return "void";
  if (main.type === "query") {
    if (hasProperties(main.parameters)) return jsonSchemaToTs(main.parameters, lex.id);
    return "void";
  }
  if (main.type === "procedure") {
    const s = main.input?.schema;
    if (!s) return "void";
    if (s.type === "ref" || s.type === "union") return jsonSchemaToTs(s, lex.id);
    if (hasProperties(s)) return jsonSchemaToTs(s, lex.id);
    return "void";
  }
  return "void";
}

function extractOutputType(lex) {
  const main = lex.defs?.main;
  if (!main) return "unknown";
  const s = main.output?.schema;
  if (!s) return "unknown";
  if (s.type === "ref" || s.type === "union") return jsonSchemaToTs(s, lex.id);
  if (hasProperties(s)) return jsonSchemaToTs(s, lex.id);
  return "unknown";
}

function extractRecordType(lex) {
  const main = lex.defs?.main;
  if (!main || main.type !== "record") return null;
  const rec = main.record;
  if (!rec) return "Record<string, unknown>";
  return jsonSchemaToTs(rec, lex.id);
}

// ── Helpers ──

function nsidToConstName(nsid) {
  const parts = nsid.split(".");
  return "NSID_" + parts.slice(2).map(p =>
    p
      .replace(/([A-Z])/g, "_$1")
      .replace(/[^A-Za-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .toUpperCase()
  ).join("_");
}

// Collision-aware name resolver. When two NSIDs (e.g. com.etzhayyim.convo.sendMessage
// vs chat.bsky.convo.sendMessage) would produce the same `NSID_*` constant,
// disambiguate by prefixing the namespace segments (com.etzhayyim → AI_etzhayyim,
// chat.bsky → CHAT_BSKY). Emits an explicit error if a 3-way collision arises.
function buildConstNameMap(nsids) {
  const byTail = new Map();
  for (const nsid of nsids) {
    const tail = nsidToConstName(nsid);
    if (!byTail.has(tail)) byTail.set(tail, []);
    byTail.get(tail).push(nsid);
  }
  const final = new Map();
  for (const [tail, group] of byTail) {
    if (group.length === 1) { final.set(group[0], tail); continue; }
    for (const nsid of group) {
      const parts = nsid.split(".");
      const prefix = parts.slice(0, 2).map(p => p.replace(/([A-Z])/g, "_$1").toUpperCase()).join("_");
      const disambiguated = `NSID_${prefix}_` + tail.slice("NSID_".length);
      if ([...final.values()].includes(disambiguated)) {
        throw new Error(`lexicon-registry codegen: unresolved NSID constant collision for ${nsid} (candidate ${disambiguated} already taken)`);
      }
      final.set(nsid, disambiguated);
    }
  }
  return final;
}

function nsidToTypeName(nsid) {
  return nsid.split(".").map(p => p.charAt(0).toUpperCase() + p.slice(1)).join("");
}

// ── Code Generator ──

function generate(lexicons) {
  // Only lexicons with main.type go into typed registries
  const withMain = lexicons.filter(l => l.defs.main?.type);
  const queries = withMain.filter(l => l.defs.main.type === "query");
  const procedures = withMain.filter(l => l.defs.main.type === "procedure");
  const records = withMain.filter(l => l.defs.main.type === "record");

  const lines = [];

  lines.push("// pds-lexicon-registry.gen.ts — Auto-generated typed NSID registry from Lexicon JSON.");
  lines.push("// DO NOT EDIT. Regenerate with: node 70-tools/scripts/contract/gen-pds-lexicon-registry.mjs");
  lines.push("// Lexicon JSON (00-contracts/lexicons/) is the Single Source of Truth.");
  lines.push("// Supports: $ref resolution, union types, record types, cross-namespace refs.");
  lines.push("");

  // ── NSID Literal Types ──
  lines.push("// ── NSID Literal Types ──");
  lines.push("");

  if (queries.length > 0) {
    lines.push("export type LexiconQueryNSID =");
    queries.forEach((q, i) => {
      lines.push(`  ${i === 0 ? "" : "| "}"${q.id}"`);
    });
    lines.push(";");
  } else {
    lines.push("export type LexiconQueryNSID = never;");
  }
  lines.push("");

  if (procedures.length > 0) {
    lines.push("export type LexiconProcedureNSID =");
    procedures.forEach((p, i) => {
      lines.push(`  ${i === 0 ? "" : "| "}"${p.id}"`);
    });
    lines.push(";");
  } else {
    lines.push("export type LexiconProcedureNSID = never;");
  }
  lines.push("");

  lines.push("export type LexiconXrpcNSID = LexiconQueryNSID | LexiconProcedureNSID;");
  lines.push("");

  if (records.length > 0) {
    lines.push("export type LexiconRecordNSID =");
    records.forEach((r, i) => {
      lines.push(`  ${i === 0 ? "" : "| "}"${r.id}"`);
    });
    lines.push(";");
    lines.push("");
  }

  // ── Record Types ──
  lines.push("// ── Record Types (with $ref resolved) ──");
  lines.push("");
  for (const lex of records) {
    const recType = extractRecordType(lex);
    if (recType) {
      const typeName = nsidToTypeName(lex.id) + "Record";
      lines.push(`export type ${typeName} = ${recType};`);
      lines.push("");
    }
  }

  if (records.length > 0) {
    lines.push("export interface RecordTypeMap {");
    records.forEach((lex) => {
      const recType = extractRecordType(lex);
      lines.push(`  "${lex.id}": ${recType || "Record<string, unknown>"};`);
    });
    lines.push("}");
    lines.push("");
    lines.push("export type RecordType<N extends LexiconRecordNSID> =");
    lines.push("  N extends keyof RecordTypeMap ? RecordTypeMap[N] : never;");
    lines.push("");
  }

  // ── Per-NSID Input/Output Types ──
  lines.push("// ── Per-NSID Input/Output Types (with $ref resolved) ──");
  lines.push("");

  const allXrpc = [...queries, ...procedures].sort((a, b) => a.id.localeCompare(b.id));

  lines.push("export interface XrpcInputMap {");
  allXrpc.forEach((lex) => {
    const inputType = extractInputType(lex);
    lines.push(`  "${lex.id}": ${inputType};`);
  });
  lines.push("}");
  lines.push("");

  lines.push("export interface XrpcOutputMap {");
  allXrpc.forEach((lex) => {
    const outputType = extractOutputType(lex);
    lines.push(`  "${lex.id}": ${outputType};`);
  });
  lines.push("}");
  lines.push("");

  lines.push("export type XrpcInput<N extends LexiconXrpcNSID> =");
  lines.push("  N extends keyof XrpcInputMap ? XrpcInputMap[N] : never;");
  lines.push("");

  lines.push("export type XrpcOutput<N extends LexiconXrpcNSID> =");
  lines.push("  N extends keyof XrpcOutputMap ? XrpcOutputMap[N] : never;");
  lines.push("");

  // ── NSID Constants (collision-aware) ──
  lines.push("// ── NSID Constants ──");
  lines.push("");
  const constNames = buildConstNameMap(allXrpc.map(l => l.id));
  for (const lex of allXrpc) {
    lines.push(`export const ${constNames.get(lex.id)} = "${lex.id}" as const;`);
  }
  lines.push("");

  // ── NSID Sets ──
  lines.push("// ── NSID Set (for O(1) membership check) ──");
  lines.push("");
  lines.push("export const LEXICON_QUERY_NSIDS = new Set<LexiconQueryNSID>([");
  for (const q of queries) lines.push(`  "${q.id}",`);
  lines.push("] as const);");
  lines.push("");
  lines.push("export const LEXICON_PROCEDURE_NSIDS = new Set<LexiconProcedureNSID>([");
  for (const p of procedures) lines.push(`  "${p.id}",`);
  lines.push("] as const);");
  lines.push("");
  lines.push("export const LEXICON_ALL_NSIDS = new Set<LexiconXrpcNSID>([");
  lines.push("  ...LEXICON_QUERY_NSIDS,");
  lines.push("  ...LEXICON_PROCEDURE_NSIDS,");
  lines.push("] as const);");
  lines.push("");
  if (records.length > 0) {
    lines.push("export const LEXICON_RECORD_NSIDS = new Set<LexiconRecordNSID>([");
    for (const r of records) lines.push(`  "${r.id}",`);
    lines.push("] as const);");
    lines.push("");
  }

  // ── Type Guards ──
  lines.push("// ── Type Guards ──");
  lines.push("");
  lines.push("export function isLexiconNSID(nsid: string): nsid is LexiconXrpcNSID {");
  lines.push("  return LEXICON_ALL_NSIDS.has(nsid as LexiconXrpcNSID);");
  lines.push("}");
  lines.push("");
  lines.push("export function isLexiconQuery(nsid: string): nsid is LexiconQueryNSID {");
  lines.push("  return LEXICON_QUERY_NSIDS.has(nsid as LexiconQueryNSID);");
  lines.push("}");
  lines.push("");
  lines.push("export function isLexiconProcedure(nsid: string): nsid is LexiconProcedureNSID {");
  lines.push("  return LEXICON_PROCEDURE_NSIDS.has(nsid as LexiconProcedureNSID);");
  lines.push("}");
  lines.push("");
  if (records.length > 0) {
    lines.push("export function isLexiconRecord(nsid: string): nsid is LexiconRecordNSID {");
    lines.push("  return LEXICON_RECORD_NSIDS.has(nsid as LexiconRecordNSID);");
    lines.push("}");
    lines.push("");
  }

  // ── Typed Body Parser ──
  lines.push("// ── Typed Body Parser ──");
  lines.push("");
  lines.push("/**");
  lines.push(" * Type-safe body cast for a known Lexicon NSID.");
  lines.push(" * Usage: const input = parseXrpcBody<\"com.etzhayyim.convo.send\">(body);");
  lines.push(" */");
  lines.push("export function parseXrpcBody<N extends LexiconXrpcNSID>(");
  lines.push("  body: Record<string, unknown>,");
  lines.push("): XrpcInput<N> {");
  lines.push("  return body as XrpcInput<N>;");
  lines.push("}");
  lines.push("");

  // ── Typed Response Builder ──
  lines.push("// ── Typed Response Builder ──");
  lines.push("");
  lines.push("/**");
  lines.push(" * Type-safe response cast for a known Lexicon NSID.");
  lines.push(" * Usage: return typedResponse<\"com.etzhayyim.convo.send\">(data);");
  lines.push(" */");
  lines.push("export function typedResponse<N extends LexiconXrpcNSID>(");
  lines.push("  data: XrpcOutput<N>,");
  lines.push("): XrpcOutput<N> {");
  lines.push("  return data;");
  lines.push("}");
  lines.push("");

  // ── Metadata ──
  lines.push("// ── Lexicon Metadata ──");
  lines.push("");
  lines.push("export interface LexiconMeta {");
  lines.push("  readonly id: string;");
  lines.push("  readonly type: \"query\" | \"procedure\" | \"record\" | \"permission-set\" | \"object\" | \"subscription\";");
  lines.push("  readonly description?: string;");
  lines.push("}");
  lines.push("");
  lines.push("export const LEXICON_META: ReadonlyMap<string, LexiconMeta> = new Map([");
  for (const lex of withMain) {
    const desc = lex.description || lex.defs.main.description;
    const descStr = desc ? `, description: ${JSON.stringify(desc)}` : "";
    lines.push(`  ["${lex.id}", { id: "${lex.id}", type: "${lex.defs.main.type}"${descStr} }],`);
  }
  lines.push("]);");
  lines.push("");

  // ── Runtime schema registry ──
  lines.push("// ── Runtime schema registry (full lexicon JSON, for runtime validation) ──");
  lines.push("");
  lines.push("export const LEXICON_SCHEMA_BY_ID: ReadonlyMap<string, Record<string, unknown>> = new Map([");
  for (const lex of lexicons) {
    lines.push(`  ["${lex.id}", ${JSON.stringify(lex)}],`);
  }
  lines.push("]);");
  lines.push("");

  // ── $ref resolution helpers ──
  lines.push("// ── $ref Resolution Helpers (runtime) ──");
  lines.push("");
  lines.push("/**");
  lines.push(" * Resolve a Lexicon $ref at runtime.");
  lines.push(" * @param ref - e.g. \"com.atproto.label.defs#label\" or \"#localDef\"");
  lines.push(" * @param currentNsid - the NSID of the lexicon containing the ref");
  lines.push(" */");
  lines.push("export function resolveRefSchema(ref: string, currentNsid?: string): Record<string, unknown> | undefined {");
  lines.push("  if (ref.startsWith(\"#\") && currentNsid) {");
  lines.push("    const lex = LEXICON_SCHEMA_BY_ID.get(currentNsid) as { defs?: Record<string, unknown> } | undefined;");
  lines.push("    return (lex?.defs as Record<string, unknown> | undefined)?.[ref.slice(1)] as Record<string, unknown> | undefined;");
  lines.push("  }");
  lines.push("  if (ref.includes(\"#\")) {");
  lines.push("    const [nsid, defName] = ref.split(\"#\");");
  lines.push("    const lex = LEXICON_SCHEMA_BY_ID.get(nsid) as { defs?: Record<string, unknown> } | undefined;");
  lines.push("    return (lex?.defs as Record<string, unknown> | undefined)?.[defName] as Record<string, unknown> | undefined;");
  lines.push("  }");
  lines.push("  const lex = LEXICON_SCHEMA_BY_ID.get(ref) as { defs?: Record<string, unknown> } | undefined;");
  lines.push("  return (lex?.defs as Record<string, unknown> | undefined)?.main as Record<string, unknown> | undefined;");
  lines.push("}");
  lines.push("");

  return lines.join("\n");
}

// ── Client Type Map Generator ──

function generateClientTypes(lexicons) {
  const withMain = lexicons.filter(l => l.defs.main?.type);
  const queries = withMain.filter(l => l.defs.main.type === "query");
  const procedures = withMain.filter(l => l.defs.main.type === "procedure");
  const allXrpc = [...queries, ...procedures].sort((a, b) => a.id.localeCompare(b.id));

  const lines = [];

  lines.push("// lexicon-types.gen.ts — Auto-generated client-side NSID type map from Lexicon JSON.");
  lines.push("// DO NOT EDIT. Regenerate with: node 70-tools/scripts/contract/gen-pds-lexicon-registry.mjs");
  lines.push("// Lexicon JSON (00-contracts/lexicons/) is the Single Source of Truth.");
  lines.push("//");
  lines.push("// This file provides build-time type safety for XRPC client calls:");
  lines.push("//   - NSID literal type (typo → compile error)");
  lines.push("//   - NSID → Input type mapping (wrong field → compile error)");
  lines.push("//   - NSID → Output type mapping (wrong property access → compile error)");
  lines.push("");

  // ── NSID literals ──
  lines.push("/** All valid query NSIDs. */");
  lines.push("export type QueryNSID =");
  queries.forEach((q, i) => lines.push(`  ${i === 0 ? "" : "| "}"${q.id}"`));
  lines.push(";");
  lines.push("");

  lines.push("/** All valid procedure NSIDs. */");
  lines.push("export type ProcedureNSID =");
  procedures.forEach((p, i) => lines.push(`  ${i === 0 ? "" : "| "}"${p.id}"`));
  lines.push(";");
  lines.push("");

  lines.push("/** All valid XRPC NSIDs (query | procedure). */");
  lines.push("export type XrpcNSID = QueryNSID | ProcedureNSID;");
  lines.push("");

  // ── Input type map ──
  lines.push("/** Maps NSID → request params/body type. Build-time enforced. */");
  lines.push("export type InputOf<N extends XrpcNSID> =");
  allXrpc.forEach((lex, i) => {
    const inputType = extractInputType(lex);
    lines.push(`  ${i === 0 ? "" : ": "}N extends "${lex.id}" ? ${inputType}`);
  });
  lines.push("  : never;");
  lines.push("");

  // ── Output type map ──
  lines.push("/** Maps NSID → response type. Build-time enforced. */");
  lines.push("export type OutputOf<N extends XrpcNSID> =");
  allXrpc.forEach((lex, i) => {
    const outputType = extractOutputType(lex);
    lines.push(`  ${i === 0 ? "" : ": "}N extends "${lex.id}" ? ${outputType}`);
  });
  lines.push("  : never;");
  lines.push("");

  // ── Method type map ──
  lines.push("/** Maps NSID → HTTP method. */");
  lines.push("export type MethodOf<N extends XrpcNSID> =");
  lines.push(`  N extends QueryNSID ? "GET"`);
  lines.push(`  : N extends ProcedureNSID ? "POST"`);
  lines.push("  : never;");
  lines.push("");

  return lines.join("\n");
}

// ── Main ──
const lexicons = scanLexicons(LEXICON_DIR);
if (lexicons.length === 0) {
  console.error("No lexicon files found in", LEXICON_DIR);
  process.exit(1);
}

buildDefIndex(lexicons);

const withMain = lexicons.filter(l => l.defs.main?.type);
const queries = withMain.filter(l => l.defs.main.type === "query");
const procedures = withMain.filter(l => l.defs.main.type === "procedure");
const records = withMain.filter(l => l.defs.main.type === "record");
const defsOnly = lexicons.filter(l => !l.defs.main?.type);

const output = generate(lexicons);
const clientOutput = generateClientTypes(lexicons);

console.error(`scanned: ${lexicons.length} lexicons (${defsOnly.length} defs-only for $ref resolution)`);
console.error(`generated: ${withMain.length} typed (${queries.length} query, ${procedures.length} procedure, ${records.length} record)`);
console.error(`def index: ${defIndex.size} resolvable defs`);

if (isDryRun) {
  console.log(output);
} else {
  writeFileSync(OUT_FILE, output, "utf8");
  console.error(`wrote ${OUT_FILE}`);
  writeFileSync(CLIENT_OUT_FILE, clientOutput, "utf8");
  console.error(`wrote ${CLIENT_OUT_FILE}`);
}
