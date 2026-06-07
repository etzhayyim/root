#!/usr/bin/env node
/**
 * R2 → B2 codemod for Cloudflare Worker TS files (tightened scope).
 *
 * Mechanically replaces `<env>.CDN_R2.{get,put,head,delete}(...)` call
 * sites with `b2{Get,Put,Head,Delete}(<env>, ...)` from
 * `@etzhayyim/kotodama-host-sdk`, and adjusts the import block.
 *
 * What this codemod does NOT do (deliberately, because each requires
 * per-Worker judgment):
 *
 *   - Rename `R2Bucket` types to `B2Env`. The same Worker may have
 *     other R2 bindings (TILES, GRAPH_R2, etc.) that are not part of
 *     the CDN_R2 migration scope. Type renames are MANUAL.
 *   - Rewrite `.httpMetadata?.contentType` accessors. The accessed
 *     object may be from another R2 binding still in use. Manual.
 *   - Add `B2_KEY_ID` / `B2_APPLICATION_KEY` env declarations. The
 *     wrangler-side script does that.
 *   - Update wrangler.jsonc, CLAUDE.md, or migrate blob data.
 *
 * The codemod only runs on files containing actual `CDN_R2.{get,put,
 * head,delete}(` call sites — files with only the `R2Bucket` type
 * reference are skipped.
 *
 * Usage:
 *   node 70-tools/scripts/migration/r2-to-b2-codemod.mjs \
 *     --include '60-apps/etzhayyim-project-foo/**\/*.ts' \
 *     --dry-run                # preview only (default)
 *
 *   node 70-tools/scripts/migration/r2-to-b2-codemod.mjs \
 *     --include '60-apps/etzhayyim-project-foo/**\/*.ts' \
 *     --apply                  # write changes
 */
import fs from "node:fs";
import path from "node:path";
import { glob } from "node:fs/promises";

const ROOT = path.resolve(new URL(".", import.meta.url).pathname, "../../..");
const SKIP_DIR = new Set(["node_modules", "_archive", ".git", "target", "dist", "pkg", "build"]);

function shouldSkip(filePath) {
  return filePath.split(path.sep).some((p) => SKIP_DIR.has(p));
}

// Method-call replacements. Each tuple is [regex, replacement, label].
// Order matters: longer patterns (PUT with httpMetadata wrapper) come
// before shorter ones (PUT with no opts).
const METHOD_CALL_REPLACEMENTS = [
  // .head / .get / .delete — single arg, simple replacement.
  [
    /\b(\w+(?:\.\w+)*)\.CDN_R2\.head\s*\(([^)]+)\)/g,
    "b2Head($1, $2)",
    "head",
  ],
  [
    /\b(\w+(?:\.\w+)*)\.CDN_R2\.get\s*\(([^)]+)\)/g,
    "b2Get($1, $2)",
    "get",
  ],
  [
    /\b(\w+(?:\.\w+)*)\.CDN_R2\.delete\s*\(([^)]+)\)/g,
    "b2Delete($1, $2)",
    "delete",
  ],
  // .put with R2-style { httpMetadata: { contentType } } wrapper.
  [
    /\b(\w+(?:\.\w+)*)\.CDN_R2\.put\s*\(([^,]+),\s*([^,]+),\s*\{\s*httpMetadata:\s*\{([^}]+)\}\s*\}\s*\)/g,
    "b2Put($1, $2, $3, {$4})",
    "put-with-meta",
  ],
  // .put with no opts.
  [
    /\b(\w+(?:\.\w+)*)\.CDN_R2\.put\s*\(([^,]+),\s*([^)]+)\)/g,
    "b2Put($1, $2, $3)",
    "put",
  ],
];

// Match `import { ... } from "@etzhayyim/kotodama-host-sdk"` allowing the
// `{ ... }` to span multiple lines.
const IMPORT_PATTERN_HOSTSDK =
  /import\s+\{([\s\S]*?)\}\s+from\s+["']@etzhayyim\/kotodama-host-sdk["']\s*;?/;

function addB2Imports(text) {
  if (/\bb2Get\b/.test(text) && /\bB2Env\b/.test(text)) return text;
  const needsImport = /\bb2(Get|Put|Head|Delete)\b/.test(text) || /\bB2Env\b/.test(text);
  if (!needsImport) return text;

  const m = text.match(IMPORT_PATTERN_HOSTSDK);
  if (m) {
    const inner = m[1];
    const existing = inner.split(/[,\n]/).map((s) => s.trim()).filter((s) => s.length > 0);
    const have = new Set(existing.map((e) => e.replace(/^type\s+/, "")));
    const additions = ["b2Get", "b2Put", "b2Head", "b2Delete"].filter((n) => !have.has(n));
    const typeAdditions = have.has("B2Env") ? [] : ["type B2Env"];
    if (additions.length === 0 && typeAdditions.length === 0) return text;
    const merged = [...existing, ...additions, ...typeAdditions];
    const rebuilt = `import {\n  ${merged.join(",\n  ")},\n} from "@etzhayyim/kotodama-host-sdk";`;
    return text.replace(IMPORT_PATTERN_HOSTSDK, rebuilt);
  }
  return `import { b2Get, b2Put, b2Head, b2Delete, type B2Env } from "@etzhayyim/kotodama-host-sdk";\n${text}`;
}

function transform(text) {
  // Skip files that only have the R2Bucket type but no CDN_R2 call.
  // We deliberately leave those for manual review since the type may
  // belong to a different R2 binding (TILES, GRAPH_R2, etc.).
  if (!/\.CDN_R2\.(get|put|head|delete)\s*\(/.test(text)) {
    return { text, changes: 0 };
  }

  let out = text;
  let changes = 0;
  for (const [pat, repl] of METHOD_CALL_REPLACEMENTS) {
    const before = out;
    out = out.replace(pat, repl);
    if (out !== before) changes++;
  }
  if (changes > 0) {
    out = addB2Imports(out);
  }
  return { text: out, changes };
}

async function* gatherFiles(includes) {
  for (const inc of includes) {
    for await (const p of glob(inc, { cwd: ROOT })) {
      if (shouldSkip(p)) continue;
      if (!p.endsWith(".ts")) continue;
      yield path.resolve(ROOT, p);
    }
  }
}

function parseArgs(argv) {
  const out = { includes: [], dryRun: false, apply: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--include") out.includes.push(argv[++i]);
    else if (a === "--dry-run") out.dryRun = true;
    else if (a === "--apply") out.apply = true;
    else if (a === "--help" || a === "-h") {
      console.error("Usage: r2-to-b2-codemod.mjs --include 'glob' [--apply | --dry-run]");
      process.exit(0);
    }
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.includes.length === 0) {
    console.error("Error: --include <glob> required (one or more times)");
    process.exit(1);
  }
  if (!args.apply && !args.dryRun) args.dryRun = true;

  let totalFiles = 0;
  let touchedFiles = 0;
  let totalChanges = 0;

  for await (const filePath of gatherFiles(args.includes)) {
    totalFiles++;
    const orig = fs.readFileSync(filePath, "utf8");
    if (!/CDN_R2/.test(orig)) continue;
    const { text, changes } = transform(orig);
    if (changes === 0 || text === orig) continue;
    totalChanges += changes;
    touchedFiles++;
    const rel = path.relative(ROOT, filePath);
    if (args.apply) {
      fs.writeFileSync(filePath, text, "utf8");
      console.log(`apply  ${rel} (${changes} call sites)`);
    } else {
      console.log(`dry    ${rel} (${changes} call sites)`);
    }
  }

  console.log(`\nFiles scanned: ${totalFiles}`);
  console.log(`Files touched: ${touchedFiles}`);
  console.log(`Call sites:    ${totalChanges}`);
  console.log(args.apply ? "APPLIED." : "DRY RUN — re-run with --apply to write changes.");

  if (touchedFiles > 0) {
    console.log("\nManual follow-up still required for each touched file:");
    console.log("  - Update wrangler.jsonc (drop r2_buckets, add B2_BUCKET / B2_REGION");
    console.log("    / B2_ENDPOINT vars + B2_KEY_ID / B2_APPLICATION_KEY secrets).");
    console.log("    Use 70-tools/scripts/migration/r2-to-b2-wrangler.mjs.");
    console.log("  - Mirror blob data: aws s3 sync (B2 endpoint, Bandwidth Ally).");
    console.log("  - wrangler secret put B2_KEY_ID / B2_APPLICATION_KEY.");
    console.log("  - Review .httpMetadata?.contentType accessors (B2GetResult.contentType");
    console.log("    is direct, not nested under .httpMetadata).");
    console.log("  - Test + deploy.");
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
