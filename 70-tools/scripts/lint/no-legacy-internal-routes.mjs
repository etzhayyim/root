#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";

const EXCLUDE_GLOBS = [
  "!.git",
  "!**/node_modules/**",
  "!**/.svelte-kit/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/coverage/**",
  "!**/out/**",
  "!**/.out/**",
  "!**/.wrangler-out/**",
  "!**/_app/immutable/**",
  "!**/playwright-report/**",
  "!**/project.inlang/cache/**",
  "!**/*.min.*",
  "!**/*.map",
  "!**/_bundled_worker.mjs",
  "!pnpm-lock.yaml",
];

const RULES = [
  {
    id: "sync-serve",
    re: /^\s*sdk\.app\.serve\(\)\s*;?\s*$/g,
    message: "legacy sync serve() call",
  },
  {
    id: "legacy-register-call",
    re: /\b(?:this\.host|host(?:Imports)?)\.(?:identityRegister|capabilityDeclare|governanceRegisterManifest|agentRegisterTools)\(/g,
    message: "legacy host-import registration call",
  },
  {
    id: "legacy-internal-route",
    re: /(?:https:\/\/pds\.internal\/(?:internal|_internal)\/|http:\/\/pds\/internal\/|\/internal\/(?:query|yata\/query|identity\/register|capability\/declare|governance\/manifest|agent\/register-tools|batch-flush))\b/g,
    message: "legacy PDS /internal/* route usage",
  },
  {
    id: "legacy-registration-nsid-call",
    re: /\b(?:xrpc|rpc)\(\s*["']com\.etzhayyim\.(?:identity\.register|capability\.declare|agent\.registerTools)["']/g,
    message: "forbidden legacy internal registration NSID call",
  },
];

function listFiles() {
  const args = ["--files", "--hidden"];
  for (const glob of EXCLUDE_GLOBS) args.push("--glob", glob);
  args.push("--glob", "*.{ts,tsx,js,mjs,cjs,svelte}");

  const result = spawnSync("rg", args, {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`rg --files failed (code=${result.status}): ${result.stderr?.trim() ?? ""}`);
  }
  const out = result.stdout.trim();
  return out ? out.split("\n").filter(Boolean) : [];
}

function collectViolations() {
  const out = [];
  for (const file of listFiles()) {
    if (file.endsWith("/_bundled_worker.mjs")) continue;
    if (file.includes("/.out/") || file.includes("/.wrangler-out/")) continue;
    const text = fs.readFileSync(file, "utf8");
    const lines = text.split("\n");
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (trimmed.startsWith("//") || trimmed.startsWith("*") || trimmed.startsWith("/*")) continue;
      for (const rule of RULES) {
        if (rule.id === "legacy-registration-nsid-call" && file.includes(".generated.")) continue;
        rule.re.lastIndex = 0;
        if (!rule.re.test(line)) continue;
        out.push(`${file}:${i + 1}:${rule.id}:${rule.message}: ${trimmed}`);
      }
    }
  }
  return [...new Set(out)].sort();
}

const violations = collectViolations();
if (violations.length > 0) {
  console.error("ERROR: legacy internal route patterns detected:");
  for (const v of violations.slice(0, 200)) console.error(`  ${v}`);
  if (violations.length > 200) console.error(`  ...and ${violations.length - 200} more`);
  process.exit(1);
}

console.log("lint:legacy-internal ok");
