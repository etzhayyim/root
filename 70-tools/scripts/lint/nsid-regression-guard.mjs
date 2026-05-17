#!/usr/bin/env node

import { promises as fs } from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = process.cwd();
const BASELINE_CSV = path.join(ROOT, "80-data/reports", "nsid-rule-violations-2026-04-01.csv");

function parseCsvLine(line) {
  const out = [];
  let i = 0;
  while (i < line.length) {
    if (line[i] === '"') {
      let j = i + 1;
      let cell = "";
      while (j < line.length) {
        if (line[j] === '"') {
          if (line[j + 1] === '"') {
            cell += '"';
            j += 2;
            continue;
          }
          break;
        }
        cell += line[j];
        j += 1;
      }
      out.push(cell);
      i = j + 1;
      if (line[i] === ",") i += 1;
      continue;
    }
    let j = i;
    while (j < line.length && line[j] !== ",") j += 1;
    out.push(line.slice(i, j));
    i = j + 1;
  }
  return out;
}

function isViolation(method) {
  return !method.includes(".");
}

async function collectCurrentViolations() {
  const set = new Set();
  const out = execFileSync(
    "rg",
    [
      "-n",
      String.raw`\.command\("([^"]+)"`,
      "60-apps",
      "50-infra",
      "20-actors",
      "30-graph",
      "40-engine",
      "--glob",
      "!**/node_modules/**",
      "--glob",
      "!**/.svelte-kit/**",
      "--glob",
      "!**/dist/**",
    ],
    { cwd: ROOT, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 },
  );
  const lines = out.split("\n").filter(Boolean);
  for (const line of lines) {
    const m = line.match(/^([^:]+):\d+:.*\.command\("([^"]+)"/);
    if (!m) continue;
    const rel = m[1];
    const method = m[2];
    if (!isViolation(method)) continue;
    set.add(`${rel}\t${method}`);
  }
  return set;
}

async function loadBaseline() {
  const csv = await fs.readFile(BASELINE_CSV, "utf8");
  const lines = csv.split("\n").filter(Boolean);
  if (lines.length < 2) return new Set();
  const header = parseCsvLine(lines[0]);
  const pathIdx = header.indexOf("path");
  const methodIdx = header.indexOf("method");
  if (pathIdx < 0 || methodIdx < 0) {
    throw new Error(`Invalid baseline header in ${BASELINE_CSV}`);
  }
  const set = new Set();
  for (let i = 1; i < lines.length; i += 1) {
    const row = parseCsvLine(lines[i]);
    const p = row[pathIdx];
    const m = row[methodIdx];
    if (!p || !m) continue;
    set.add(`${p}\t${m}`);
  }
  return set;
}

async function main() {
  const baseline = await loadBaseline();
  const current = await collectCurrentViolations();

  const added = [...current].filter((k) => !baseline.has(k)).sort();
  const removed = [...baseline].filter((k) => !current.has(k)).sort();

  console.log(`baseline=${baseline.size} current=${current.size} added=${added.length} removed=${removed.length}`);

  if (removed.length) {
    console.log("info: existing violations reduced since baseline (good).");
  }

  if (added.length) {
    console.error("ERROR: new NSID rule violations introduced:");
    for (const row of added.slice(0, 120)) {
      const [p, m] = row.split("\t");
      console.error(`- ${p} :: ${m}`);
    }
    if (added.length > 120) {
      console.error(`... and ${added.length - 120} more`);
    }
    process.exit(1);
  }
}

await main();
