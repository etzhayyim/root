#!/usr/bin/env node
/**
 * Repo-wide Cloudflare edge policy guard.
 *
 * Cloudflare deployables in this repository are edge/BFF surfaces only:
 * - SvelteKit Cloudflare output is the desired appview shape.
 * - Hono worker entries are retired for appviews.
 * - Hyperdrive and DB/business logic belong in k8s pods behind the MCP router.
 *
 * This guard is baseline-backed because the repository still contains legacy
 * workers. It fails on new drift while keeping the migration inventory visible.
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const UPDATE = process.argv.includes("--update-baseline");
const STRICT = process.argv.includes("--strict");
const BASELINE_PATH = "90-docs/rules/cloudflare-edge-bff-policy-baseline.txt";
const SCOPES = ["50-infra/cloudflare/workers", "60-apps"].filter((dir) => fs.existsSync(dir));
const INCLUDE_GLOB = "*.{ts,tsx,js,mjs,cjs,svelte}";
const SOURCE_EXCLUDES = [
  "!**/.git/**",
  "!**/node_modules/**",
  "!**/.svelte-kit/**",
  "!**/.wrangler/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/coverage/**",
  "!**/_app/**",
  "!**/static/assets/**",
  "!**/static/build/**",
  "!**/android/**",
  "!**/ios/**",
  "!**/*.d.ts",
  "!**/*.min.*",
  "!**/*.map",
  "!70-tools/scripts/lint/cloudflare-edge-bff-policy.mjs",
];

const MAIN_RE = /"main"\s*:\s*"([^"]+)"/;
const SVELTEKIT_CF_WORKER_RE = /(?:^|\/)\.?svelte-kit\/cloudflare\/_worker\.js$/;
const COMMENT_LINE_RE = /^\s*(?:\/\/|\*|\/\*)/;
const RULES = [
  {
    id: "hono-import",
    re: /\bfrom\s+["'](?:hono|@hono\/[^"']+)["']|\brequire\(\s*["'](?:hono|@hono\/[^"']+)["']\s*\)/,
  },
  {
    id: "hyperdrive-usage",
    re: /\b(?:HYPERDRIVE|Hyperdrive|hyperdrive)\b/,
  },
  {
    id: "kysely-direct-db",
    re: /\b(?:createKyselyDb|new\s+Kysely|selectFrom|insertInto|updateTable|deleteFrom)\s*\(/,
  },
  {
    id: "pg-direct-db",
    re: /\bfrom\s+["']pg["']|\brequire\(\s*["']pg["']\s*\)|\bnew\s+(?:Pool|Client)\s*\(/,
  },
];

function rgFiles(args) {
  const result = spawnSync("rg", args, {
    encoding: "utf8",
    maxBuffer: 128 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0 && result.status !== 1) {
    throw new Error(`rg failed (code=${result.status}): ${result.stderr?.trim() ?? ""}`);
  }
  const out = result.stdout.trim();
  return out ? out.split("\n").filter(Boolean) : [];
}

function listWranglers() {
  return rgFiles(["--files", "--hidden", "--glob", "wrangler.{json,jsonc}", ...SCOPES]);
}

function listSourceFiles() {
  const args = ["--files", "--hidden", "--glob", INCLUDE_GLOB];
  for (const glob of SOURCE_EXCLUDES) args.push("--glob", glob);
  args.push(...SCOPES);
  return rgFiles(args);
}

function lineNumberAt(text, index) {
  let line = 1;
  for (let i = 0; i < index; i += 1) {
    if (text.charCodeAt(i) === 10) line += 1;
  }
  return line;
}

function addEntry(entries, file, lineNo, rule, text) {
  const trimmed = text.trim().replace(/\s+/g, " ");
  entries.push(`${file}:${lineNo}:${rule}:${trimmed}`);
}

function collectWranglerEntries(entries) {
  for (const file of listWranglers()) {
    const text = fs.readFileSync(file, "utf8");
    const main = MAIN_RE.exec(text)?.[1];
    if (main && !SVELTEKIT_CF_WORKER_RE.test(main)) {
      const index = text.indexOf(main);
      addEntry(entries, file, lineNumberAt(text, index), "wrangler-non-sveltekit-main", `"main": "${main}"`);
    }

    const hyperdriveIndex = text.search(/\bhyperdrive\b/i);
    if (hyperdriveIndex >= 0) {
      const lineNo = lineNumberAt(text, hyperdriveIndex);
      const line = text.split("\n")[lineNo - 1] ?? "";
      addEntry(entries, file, lineNo, "wrangler-hyperdrive-binding", line);
    }
  }
}

function collectSourceEntries(entries) {
  for (const file of listSourceFiles()) {
    const lines = fs.readFileSync(file, "utf8").split("\n");
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      if (!line.trim() || COMMENT_LINE_RE.test(line)) continue;
      for (const rule of RULES) {
        if (rule.re.test(line)) addEntry(entries, file, i + 1, rule.id, line);
      }
    }
  }
}

function collectEntries() {
  const entries = [];
  collectWranglerEntries(entries);
  collectSourceEntries(entries);
  return [...new Set(entries)].sort();
}

function normalizedEntryKey(entry) {
  const match = /^(.*?):\d+:([^:]+):(.*)$/.exec(entry);
  if (!match) return entry;
  const [, file, rule, text] = match;
  return `${file}:${rule}:${text}`;
}

const current = collectEntries();

if (UPDATE) {
  fs.mkdirSync(path.dirname(BASELINE_PATH), { recursive: true });
  fs.writeFileSync(BASELINE_PATH, current.length > 0 ? `${current.join("\n")}\n` : "");
  console.log(`updated baseline: ${BASELINE_PATH} (${current.length} entries)`);
  process.exit(0);
}

const baseline = fs.existsSync(BASELINE_PATH)
  ? fs.readFileSync(BASELINE_PATH, "utf8").split("\n").filter(Boolean)
  : [];
const baselineSet = new Set(baseline.map(normalizedEntryKey));
const currentSet = new Set(current.map(normalizedEntryKey));
const added = current.filter((entry) => !baselineSet.has(normalizedEntryKey(entry)));
const removed = baseline.filter((entry) => !currentSet.has(normalizedEntryKey(entry)));

if (STRICT && current.length > 0) {
  console.error("Cloudflare edge/BFF policy violations detected in strict mode:");
  for (const entry of current.slice(0, 200)) console.error(`  ${entry}`);
  if (current.length > 200) console.error(`  ...and ${current.length - 200} more`);
  process.exit(1);
}

if (added.length > 0) {
  console.error("New Cloudflare edge/BFF policy drift detected:");
  for (const entry of added.slice(0, 200)) console.error(`  ${entry}`);
  if (added.length > 200) console.error(`  ...and ${added.length - 200} more`);
  console.error("");
  console.error("Cloudflare must stay edge-only: SvelteKit BFF, no Hono appview, no Hyperdrive/DB logic.");
  console.error("Move business logic and DB access into k8s pods behind the agentgateway MCP router.");
  console.error("If this is an intentional legacy inventory change, run:");
  console.error("  pnpm lint:cloudflare:edge-bff:update");
  process.exit(1);
}

console.log(
  `lint:cloudflare:edge-bff ok (current=${current.length}, baseline=${baseline.length}, removed=${removed.length})`,
);
