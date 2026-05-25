#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";

const SEARCH_ROOTS = [
  "00-contracts",
  "10-protocol",
  "20-actors",
  "30-graph",
  "50-infra",
  "60-apps",
  "70-tools",
  "infra",
].filter((dir) => fs.existsSync(dir));

const INCLUDE_GLOB = "*.{json,jsonc,jsonld,toml,ts,tsx,js,mjs,cjs,svelte,py,go,sh,yml,yaml}";
const EXCLUDE_GLOBS = [
  "!**/.git/**",
  "!**/node_modules/**",
  "!**/.svelte-kit/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/coverage/**",
  "!**/.wrangler/**",
  "!**/.wrangler-out/**",
  "!**/static/**",
  "!**/public/**",
  "!**/*.gen.*",
  "!**/generated/**",
  "!**/_registry/**",
  "!**/data/**",
  "!90-docs/**",
  "!80-data/**",
  "!70-tools/scripts/lint/no-two-stage-gftd-domains.mjs",
];

const HOST_RE = /(?:did:web:|https?:\/\/|["'`\s(])([a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+\.gftd\.ai)(?=[/:*"'`\s),}]|$)/gi;

function listFiles() {
  const args = ["--files", "--hidden", "--glob", INCLUDE_GLOB];
  for (const glob of EXCLUDE_GLOBS) args.push("--glob", glob);
  args.push(...SEARCH_ROOTS);
  const result = spawnSync("rg", args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`rg --files failed (code=${result.status}): ${result.stderr?.trim() ?? ""}`);
  }
  return result.stdout.trim().split("\n").filter(Boolean);
}

function lineNumberAt(text, index) {
  let line = 1;
  for (let i = 0; i < index; i += 1) {
    if (text.charCodeAt(i) === 10) line += 1;
  }
  return line;
}

function isForbiddenetzhayyimHost(host) {
  const lower = host.toLowerCase();
  if (!lower.endsWith(".etzhayyim.com")) return false;
  const labels = lower.slice(0, -".etzhayyim.com".length).split(".").filter(Boolean);
  return labels.length > 1;
}

function suggestedHost(host) {
  return `${host.slice(0, -".etzhayyim.com".length).replaceAll(".", "-")}.etzhayyim.com`;
}

const violations = [];
for (const file of listFiles()) {
  const text = fs.readFileSync(file, "utf8");
  const lines = text.split("\n");
  HOST_RE.lastIndex = 0;
  let match;
  while ((match = HOST_RE.exec(text)) !== null) {
    const host = match[1];
    if (!host || !isForbiddenetzhayyimHost(host)) continue;
    const line = lineNumberAt(text, match.index);
    violations.push({
      file,
      line,
      host,
      suggestion: suggestedHost(host),
      text: (lines[line - 1] ?? "").trim(),
    });
  }
}

const unique = [...new Map(
  violations.map((v) => [`${v.file}:${v.line}:${v.host}`, v]),
).values()].sort((a, b) => `${a.file}:${a.line}:${a.host}`.localeCompare(`${b.file}:${b.line}:${b.host}`));

if (process.argv.includes("--json")) {
  console.log(JSON.stringify(unique, null, 2));
  process.exit(unique.length > 0 ? 1 : 0);
}

if (unique.length > 0) {
  const hosts = [...new Map(unique.map((v) => [v.host, v.suggestion])).entries()]
    .sort(([a], [b]) => a.localeCompare(b));
  console.error("lint:no-two-stage-gftd-domains failed");
  console.error("etzhayyim public domains must use exactly one label before etzhayyim.com.");
  console.error("Use hyphenated single-label hosts, e.g. ind-state.etzhayyim.com, not ind.state.etzhayyim.com.\n");
  console.error(`Forbidden hosts (${hosts.length}):`);
  for (const [host, suggestion] of hosts.slice(0, 120)) {
    console.error(`  ${host} -> ${suggestion}`);
  }
  if (hosts.length > 120) console.error(`  ...and ${hosts.length - 120} more hosts`);
  console.error(`\nOccurrences (${unique.length}):`);
  for (const v of unique.slice(0, 200)) {
    console.error(`  ${v.file}:${v.line}: ${v.host} -> ${v.suggestion}`);
  }
  if (unique.length > 200) console.error(`  ...and ${unique.length - 200} more occurrences`);
  process.exit(1);
}

console.log("lint:no-two-stage-gftd-domains ok");
