#!/usr/bin/env node

/**
 * gen-permission-scope-client.mjs — Lexicon JSON (type: "permission-set") → typed scope client
 *
 * Generates `permission-scope-client.gen.ts` for type-safe OAuth scope building.
 * Lexicon JSON (00-contracts/lexicons/) is the Single Source of Truth.
 *
 * Usage:
 *   node gen-permission-scope-client.mjs              # generate
 *   node gen-permission-scope-client.mjs --dry-run    # print to stdout
 */

import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const LEXICON_DIR = path.join(ROOT, "00-contracts/lexicons");
const OUT_FILE = path.join(ROOT, "10-protocol/wproto/src/permission-scope-client.gen.ts");

const isDryRun = process.argv.includes("--dry-run");

function scanPermissionSets(dir) {
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
          if (json.lexicon === 1 && json.defs?.main?.type === "permission-set") {
            results.push(json);
          }
        } catch { /* skip */ }
      }
    }
  }
  walk(dir);
  return results.sort((a, b) => a.id.localeCompare(b.id));
}

function nsidToConstName(nsid) {
  const parts = nsid.split(".");
  return parts
    .slice(2)
    .map((p) => p.replace(/([A-Z])/g, "_$1").toUpperCase())
    .join("_");
}

function nsidToVarName(nsid) {
  const parts = nsid.split(".");
  const last = parts[parts.length - 1];
  return last[0].toLowerCase() + last.slice(1);
}

function generate(permSets) {
  const L = [];

  L.push("// permission-scope-client.gen.ts — Auto-generated typed OAuth scope client from Lexicon JSON.");
  L.push("// DO NOT EDIT. Regenerate with: node 70-tools/scripts/contract/gen-permission-scope-client.mjs");
  L.push("// Lexicon JSON (00-contracts/lexicons/) is the Single Source of Truth.");
  L.push("");

  // ── NSID literal union ──
  L.push("// ── Permission Set NSID Literal Types ──");
  L.push("");
  L.push("export type PermissionSetNSID =");
  permSets.forEach((ps, i) => {
    L.push(`  ${i === 0 ? "" : "| "}"${ps.id}"`);
  });
  L.push(";");
  L.push("");

  // ── NSID constants ──
  L.push("// ── NSID Constants ──");
  L.push("");
  for (const ps of permSets) {
    L.push(`export const ${nsidToConstName(ps.id)} = "${ps.id}" as const;`);
  }
  L.push("");

  // ── Permission resource types ──
  L.push("// ── Permission Types ──");
  L.push("");
  L.push("export interface PermissionDef {");
  L.push("  readonly resource: \"repo\" | \"rpc\";");
  L.push("  readonly collection?: readonly string[];");
  L.push("  readonly action?: readonly string[];");
  L.push("  readonly lxm?: readonly string[];");
  L.push("}");
  L.push("");
  L.push("export interface PermissionSetMeta {");
  L.push("  readonly id: PermissionSetNSID;");
  L.push("  readonly title: string;");
  L.push("  readonly detail: string;");
  L.push("  readonly titleLang?: Readonly<Record<string, string>>;");
  L.push("  readonly detailLang?: Readonly<Record<string, string>>;");
  L.push("  readonly permissions: readonly PermissionDef[];");
  L.push("}");
  L.push("");

  // ── Registry ──
  L.push("// ── Permission Set Registry (from Lexicon JSON) ──");
  L.push("");
  L.push("export const PERMISSION_SET_REGISTRY: ReadonlyMap<PermissionSetNSID, PermissionSetMeta> = new Map<PermissionSetNSID, PermissionSetMeta>([");
  for (const ps of permSets) {
    const main = ps.defs.main;
    const perms = (main.permissions || []).map((p) => {
      const parts = [`resource: "${p.resource}"`];
      if (p.collection) parts.push(`collection: ${JSON.stringify(p.collection)}`);
      if (p.action) parts.push(`action: ${JSON.stringify(p.action)}`);
      if (p.lxm) parts.push(`lxm: ${JSON.stringify(p.lxm)}`);
      return `{ ${parts.join(", ")} }`;
    });
    const titleLang = main["title:lang"];
    const detailLang = main["detail:lang"];
    L.push(`  ["${ps.id}", {`);
    L.push(`    id: "${ps.id}",`);
    L.push(`    title: ${JSON.stringify(main.title)},`);
    L.push(`    detail: ${JSON.stringify(main.detail)},`);
    if (titleLang) L.push(`    titleLang: ${JSON.stringify(titleLang)},`);
    if (detailLang) L.push(`    detailLang: ${JSON.stringify(detailLang)},`);
    L.push(`    permissions: [${perms.join(", ")}],`);
    L.push(`  }],`);
  }
  L.push("]);");
  L.push("");

  // ── Type-safe scope builder ──
  L.push("// ── Type-safe OAuth Scope Builder ──");
  L.push("");
  L.push("export class ScopeBuilder {");
  L.push("  private readonly scopes = new Set<string>();");
  L.push("");
  L.push("  constructor() {");
  L.push('    this.scopes.add("atproto");');
  L.push("  }");
  L.push("");
  L.push("  /** Include a permission set by NSID (type-safe: only valid IDs accepted). */");
  L.push("  include(id: PermissionSetNSID): this {");
  L.push("    this.scopes.add(`include:${id}`);");
  L.push("    return this;");
  L.push("  }");
  L.push("");
  L.push('  /** Add transition:chat.bsky scope for Bluesky DM. */');
  L.push("  chat(): this {");
  L.push('    this.scopes.add("transition:chat.bsky");');
  L.push("    return this;");
  L.push("  }");
  L.push("");
  L.push('  /** Add transition:generic scope. */');
  L.push("  generic(): this {");
  L.push('    this.scopes.add("transition:generic");');
  L.push("    return this;");
  L.push("  }");
  L.push("");
  L.push("  /** Add a standalone resource scope (blob/account/identity). */");
  L.push("  resource(scope: `blob${string}` | `account${string}` | `identity${string}`): this {");
  L.push("    this.scopes.add(scope);");
  L.push("    return this;");
  L.push("  }");
  L.push("");
  L.push("  /** Build the OAuth scope string. */");
  L.push("  build(): string {");
  L.push("    return [...this.scopes].join(\" \");");
  L.push("  }");
  L.push("");
  L.push("  /** Get the scope set for inspection. */");
  L.push("  toSet(): ReadonlySet<string> {");
  L.push("    return new Set(this.scopes);");
  L.push("  }");
  L.push("}");
  L.push("");

  // ── Convenience factory ──
  L.push("/** Create a new type-safe scope builder. */");
  L.push("export function scopeBuilder(): ScopeBuilder {");
  L.push("  return new ScopeBuilder();");
  L.push("}");
  L.push("");

  // ── Pre-built scope strings ──
  L.push("// ── Pre-built Scope Strings (for common patterns) ──");
  L.push("");
  for (const ps of permSets) {
    const varName = nsidToVarName(ps.id);
    L.push(`/** include:${ps.id} — ${ps.defs.main.title} */`);
    L.push(`export const SCOPE_${nsidToConstName(ps.id)} = "include:${ps.id}" as const;`);
  }
  L.push("");

  // ── Type guard ──
  L.push("// ── Type Guards ──");
  L.push("");
  L.push("const _ALL_IDS = new Set<string>(PERMISSION_SET_REGISTRY.keys());");
  L.push("");
  L.push("export function isPermissionSetNSID(s: string): s is PermissionSetNSID {");
  L.push("  return _ALL_IDS.has(s);");
  L.push("}");
  L.push("");
  L.push("/** Extract permission set NSID from an include: scope string. */");
  L.push('export function parseIncludeScope(scope: string): PermissionSetNSID | null {');
  L.push('  if (!scope.startsWith("include:")) return null;');
  L.push('  const id = scope.slice("include:".length);');
  L.push("  return isPermissionSetNSID(id) ? id : null;");
  L.push("}");
  L.push("");

  // ── Utility: check if a method is covered by a permission set ──
  L.push("// ── Method Coverage Check ──");
  L.push("");
  L.push("/** Check if an XRPC method NSID is covered by a permission set's lxm patterns. */");
  L.push("export function permissionSetCoversMethod(setId: PermissionSetNSID, method: string): boolean {");
  L.push("  const meta = PERMISSION_SET_REGISTRY.get(setId);");
  L.push("  if (!meta) return false;");
  L.push("  for (const perm of meta.permissions) {");
  L.push('    if (perm.resource !== "rpc") continue;');
  L.push("    for (const lxm of perm.lxm ?? []) {");
  L.push("      if (lxm === method) return true;");
  L.push('      if (lxm.endsWith(".*") && method.startsWith(lxm.slice(0, -1))) return true;');
  L.push("    }");
  L.push("  }");
  L.push("  return false;");
  L.push("}");
  L.push("");

  return L.join("\n");
}

// ── Main ──

const permSets = scanPermissionSets(LEXICON_DIR);
if (permSets.length === 0) {
  console.error("No permission-set lexicon files found in", LEXICON_DIR);
  process.exit(1);
}

const output = generate(permSets);
console.log(`generated permission scope client: ${permSets.length} permission sets`);

if (isDryRun) {
  console.log(output);
} else {
  writeFileSync(OUT_FILE, output, "utf8");
  console.log(`wrote ${OUT_FILE}`);
}
