#!/usr/bin/env node
// ADR-2605111200 Phase 1.5 — infra Worker wrangler.jsonc に hyperdrive binding を一時 revert。
// ADR-2605111300 (PDS-to-pod migration) が完了するまで、infra Workers (PDS / AppView / graph 等)
// は HYPERDRIVE を維持する。app-actor Worker (60-apps/) には binding を戻さない。
//
// Usage: node 70-tools/scripts/migrations/2605111300-revert-infra-hyperdrive-binding.mjs

import { readFileSync, writeFileSync } from "node:fs";
import { execSync } from "node:child_process";

const repoRoot = execSync("git rev-parse --show-toplevel", { encoding: "utf8" }).trim();

// Workers that currently use createKyselyDb / env.HYPERDRIVE in src/ — restore their binding.
const INFRA_WORKERS = [
  "50-infra/cloudflare/workers/atproto",
  "50-infra/cloudflare/workers/appview",
  "50-infra/cloudflare/workers/graph",
  "50-infra/cloudflare/workers/chat",
  "50-infra/cloudflare/workers/signal",
  "50-infra/cloudflare/workers/kotodama",
  "50-infra/cloudflare/workers/murakumo",
  "50-infra/cloudflare/workers/claim-consumer",
  "50-infra/cloudflare/workers/comfyui",
  "50-infra/cloudflare/workers/gameka-playtest-shell",
  "50-infra/cloudflare/workers/actor-resolver",
  "50-infra/cloudflare/workers/pds-tail-archiver",
];

const BINDING_BLOCK = `  "hyperdrive": [
    { "binding": "HYPERDRIVE", "id": "e84c0a2babe44fc7b74818e394b4b896" }
  ],`;

let touched = 0;
let skipped = 0;

for (const dir of INFRA_WORKERS) {
  const path = `${repoRoot}/${dir}/wrangler.jsonc`;
  let src;
  try {
    src = readFileSync(path, "utf8");
  } catch (e) {
    console.log(`skip (no wrangler.jsonc): ${dir}`);
    skipped += 1;
    continue;
  }

  if (/"hyperdrive"\s*:/.test(src)) {
    console.log(`already-present: ${dir}`);
    skipped += 1;
    continue;
  }

  // Insert hyperdrive block right after the opening `{` (top of object).
  const out = src.replace(/^\{(\s*\n)/, `{$1${BINDING_BLOCK}\n`);

  if (out === src) {
    console.log(`could-not-insert: ${dir}`);
    skipped += 1;
    continue;
  }

  writeFileSync(path, out);
  touched += 1;
  console.log(`reverted: ${dir}`);
}

console.log(`\nDone. reverted=${touched} skipped=${skipped} total=${INFRA_WORKERS.length}`);
