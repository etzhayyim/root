#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const OUT = path.join(
  ROOT,
  "orgs/etzhayyim/com-etzhayyim-app-coverage/appview/coverage-ui-c0v3r4g3/svelte/static/bpmn-coverage/latest.json",
);

function readCoverage() {
  const stdout = execFileSync(
    process.execPath,
    ["70-tools/scripts/lint/bpmn-coverage.mjs", "--json"],
    { cwd: ROOT, encoding: "utf8", stdio: ["ignore", "pipe", "inherit"] },
  );
  return JSON.parse(stdout);
}

function main() {
  const report = readCoverage();
  const payload = {
    generated_at: new Date().toISOString(),
    loop_schedule: {
      workflow: ".github/workflows/coverage-site.yml",
      cron: "15 */6 * * *",
      site_path: "/bpmn-coverage/latest.json",
    },
    ...report,
  };

  mkdirSync(path.dirname(OUT), { recursive: true });
  writeFileSync(OUT, `${JSON.stringify(payload, null, 2)}\n`);
  console.log(`wrote ${path.relative(ROOT, OUT)} (${report.count} BPMN bindings)`);
}

main();
