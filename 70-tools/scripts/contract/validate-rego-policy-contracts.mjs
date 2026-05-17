import { existsSync } from "node:fs";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const policiesRoot = path.join(root, "00-contracts/policies");

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
  console.error(`[rego-contract] ${message}`);
  process.exitCode = 1;
}

if (!existsSync(policiesRoot)) {
  fail("00-contracts/policies does not exist");
} else {
  const files = await walk(policiesRoot);
  const policyFiles = files.filter((file) => file.endsWith("/policy.rego"));
  if (policyFiles.length === 0) fail("no policy.rego files found");

  for (const policyFile of policyFiles) {
    const dir = path.dirname(policyFile);
    for (const required of ["data.json", "test.rego"]) {
      if (!existsSync(path.join(dir, required))) {
        fail(`${path.relative(root, dir)} missing ${required}`);
      }
    }
    const policy = await readFile(policyFile, "utf8");
    const pkg = policy.match(/^package\s+([A-Za-z0-9_.]+)/m)?.[1];
    if (!pkg) fail(`${path.relative(root, policyFile)} missing package declaration`);
    const data = JSON.parse(await readFile(path.join(dir, "data.json"), "utf8"));
    if (!data.method_policy || typeof data.method_policy !== "object") {
      fail(`${path.relative(root, dir)}/data.json missing method_policy`);
    }
  }

  const opa = spawnSync("opa", ["test", policiesRoot], { cwd: root, encoding: "utf8" });
  if (opa.error && opa.error.code === "ENOENT") {
    console.warn("[rego-contract] opa not found; skipped opa test");
  } else if (opa.status !== 0) {
    process.stdout.write(opa.stdout ?? "");
    process.stderr.write(opa.stderr ?? "");
    fail("opa test failed");
  } else {
    process.stdout.write(opa.stdout ?? "");
  }
}
