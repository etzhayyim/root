#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const configPath = path.join(root, "70-tools/config/retired-cf-workers.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));

const errors = [];

for (const activePath of config.activePaths ?? []) {
  const activeAbs = path.join(root, activePath);
  const archivedAbs = path.join(root, config.archiveRoot, activePath);

  if (fs.existsSync(activeAbs)) {
    errors.push(`${activePath}: retired CF Worker config is back in active tree`);
  }
  if (!fs.existsSync(archivedAbs)) {
    errors.push(`${path.relative(root, archivedAbs)}: archived retired config is missing`);
  }
}

if (errors.length > 0) {
  console.error("retired-cf-worker-guard failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`retired-cf-worker-guard: ok (${config.activePaths.length} retired Worker configs)`);
