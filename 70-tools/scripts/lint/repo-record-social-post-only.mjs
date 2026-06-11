#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";

const SEARCH_ROOTS = [
  "20-actors",
  "30-graph/graph-schema/migrations",
  "50-infra",
  "60-apps",
  "70-tools/scripts/contract",
].filter((dir) => fs.existsSync(dir));

const INCLUDE_GLOB = "*.{py,ts,tsx,js,mjs,cjs,svelte,go,sh,yaml,yml}";
const EXCLUDE_GLOBS = [
  "!**/.git/**",
  "!**/node_modules/**",
  "!**/__pycache__/**",
  "!**/.svelte-kit/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/coverage/**",
  "!**/.wrangler-out/**",
  "!**/*.test.*",
  "!**/test/**",
  "!**/tests/**",
];

const DIRECT_WRITE_RE = /\b(?:INSERT\s+INTO\s+vertex_repo_record|insertInto\s*\(\s*["']vertex_repo_record["'])\b/gi;
const WRITE_ALLOWLIST_RE = /\bwrite(?:_table_)?TableAllowlist\b[^\n]*\bvertex_repo_record\b|\bwrite_table_allowlist\b[^\n]*\bvertex_repo_record\b|\bwriteTableAllowlist\s*=\s*\[[\s\S]*?\]/gi;
const POST_COLLECTION_RE = /\bapp\.bsky\.feed\.post\b/;
const MIRROR_GUARD_RE = /\bshouldMirrorToRepoRecord\b|\bPOST_COLLECTION must be app\.bsky\.feed\.post\b|\bvertex_repo_record is reserved for social posts\b/;
const ALLOWLIST_CLEANUP_RE = /\bgov_repo_record_allowlist_cleanup\b|\bremove[s]?\s+vertex_repo_record\b|\barray_remove\b[\s\S]{0,80}\bvertex_repo_record\b/i;

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

function contextAround(lines, lineNo, radius = 80) {
  const start = Math.max(0, lineNo - radius - 1);
  const end = Math.min(lines.length, lineNo + radius);
  return lines.slice(start, end).join("\n");
}

function isAllowedContext(context) {
  if (ALLOWLIST_CLEANUP_RE.test(context)) return true;
  return POST_COLLECTION_RE.test(context) && (MIRROR_GUARD_RE.test(context) || /collection\s*[!=]=+|POST_COLLECTION|app\.bsky\.feed\.post/.test(context));
}

function collectViolations() {
  const violations = [];
  for (const file of listFiles()) {
    if (file === "70-tools/scripts/lint/repo-record-social-post-only.mjs") continue;
    const text = fs.readFileSync(file, "utf8");
    const lines = text.split("\n");
    for (const re of [DIRECT_WRITE_RE, WRITE_ALLOWLIST_RE]) {
      re.lastIndex = 0;
      let match;
      while ((match = re.exec(text)) !== null) {
        if (re === WRITE_ALLOWLIST_RE && !match[0].includes("vertex_repo_record")) continue;
        const lineNo = lineNumberAt(text, match.index);
        const context = contextAround(lines, lineNo);
        if (isAllowedContext(context)) continue;
        violations.push(`${file}:${lineNo}: ${lines[lineNo - 1]?.trim() ?? match[0]}`);
      }
    }
  }
  return violations.sort();
}

const violations = collectViolations();
if (violations.length > 0) {
  console.error("repo-record-social-post-only: vertex_repo_record direct writes must be app.bsky.feed.post guarded.");
  console.error("Route profile/follow/like/cohort/domain state to typed vertex_/edge_ tables instead.");
  for (const v of violations.slice(0, 200)) console.error(`  ${v}`);
  if (violations.length > 200) console.error(`  ...and ${violations.length - 200} more`);
  process.exit(1);
}

console.log("repo-record-social-post-only: OK");
