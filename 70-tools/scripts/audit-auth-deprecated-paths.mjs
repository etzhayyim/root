#!/usr/bin/env node
// ADR-0022 Step 7 evidence collector — ADR-0024 Step 1 prerequisite.
//
// Purpose: verify zero-traffic on the PDS auth deprecation channels before we
// delete the Cookie fallback / AUTH_SERVICE delegation code in verify.ts and
// before we narrow auth.etzhayyim.com route patterns (ADR-0024 Step 2).
//
// Tracked channels (emitted by `logDeprecatedAuthPath()` in
// 50-infra/cloudflare/workers/atproto/src/auth/verify.ts):
//   - cookie-fallback           (etzhayyim_session Cookie → Bearer 昇格)
//   - auth-service-delegation   (AUTH_SERVICE.fetch session 昇格)
//   - parse-jwt-payload-unsafe  (HS256 unsafe payload trust; already removed)
//
// Modes:
//   1) --tail                  Live `wrangler tail` JSON stream, classify in-flight.
//   2) --logpush <ndjson>       Cloudflare Logpush ndjson export file.
//
// Pass criteria (release gate): **zero** hits across a full release cycle
// (per ADR-0022 Step 7 acceptance note, deps.toml L8811-8823).
//
// Usage:
//   node 70-tools/scripts/audit-auth-deprecated-paths.mjs --tail
//   node 70-tools/scripts/audit-auth-deprecated-paths.mjs --logpush ./logs.ndjson
//   WRANGLER_WORKER=etzhayyim-pds node ... --tail

import { spawn } from "node:child_process";
import { createReadStream } from "node:fs";
import { createInterface } from "node:readline";
import { argv, exit, stderr, stdout } from "node:process";

const CHANNELS = new Set([
  "cookie-fallback",
  "auth-service-delegation",
  "parse-jwt-payload-unsafe",
]);
const TAG = "[auth][deprecated]";

function parseArgs() {
  const args = argv.slice(2);
  const opts = { mode: null, file: null };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === "--tail") opts.mode = "tail";
    else if (a === "--logpush") { opts.mode = "logpush"; opts.file = args[++i]; }
    else if (a === "--help" || a === "-h") { printHelp(); exit(0); }
  }
  if (!opts.mode) { printHelp(); exit(2); }
  if (opts.mode === "logpush" && !opts.file) {
    stderr.write("--logpush requires a path\n"); exit(2);
  }
  return opts;
}

function printHelp() {
  stdout.write(`audit-auth-deprecated-paths — ADR-0022 Step 7 evidence

  --tail                  Stream wrangler tail (Worker: WRANGLER_WORKER env, default etzhayyim-pds)
  --logpush <ndjson>      Analyze a Cloudflare Logpush ndjson export

Exit code 0 = zero hits (gate PASS). Non-zero = hits found (gate FAIL).
`);
}

const counts = Object.create(null);
for (const c of CHANNELS) counts[c] = 0;
const samples = [];

function recordLine(rawLine) {
  if (!rawLine.includes(TAG)) return;
  let payload = null;
  try {
    const obj = JSON.parse(rawLine);
    payload = obj;
  } catch {
    // wrangler tail non-JSON line; fall back to regex
  }
  const message = typeof payload?.message === "string" ? payload.message : rawLine;
  const channelMatch = /channel=([a-z-]+)/.exec(message);
  if (!channelMatch) return;
  const channel = channelMatch[1];
  if (!CHANNELS.has(channel)) return;
  counts[channel]++;
  if (samples.length < 10) {
    samples.push({ channel, message: message.slice(0, 500) });
  }
}

async function runTail() {
  const worker = process.env.WRANGLER_WORKER || "etzhayyim-pds";
  stderr.write(`tailing worker=${worker} (Ctrl-C to stop)\n`);
  const child = spawn("wrangler", ["tail", worker, "--format=json"], { stdio: ["ignore", "pipe", "inherit"] });
  const rl = createInterface({ input: child.stdout });
  rl.on("line", recordLine);
  return new Promise((resolve) => {
    child.on("exit", (code) => resolve(code ?? 0));
    process.on("SIGINT", () => { child.kill("SIGINT"); });
  });
}

async function runLogpush(path) {
  const rl = createInterface({ input: createReadStream(path) });
  for await (const line of rl) recordLine(line);
  return 0;
}

function report() {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  stdout.write(JSON.stringify({
    tag: TAG,
    total_hits: total,
    counts,
    samples,
    gate: total === 0 ? "PASS" : "FAIL",
  }, null, 2) + "\n");
  return total === 0 ? 0 : 1;
}

(async () => {
  const opts = parseArgs();
  if (opts.mode === "tail") await runTail();
  else if (opts.mode === "logpush") await runLogpush(opts.file);
  exit(report());
})();
