import { existsSync } from "node:fs";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const dmnRoot = path.join(root, "00-contracts/dmn");

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...await walk(full));
    else out.push(full);
  }
  return out;
}

function fail(message) {
  console.error(`[dmn-contract] ${message}`);
  process.exitCode = 1;
}

function textEntries(body, tag) {
  return [...body.matchAll(new RegExp(`<(?:\\w+:)?${tag}\\b[^>]*>\\s*<(?:\\w+:)?text>([\\s\\S]*?)<\\/(?:\\w+:)?text>\\s*<\\/(?:\\w+:)?${tag}>`, "g"))]
    .map((m) => m[1].trim());
}

if (!existsSync(dmnRoot)) {
  fail("00-contracts/dmn does not exist");
} else {
  const files = (await walk(dmnRoot)).filter((file) => file.endsWith(".dmn") || file.endsWith(".dmn.xml"));
  if (files.length === 0) fail("no DMN files found");

  for (const file of files) {
    const rel = path.relative(root, file);
    const xml = await readFile(file, "utf8");
    const decision = xml.match(/<(?:\w+:)?decision\b[^>]*\bid="([^"]+)"/);
    if (!decision) fail(`${rel} missing decision id`);

    const table = xml.match(/<(?:\w+:)?decisionTable\b([^>]*)>([\s\S]*?)<\/(?:\w+:)?decisionTable>/);
    if (!table) {
      fail(`${rel} missing decisionTable`);
      continue;
    }

    const hitPolicy = (table[1].match(/\bhitPolicy="([^"]+)"/)?.[1] ?? "FIRST").toUpperCase().replace(/\s+/g, "_");
    if (!["UNIQUE", "FIRST", "ANY", "COLLECT", "RULE_ORDER"].includes(hitPolicy)) {
      fail(`${rel} unsupported hitPolicy ${hitPolicy}`);
    }

    const inputCount = [...table[2].matchAll(/<(?:\w+:)?input\b[^>]*>/g)].length;
    const outputCount = [...table[2].matchAll(/<(?:\w+:)?output\b[^>]*\/?>/g)].length;
    if (inputCount === 0) fail(`${rel} has no input clauses`);
    if (outputCount === 0) fail(`${rel} has no output clauses`);

    const rules = [...table[2].matchAll(/<(?:\w+:)?rule\b[^>]*>([\s\S]*?)<\/(?:\w+:)?rule>/g)];
    if (rules.length === 0) fail(`${rel} has no rules`);
    for (const [index, rule] of rules.entries()) {
      const inputs = textEntries(rule[1], "inputEntry");
      const outputs = textEntries(rule[1], "outputEntry");
      if (inputs.length !== inputCount) fail(`${rel} rule ${index + 1} inputEntry count ${inputs.length} != input count ${inputCount}`);
      if (outputs.length !== outputCount) fail(`${rel} rule ${index + 1} outputEntry count ${outputs.length} != output count ${outputCount}`);
    }
  }
}
