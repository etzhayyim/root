import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const DMN_ROOT = path.join(ROOT, "00-contracts/dmn");
const OUT_FILE = path.join(ROOT, "50-infra/cloudflare/workers/atproto/src/generated/dmn-contract-registry.gen.ts");

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...await walk(full));
    else if (full.endsWith(".dmn") || full.endsWith(".dmn.xml")) out.push(full);
  }
  return out;
}

function attr(openTag, name) {
  return openTag.match(new RegExp(`\\b${name}="([^"]*)"`))?.[1] ?? "";
}

function parseDecisionMeta(xml, relPath) {
  const decisionOpen = xml.match(/<(?:\w+:)?decision\b[^>]*>/)?.[0] ?? "";
  const tableOpen = xml.match(/<(?:\w+:)?decisionTable\b[^>]*>/)?.[0] ?? "";
  const decisionId = attr(decisionOpen, "id");
  if (!decisionId) throw new Error(`${relPath}: missing decision id`);
  return {
    decisionId,
    decisionName: attr(decisionOpen, "name") || decisionId,
    hitPolicy: (attr(tableOpen, "hitPolicy") || "FIRST").toUpperCase().replace(/\s+/g, "_"),
  };
}

function tsString(value) {
  return JSON.stringify(value);
}

const files = await walk(DMN_ROOT);
const entries = [];
for (const file of files.sort()) {
  const relPath = path.relative(ROOT, file);
  const xml = await readFile(file, "utf8");
  const meta = parseDecisionMeta(xml, relPath);
  entries.push({ ...meta, path: relPath, xml });
}

const lines = [
  "// dmn-contract-registry.gen.ts - Auto-generated from 00-contracts/dmn.",
  "// Do not edit by hand. Run `pnpm codegen:dmn:registry`.",
  "",
  "export interface BundledDmnContract {",
  "  decisionId: string;",
  "  decisionName: string;",
  "  hitPolicy: string;",
  "  path: string;",
  "  xml: string;",
  "}",
  "",
  "export const BUNDLED_DMN_CONTRACTS: BundledDmnContract[] = [",
];

for (const entry of entries) {
  lines.push("  {");
  lines.push(`    decisionId: ${tsString(entry.decisionId)},`);
  lines.push(`    decisionName: ${tsString(entry.decisionName)},`);
  lines.push(`    hitPolicy: ${tsString(entry.hitPolicy)},`);
  lines.push(`    path: ${tsString(entry.path)},`);
  lines.push(`    xml: ${tsString(entry.xml)},`);
  lines.push("  },");
}

lines.push("];");
lines.push("");
lines.push("export const BUNDLED_DMN_BY_ID = new Map<string, BundledDmnContract>();");
lines.push("for (const contract of BUNDLED_DMN_CONTRACTS) {");
lines.push("  BUNDLED_DMN_BY_ID.set(contract.decisionId, contract);");
lines.push("  BUNDLED_DMN_BY_ID.set(contract.decisionName, contract);");
lines.push("}");

await mkdir(path.dirname(OUT_FILE), { recursive: true });
await writeFile(OUT_FILE, `${lines.join("\n")}\n`);
console.error(`generated DMN contracts: ${entries.length}`);
