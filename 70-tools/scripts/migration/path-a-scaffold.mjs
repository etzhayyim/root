#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ESBUILD_VERSION = "^0.25.12";
const DEFAULT_BUILD_SCRIPT = "node build.mjs";
const DEFAULT_DOC_NOTE_NAME = "260327-path-a-scaffold.md";

function printUsage() {
  console.log(`Usage: node scripts/migration/path-a-scaffold.mjs <component-dir> [options]

Options:
  --component <dir>  Alias for positional <component-dir>.
  --dry-run          Show planned changes without writing files.
  --force            Overwrite existing scaffold files when content differs.
  --skip-note        Skip creating migration note under component project docs.
  --note-name <name> Migration note filename (default: ${DEFAULT_DOC_NOTE_NAME}).
  --help             Show this help text.

Examples:
  node scripts/migration/path-a-scaffold.mjs projects/etzhayyim-project-news/wasm/news-core-component
  node scripts/migration/path-a-scaffold.mjs projects/etzhayyim-project-news/wasm/news-core-component --dry-run
  node scripts/migration/path-a-scaffold.mjs ./projects/... --force --note-name 260327-news-path-a.md
`);
}

function parseArgs(argv) {
  const args = {
    force: false,
    dryRun: false,
    skipNote: false,
    noteName: DEFAULT_DOC_NOTE_NAME,
    componentDir: null,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("-")) {
      if (args.componentDir) {
        throw new Error(`Unexpected positional argument: ${arg}`);
      }
      args.componentDir = arg;
      continue;
    }
    if (arg === "--help" || arg === "-h") {
      args.help = true;
      return args;
    }
    if (arg === "--dry-run") {
      args.dryRun = true;
      continue;
    }
    if (arg === "--force") {
      args.force = true;
      continue;
    }
    if (arg === "--skip-note") {
      args.skipNote = true;
      continue;
    }
    if (arg.startsWith("--component=")) {
      const value = arg.slice("--component=".length).trim();
      if (!value) throw new Error("--component requires a value.");
      if (args.componentDir) {
        throw new Error(`Component dir already set: ${args.componentDir}`);
      }
      args.componentDir = value;
      continue;
    }
    if (arg === "--component") {
      const value = argv[i + 1];
      if (!value || value.startsWith("-")) {
        throw new Error("--component requires a value.");
      }
      if (args.componentDir) {
        throw new Error(`Component dir already set: ${args.componentDir}`);
      }
      args.componentDir = value;
      i += 1;
      continue;
    }
    if (arg.startsWith("--note-name=")) {
      args.noteName = arg.slice("--note-name=".length).trim();
      if (!args.noteName) throw new Error("--note-name requires a value.");
      continue;
    }
    if (arg === "--note-name") {
      const value = argv[i + 1];
      if (!value || value.startsWith("-")) {
        throw new Error("--note-name requires a value.");
      }
      args.noteName = value;
      i += 1;
      continue;
    }
    throw new Error(`Unknown option: ${arg}`);
  }
  return args;
}

function ensureDirectory(targetPath) {
  if (!fs.existsSync(targetPath)) {
    fs.mkdirSync(targetPath, { recursive: true });
    return true;
  }
  return false;
}

function toSlug(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/--+/g, "-");
}

function toName(value) {
  return value
    .replace(/[-_]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function readOrNull(filePath) {
  if (!fs.existsSync(filePath)) return null;
  return fs.readFileSync(filePath, "utf8");
}

function formatJson(value) {
  return JSON.stringify(value, null, 2).trimEnd() + "\n";
}

function resolveProjectDocsDir(componentDir) {
  let current = path.resolve(componentDir);
  while (true) {
    const base = path.basename(current);
    if (base === "wasm") {
      const projectDir = path.dirname(current);
      const docsDir = path.join(projectDir, "docs");
      if (fs.existsSync(docsDir) && fs.statSync(docsDir).isDirectory()) {
        return docsDir;
      }
      return null;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return null;
}

function buildTemplates({ appId, appName }) {
  const appTemplate = `import { createHostSDK, type AppDef, type ComAtprotoSyncSubscribeReposCommit, type HostSDK } from "@etzhayyim/kotodama-host-sdk";

const APP_DEF: AppDef = {
  id: "${appId}",
  name: "${appName}",
  description: "Path A TS native scaffold entrypoint.",
};

export function createComponentHostSDK(env: Record<string, unknown>): HostSDK {
  return createHostSDK({
    appDef: APP_DEF,
    env,
  });
}

export function runHeartbeat(_sdk: HostSDK): { ok: true; message: string } {
  return { ok: true, message: "heartbeat ok" };
}

export function handleComAtprotoSyncSubscribeReposCommit(
  _sdk: HostSDK,
  _commit: ComAtprotoSyncSubscribeReposCommit,
): { ok: true; detail: string } {
  return { ok: true, detail: "commit accepted" };
}
`;

const workerTemplate = `import { createComponentHostSDK, handleComAtprotoSyncSubscribeReposCommit, runHeartbeat } from "./app.js";

type RawCommitInput = {
  seq?: number | string;
  repo?: string;
  collection?: string;
  rkey?: string;
  action?: string;
  cid?: string | null;
  rev?: string | null;
  time?: string;
};

function parseCommitPayload(body: RawCommitInput): {
  seq: bigint;
  repo: string;
  collection: string;
  rkey: string;
  action: string;
  cid: string | null;
  rev: string | null;
  time: string;
} {
  const seqNumber = Number(body.seq ?? 0);
  return {
    seq: BigInt(Number.isFinite(seqNumber) ? seqNumber : 0),
    repo: body.repo ?? "",
    collection: body.collection ?? "",
    rkey: body.rkey ?? "",
    action: body.action ?? "",
    cid: body.cid ?? null,
    rev: body.rev ?? null,
    time: body.time ?? "",
  };
}

export default {
  async fetch(request: Request, env: Record<string, unknown>): Promise<Response> {
    const sdk = createComponentHostSDK(env);
    const url = new URL(request.url);

    if (url.pathname === "/_heartbeat" && request.method === "POST") {
      const result = runHeartbeat(sdk);
      await sdk.flushWriteBuffer();
      return Response.json(result);
    }

    if (
      (url.pathname === "/_commit" || url.pathname === "/_w/commit") &&
      request.method === "POST"
    ) {
      const payload = (await request.json().catch((_err) => ({}))) as RawCommitInput;
      const result = handleComAtprotoSyncSubscribeReposCommit(sdk, parseCommitPayload(payload));
      await sdk.flushWriteBuffer();
      return Response.json(result);
    }

    const response = await sdk.handleRequest({
      method: request.method,
      url: request.url,
      headers: request.headers,
      body: request.body,
    });

    await sdk.flushWriteBuffer();
    return response;
  },
};`;

  return { appTemplate, workerTemplate };
}

function readPackageData(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  return JSON.parse(raw);
}

function writeIfNeeded(filePath, content, dryRun, force = false) {
  const existing = readOrNull(filePath);
  if (existing === null) {
    if (dryRun) {
      return { changed: true, action: "create", path: filePath };
    }
    ensureDirectory(path.dirname(filePath));
    fs.writeFileSync(filePath, content);
    return { changed: true, action: "create", path: filePath };
  }
  if (existing === content) {
    return { changed: false, action: "skip", path: filePath };
  }
  if (!force) {
    return {
      changed: false,
      action: "skip",
      path: filePath,
      reason: "exists with different content. Use --force to replace.",
    };
  }
  if (dryRun) {
    return { changed: true, action: "replace", path: filePath };
  }
  fs.writeFileSync(filePath, content);
  return { changed: true, action: "replace", path: filePath };
}

function syncPackageJson(pkgPath, options) {
  const pkg = readPackageData(pkgPath);
  const plan = [];
  let changed = false;

  if (!pkg.scripts) pkg.scripts = {};
  const buildScript = pkg.scripts["build:ts-native"];
  if (buildScript !== DEFAULT_BUILD_SCRIPT) {
    if (buildScript === undefined) {
      plan.push({ type: "add", location: "package.json scripts.build:ts-native", value: DEFAULT_BUILD_SCRIPT });
      pkg.scripts["build:ts-native"] = DEFAULT_BUILD_SCRIPT;
      changed = true;
    } else if (options.force) {
      plan.push({
        type: "change",
        location: "package.json scripts.build:ts-native",
        value: `${buildScript} -> ${DEFAULT_BUILD_SCRIPT}`,
      });
      pkg.scripts["build:ts-native"] = DEFAULT_BUILD_SCRIPT;
      changed = true;
    } else {
      plan.push({
        type: "skip",
        location: "package.json scripts.build:ts-native",
        reason: `already set to "${buildScript}"`,
      });
    }
  }

  if (!pkg.devDependencies) pkg.devDependencies = {};
  const existingEsbuild = pkg.devDependencies.esbuild;
  if (existingEsbuild === undefined) {
    plan.push({ type: "add", location: "package.json devDependencies.esbuild", value: ESBUILD_VERSION });
    pkg.devDependencies.esbuild = ESBUILD_VERSION;
    changed = true;
  } else {
    plan.push({
      type: "skip",
      location: "package.json devDependencies.esbuild",
      reason: `already declared as "${existingEsbuild}"`,
    });
  }

  if (!changed) {
    return { changed: false, plan, path: pkgPath };
  }

  const next = formatJson(pkg);
  if (options.dryRun) {
    return { changed: true, dryRun: true, plan, path: pkgPath, payload: next };
  }
  fs.writeFileSync(pkgPath, next);
  return { changed: true, path: pkgPath, plan };
}

function buildMigrationNote(docsDir, packageName, componentDir, options) {
  const notePath = path.join(docsDir, options.noteName);
  const existing = readOrNull(notePath);
  const now = new Date().toISOString();
  const content = `# Path A Migration Scaffold

- component-dir: ${componentDir}
- package: ${packageName}
- generated-at: ${now}
- scaffold-files:
  - src/app.ts
  - src/worker.ts
  - build.mjs
  - package.json (build:ts-native / esbuild devDependency)
`;
  if (existing === null) return { path: notePath, action: "create", content };
  if (existing === content) return { path: notePath, action: "skip" };
  return { path: notePath, action: "skip", reason: "note already exists with different content" };
}

function logPlan(changes) {
  for (const change of changes) {
    if (change.action === "skip") {
      if (change.reason) {
        console.log(`[skip] ${change.path} ${change.reason}`);
      } else {
        console.log(`[skip] ${change.path}`);
      }
      continue;
    }
    console.log(`[${change.action}] ${change.path}`);
  }
}

function run() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.componentDir) {
    printUsage();
    if (args.help) process.exit(0);
    process.exit(1);
  }

  const componentDir = path.resolve(process.cwd(), args.componentDir);
  if (!fs.existsSync(componentDir) || !fs.statSync(componentDir).isDirectory()) {
    console.error(`Component dir not found: ${componentDir}`);
    process.exit(1);
  }

  const pkgPath = path.join(componentDir, "package.json");
  const hasPackageJson = fs.existsSync(pkgPath);
  const pkg = hasPackageJson ? readPackageData(pkgPath) : null;
  const packageName = pkg?.name ?? path.basename(componentDir);
  const appId = toSlug(packageName) || "path-a-component";
  const appName = toName(appId);
  const { appTemplate, workerTemplate } = buildTemplates({
    appId,
    appName,
  });
  const planEntries = [];

  const srcDir = path.join(componentDir, "src");
  const appResult = writeIfNeeded(path.join(srcDir, "app.ts"), appTemplate, args.dryRun, args.force);
  const workerResult = writeIfNeeded(path.join(srcDir, "worker.ts"), workerTemplate, args.dryRun, args.force);

  planEntries.push(appResult, workerResult);

  if (hasPackageJson) {
    const packageResult = syncPackageJson(pkgPath, args);
    if (packageResult.changed) {
      if (packageResult.dryRun) {
        planEntries.push({
          action: "write",
          path: packageResult.path,
          payload: packageResult.payload,
        });
      } else {
        planEntries.push({ action: "write", path: packageResult.path, payload: true });
      }
    } else {
      planEntries.push({ action: "skip", path: packageResult.path, reason: "package.json already up to date" });
    }
  } else {
    planEntries.push({ action: "skip", path: pkgPath, reason: "package.json not found (scaffold-only mode)" });
  }

  const docsDir = args.skipNote ? null : resolveProjectDocsDir(componentDir);
  if (docsDir) {
    const note = buildMigrationNote(docsDir, packageName, componentDir, args);
    if (note.action === "create") {
      if (args.dryRun) {
        planEntries.push({ action: "create", path: note.path });
      } else {
        fs.writeFileSync(note.path, note.content);
        planEntries.push({ action: "create", path: note.path });
      }
    } else if (note.action === "skip") {
      planEntries.push({ action: "skip", path: note.path, reason: note.reason ?? "already exists" });
    }
  } else if (!args.skipNote) {
    planEntries.push({ action: "skip", path: "project docs directory", reason: "not resolvable from component path" });
  }

  logPlan(planEntries);
  console.log(`\nDry-run: ${args.dryRun ? "enabled" : "disabled"}`);

  const changedFiles = planEntries.filter((entry) => entry.action !== "skip").map((entry) => entry.path);
  const skipped = planEntries.filter((entry) => entry.action === "skip").length;
  if (changedFiles.length > 0) {
    console.log("Changed files:");
    for (const file of changedFiles) {
      console.log(`- ${file}`);
    }
  } else {
    console.log("No file changes planned.");
  }
  if (args.dryRun) {
    console.log(`Planned change count: ${changedFiles.length}, skipped: ${skipped}`);
    process.exit(0);
  }
  if (changedFiles.length === 0) {
    process.exit(0);
  }
}

run();
