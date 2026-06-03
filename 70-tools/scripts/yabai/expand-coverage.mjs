#!/usr/bin/env node
// Thin driver for yabai coverage expansion.
//
// Calls two BPMN actors (reverseIpLookup + crtshFuzzySearch) to discover
// sibling phishing domain candidates. Replaces the all-in-one
// 60-apps/etzhayyim-project-yabai/tools/track-phishing-infra/expand-coverage.mjs
// which did the same work inline (curl + psql). BPMNs handle HTTP fetch +
// audit trail; this driver filters (brand keywords, known-dedup) + writes
// candidates TSV.
//
// Usage:
//   node 70-tools/scripts/yabai/expand-coverage.mjs [--limit-ips 20]
//
// Env:
//   DISPATCHER_URL  (default https://dispatcher.etzhayyim.com)
//   RW_URL          (default $(security find-generic-password -s etzhayyim.rw -a ROOT_URL -w))

import { spawn, spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const LIMIT_IPS = parseInt(process.argv[process.argv.indexOf("--limit-ips") + 1] ?? "20", 10);
const DISPATCHER = (process.env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/$/, "");

const BRAND_KEYWORDS = ["whatsapp", "whtaspp", "whatsp", "whatsup", "line.me", "line-me",
                        "mastercard", "mastercar", "mastecard", "mstaercard", "mstr",
                        "apple", "aplle", "smbc", "sumitomo"];
const FUZZY_TERMS = ["whtaspp", "whatsp", "mastecard", "mstaer", "line-me"];

function sh(cmd, args, opts = {}) {
  return new Promise((resolve) => {
    const p = spawn(cmd, args, { stdio: ["ignore", "pipe", "pipe"] });
    let out = "", err = "";
    const t = setTimeout(() => p.kill("SIGKILL"), opts.timeoutMs ?? 15000);
    p.stdout.on("data", (b) => (out += b));
    p.stderr.on("data", (b) => (err += b));
    p.on("close", (c) => { clearTimeout(t); resolve({ code: c ?? -1, stdout: out, stderr: err }); });
  });
}

function rwUrl() {
  if (process.env.RW_URL) return process.env.RW_URL;
  const r = spawnSync("security", ["find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"]);
  return r.stdout.toString().trim();
}

async function psqlQuery(sql) {
  const r = await sh("psql", [rwUrl(), "-tA", "-F", "\t", "-c", sql], { timeoutMs: 30000 });
  if (r.code !== 0) throw new Error("psql: " + r.stderr);
  return r.stdout.trim();
}

async function xrpc(nsid, body) {
  const r = await sh("curl", [
    "-sS", "--max-time", "30",
    "-X", "POST", `${DISPATCHER}/xrpc/${nsid}`,
    "-H", "Content-Type: application/json",
    "-d", JSON.stringify(body),
  ], { timeoutMs: 35000 });
  if (r.code !== 0) throw new Error(`xrpc ${nsid}: ${r.stderr}`);
  try { return JSON.parse(r.stdout); } catch { throw new Error(`xrpc ${nsid}: bad JSON: ${r.stdout.slice(0, 200)}`); }
}

function brandMatch(domain) {
  const d = domain.toLowerCase();
  return BRAND_KEYWORDS.some((k) => d.includes(k));
}

async function main() {
  const known = new Set((await psqlQuery(
    "SELECT domain FROM vertex_yabai_infra_track WHERE domain IS NOT NULL"
  )).split("\n").filter(Boolean));

  const ips = (await psqlQuery(
    `SELECT DISTINCT resolved_ip FROM vertex_yabai_infra_track
     WHERE resolved_ip IS NOT NULL ORDER BY resolved_ip LIMIT ${LIMIT_IPS}`
  )).split("\n").filter(Boolean);

  console.error(`# known phishing domains: ${known.size}`);
  console.error(`# pivot IPs:              ${ips.length}`);

  const candidates = new Map(); // domain → source

  // Reverse-IP leg
  for (const ip of ips) {
    let siblings = [];
    try {
      const r = await xrpc("com.etzhayyim.apps.yabai.reverseIpLookup", { ip });
      siblings = r?.variables?.siblings ?? [];
      if (r?.variables?.rateLimited) console.error(`  ${ip}: rate-limited`);
    } catch (e) { console.error(`  ${ip}: ${e.message}`); }
    const fresh = siblings.filter((d) => !known.has(d) && brandMatch(d));
    for (const d of fresh) {
      if (!candidates.has(d)) candidates.set(d, `revip:${ip}`);
    }
    console.error(`  ${ip}: ${siblings.length} siblings, ${fresh.length} brand-match`);
    await new Promise((r) => setTimeout(r, 1500));
  }

  // crt.sh fuzzy leg
  for (const kw of FUZZY_TERMS) {
    let hits = [];
    try {
      const r = await xrpc("com.etzhayyim.apps.yabai.crtshFuzzySearch", { keyword: kw });
      hits = r?.variables?.siblings ?? [];
    } catch (e) { console.error(`  crt.sh ${kw}: ${e.message}`); }
    const fresh = hits.filter((d) => !known.has(d) && brandMatch(d) && !d.includes(".arpa") && !d.includes(" "));
    for (const d of fresh) {
      if (!candidates.has(d)) candidates.set(d, `crtsh:${kw}`);
    }
    console.error(`  crt.sh ${kw}: ${hits.length} hits, ${fresh.length} brand-match fresh`);
    await new Promise((r) => setTimeout(r, 2000));
  }

  const sorted = [...candidates.entries()].sort(([a], [b]) => a.localeCompare(b));
  const outFile = "/tmp/yabai-coverage-candidates.tsv";
  writeFileSync(outFile, ["domain\tsource", ...sorted.map(([d, s]) => `${d}\t${s}`)].join("\n"));
  console.log(`\nFound ${sorted.length} fresh brand-match candidates → ${outFile}`);
  for (const [d, s] of sorted.slice(0, 30)) console.log(`  ${d}\t${s}`);
  if (sorted.length > 30) console.log(`  ... +${sorted.length - 30} more`);
}

main().catch((e) => { console.error(e); process.exit(1); });
