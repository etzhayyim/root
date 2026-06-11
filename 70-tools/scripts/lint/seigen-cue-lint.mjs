#!/usr/bin/env node
import path from "node:path";
import { parseJsonFile, tryCueVet, validateCloudflarePipelines } from "../seigen/core.mjs";

function getArg(name, fallback = "") {
  const idx = process.argv.indexOf(name);
  if (idx < 0) return fallback;
  return process.argv[idx + 1] ?? fallback;
}

const configPath = getArg("--config", "rules/compliance/seigen/cloudflare-pipelines.input.example.json");
const locale = getArg("--locale", "ja");
const enforceCue = process.env.SEIGEN_ENFORCE_CUE === "1";

let input;
try {
  input = parseJsonFile(configPath, locale);
} catch (error) {
  console.error(`[seigen] ${String(error.message || error)}`);
  process.exit(1);
}

const result = validateCloudflarePipelines(input, { locale });
const cue = tryCueVet(path.resolve(configPath), { locale });

if (!cue.ok && enforceCue) {
  console.error(`[seigen] ${cue.message}`);
  if (cue.stderr) console.error(cue.stderr);
  if (cue.stdout) console.error(cue.stdout);
  process.exit(1);
}

if (cue.skipped) {
  console.warn(`[seigen] ${cue.message}`);
}

if (!result.ok) {
  console.error(`[seigen] ${result.summary}`);
  for (const d of result.diagnostics) {
    console.error(`- [${d.code}] ${d.path}: ${d.message} (actual=${JSON.stringify(d.actual)} expected=${JSON.stringify(d.expected)})`);
  }
  process.exit(1);
}

console.log(`[seigen] ${result.summary}`);
process.exit(0);
