import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const POLICIES_ROOT = path.join(ROOT, "00-contracts/policies");
const OUT_FILE = path.join(ROOT, "50-infra/cloudflare/workers/atproto/src/generated/rego-policy-registry.gen.ts");

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...await walk(full));
    else if (entry.name === "policy.rego") out.push(full);
  }
  return out;
}

function parsePackage(rego, relPath) {
  const pkg = rego.match(/^package\s+([A-Za-z0-9_.]+)/m)?.[1];
  if (!pkg) throw new Error(`${relPath}: missing package declaration`);
  return pkg;
}

function tsString(value) {
  return JSON.stringify(value);
}

const policyFiles = await walk(POLICIES_ROOT);
const entries = [];
for (const policyFile of policyFiles.sort()) {
  const dir = path.dirname(policyFile);
  const relPath = path.relative(ROOT, policyFile);
  const dataPath = path.join(dir, "data.json");
  const testPath = path.join(dir, "test.rego");
  const rego = await readFile(policyFile, "utf8");
  const data = JSON.parse(await readFile(dataPath, "utf8"));
  await readFile(testPath, "utf8");
  const pkg = parsePackage(rego, relPath);
  const methodPolicy = data.method_policy;
  if (!methodPolicy || typeof methodPolicy !== "object") {
    throw new Error(`${path.relative(ROOT, dataPath)}: missing method_policy`);
  }
  entries.push({
    package: pkg,
    path: path.relative(ROOT, dir),
    rego,
    data,
    methodPolicy: {
      package: pkg,
      requiresAuth: Boolean(methodPolicy.requiresAuth),
      allowedScopes: Array.isArray(methodPolicy.allowedScopes) ? methodPolicy.allowedScopes : [],
      allowedPermissionSets: Array.isArray(methodPolicy.allowedPermissionSets) ? methodPolicy.allowedPermissionSets : [],
      publicRead: Boolean(methodPolicy.publicRead),
    },
  });
}

const lines = [
  "// rego-policy-registry.gen.ts - Auto-generated from 00-contracts/policies.",
  "// Do not edit by hand. Run `pnpm codegen:rego:registry`.",
  "",
  "export interface BundledRegoMethodPolicy {",
  "  package: string;",
  "  requiresAuth: boolean;",
  "  allowedScopes: string[];",
  "  allowedPermissionSets: string[];",
  "  publicRead: boolean;",
  "}",
  "",
  "export interface BundledRegoPolicy {",
  "  package: string;",
  "  path: string;",
  "  rego: string;",
  "  data: Record<string, unknown>;",
  "  methodPolicy: BundledRegoMethodPolicy;",
  "}",
  "",
  "export const BUNDLED_REGO_POLICIES: BundledRegoPolicy[] = [",
];

for (const entry of entries) {
  lines.push("  {");
  lines.push(`    package: ${tsString(entry.package)},`);
  lines.push(`    path: ${tsString(entry.path)},`);
  lines.push(`    rego: ${tsString(entry.rego)},`);
  lines.push(`    data: ${tsString(entry.data)},`);
  lines.push(`    methodPolicy: ${tsString(entry.methodPolicy)},`);
  lines.push("  },");
}

lines.push("];");
lines.push("");
lines.push("export const BUNDLED_REGO_BY_PACKAGE = new Map<string, BundledRegoPolicy>();");
lines.push("for (const policy of BUNDLED_REGO_POLICIES) BUNDLED_REGO_BY_PACKAGE.set(policy.package, policy);");

await mkdir(path.dirname(OUT_FILE), { recursive: true });
await writeFile(OUT_FILE, `${lines.join("\n")}\n`);
console.error(`generated Rego policies: ${entries.length}`);
