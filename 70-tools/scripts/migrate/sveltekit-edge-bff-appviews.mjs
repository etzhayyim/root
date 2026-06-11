#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOTS = ["60-apps"];
const APPLY = process.argv.includes("--write");
const TARGET_ARG = process.argv.find((arg) => arg.startsWith("--target="));
const TARGET_FILTER = TARGET_ARG ? TARGET_ARG.slice("--target=".length) : "";
const SVELTEKIT_MAIN = "svelte/.svelte-kit/cloudflare/_worker.js";
const SVELTEKIT_ASSETS = "./svelte/.svelte-kit/cloudflare/client";
const MCP_ROUTER_URL = "https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message";

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if ([".git", "node_modules", ".svelte-kit", ".wrangler", "build", "dist"].includes(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if ((entry.name === "wrangler.jsonc" || entry.name === "wrangler.json") && full.includes("/appview/")) out.push(full);
  }
  return out;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function writeJson(file, value) {
  const next = `${JSON.stringify(value, null, 2)}\n`;
  if (fs.existsSync(file) && fs.readFileSync(file, "utf8") === next) return false;
  if (APPLY) fs.writeFileSync(file, next);
  return true;
}

function writeText(file, value) {
  if (fs.existsSync(file) && fs.readFileSync(file, "utf8") === value) return false;
  if (APPLY) {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, value);
  }
  return true;
}

function removeFile(file) {
  if (!fs.existsSync(file)) return false;
  if (APPLY) fs.rmSync(file);
  return true;
}

function updateWrangler(file) {
  let text = fs.readFileSync(file, "utf8");
  const before = text;
  text = text.replace(/"main"\s*:\s*"[^"]+"/, `"main": "${SVELTEKIT_MAIN}"`);
  if (/"assets"\s*:\s*\{/.test(text)) {
    text = text.replace(/"directory"\s*:\s*"\.\/svelte\/build"/, `"directory": "${SVELTEKIT_ASSETS}"`);
    if (!/"assets"\s*:\s*\{[\s\S]*?"directory"/.test(text)) {
      text = text.replace(/"assets"\s*:\s*\{/, `"assets": {\n    "directory": "${SVELTEKIT_ASSETS}",`);
    }
  } else {
    text = text.replace(
      /"compatibility_flags"\s*:\s*\[[^\]]*\]\s*,/,
      (match) => `${match}\n  "assets": {\n    "directory": "${SVELTEKIT_ASSETS}",\n    "binding": "ASSETS",\n    "html_handling": "auto-trailing-slash",\n    "not_found_handling": "single-page-application"\n  },`,
    );
  }
  text = text.replace(/,\s*"alias"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*(?=,\s*"assets")/s, "");
  text = text.replace(/\n\s*"hyperdrive"\s*:\s*\[[\s\S]*?\]\s*,/m, "\n");
  text = text.replace(/"APP_FRAMEWORK"\s*:\s*"[^"]+"/, `"APP_FRAMEWORK": "sveltekit-edge-bff"`);
  if (!text.includes('"AGENTGATEWAY_MCP_ROUTER_URL"')) {
    text = text.replace(
      /"APP_FRAMEWORK"\s*:\s*"sveltekit-edge-bff"\s*,/,
      `"APP_FRAMEWORK": "sveltekit-edge-bff",\n    "AGENTGATEWAY_MCP_ROUTER_URL": "${MCP_ROUTER_URL}",`,
    );
  }
  if (text !== before && APPLY) fs.writeFileSync(file, text);
  return text !== before;
}

function isAlreadySvelteKitEdgeBff(wrangler, svelteDir) {
  const wranglerText = fs.readFileSync(wrangler, "utf8");
  const pkg = readJson(path.join(svelteDir, "package.json"));
  return wranglerText.includes(`"main": "${SVELTEKIT_MAIN}"`)
    && wranglerText.includes(`"directory": "${SVELTEKIT_ASSETS}"`)
    && !/"alias"\s*:/.test(wranglerText)
    && !/\b(?:hyperdrive|HYPERDRIVE)\b/.test(wranglerText)
    && !!pkg.devDependencies?.["@sveltejs/kit"];
}

function updateOuterPackage(dir) {
  const file = path.join(dir, "package.json");
  if (!fs.existsSync(file)) return false;
  const pkg = readJson(file);
  const before = JSON.stringify(pkg);
  pkg.main = SVELTEKIT_MAIN;
  pkg.scripts = {
    ...(pkg.scripts ?? {}),
    dev: "pnpm --dir svelte dev",
    build: "pnpm --dir svelte build",
    preview: "pnpm --dir svelte preview",
    check: "pnpm --dir svelte check",
  };
  for (const key of ["dependencies", "devDependencies"]) {
    if (!pkg[key]) continue;
    for (const dep of ["hono", "@hono/node-server", "@etzhayyim/kotodama-host-sdk", "kysely", "pg"]) delete pkg[key][dep];
    if (Object.keys(pkg[key]).length === 0) delete pkg[key];
  }
  return JSON.stringify(pkg) !== before ? writeJson(file, pkg) : false;
}

function updateSveltePackage(svelteDir) {
  const file = path.join(svelteDir, "package.json");
  const pkg = readJson(file);
  const before = JSON.stringify(pkg);
  pkg.scripts = {
    ...(pkg.scripts ?? {}),
    dev: "vite dev",
    build: "vite build",
    preview: "vite preview",
    check: "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
  };
  pkg.dependencies = { ...(pkg.dependencies ?? {}) };
  pkg.dependencies.svelte = pkg.dependencies.svelte ?? "^5.55.3";
  pkg.devDependencies = { ...(pkg.devDependencies ?? {}) };
  pkg.devDependencies["@sveltejs/adapter-cloudflare"] = pkg.devDependencies["@sveltejs/adapter-cloudflare"] ?? "^7.2.8";
  pkg.devDependencies["@sveltejs/kit"] = pkg.devDependencies["@sveltejs/kit"] ?? "^2.57.1";
  pkg.devDependencies["@sveltejs/vite-plugin-svelte"] = pkg.devDependencies["@sveltejs/vite-plugin-svelte"] ?? "^5.1.1";
  pkg.devDependencies["svelte-check"] = pkg.devDependencies["svelte-check"] ?? "^4.4.6";
  pkg.devDependencies.typescript = pkg.devDependencies.typescript ?? "^5.9.3";
  pkg.devDependencies.vite = pkg.devDependencies.vite ?? "^6.4.2";
  return JSON.stringify(pkg) !== before ? writeJson(file, pkg) : false;
}

function migrateSvelteProject(svelteDir) {
  let changed = false;
  changed = updateSveltePackage(svelteDir) || changed;
  changed = writeText(path.join(svelteDir, "svelte.config.js"), `import adapter from '@sveltejs/adapter-cloudflare';\nimport { vitePreprocess } from '@sveltejs/vite-plugin-svelte';\n\nconst config = {\n  preprocess: vitePreprocess(),\n  kit: {\n    adapter: adapter()\n  }\n};\n\nexport default config;\n`) || changed;
  changed = writeText(path.join(svelteDir, "vite.config.ts"), `import { sveltekit } from '@sveltejs/kit/vite';\nimport { defineConfig } from 'vite';\n\nexport default defineConfig({\n  plugins: [sveltekit()]\n});\n`) || changed;
  changed = writeText(path.join(svelteDir, "tsconfig.json"), `{\n  "extends": "./.svelte-kit/tsconfig.json",\n  "compilerOptions": {\n    "allowJs": true,\n    "checkJs": true,\n    "esModuleInterop": true,\n    "forceConsistentCasingInFileNames": true,\n    "resolveJsonModule": true,\n    "skipLibCheck": true,\n    "sourceMap": true,\n    "strict": true,\n    "moduleResolution": "bundler"\n  }\n}\n`) || changed;
  changed = writeText(path.join(svelteDir, "src", "app.html"), `<!doctype html>\n<html lang="ja">\n  <head>\n    <meta charset="utf-8" />\n    <meta name="viewport" content="width=device-width, initial-scale=1" />\n    %sveltekit.head%\n  </head>\n  <body data-sveltekit-preload-data="hover">\n    <div style="display: contents">%sveltekit.body%</div>\n  </body>\n</html>\n`) || changed;
  const appFile = path.join(svelteDir, "src", "App.svelte");
  if (fs.existsSync(appFile)) {
    changed = writeText(path.join(svelteDir, "src", "routes", "+page.svelte"), `<script lang="ts">\n  import App from '../App.svelte';\n</script>\n\n<App />\n`) || changed;
  }
  changed = removeFile(path.join(svelteDir, "src", "main.ts")) || changed;
  changed = removeFile(path.join(svelteDir, "index.html")) || changed;
  return changed;
}

const wranglers = ROOTS.flatMap((root) => walk(root))
  .filter((file) => !TARGET_FILTER || file.includes(TARGET_FILTER))
  .filter((file) => fs.existsSync(path.join(path.dirname(file), "svelte", "package.json")));

const changed = [];
for (const wrangler of wranglers) {
  const dir = path.dirname(wrangler);
  const svelteDir = path.join(dir, "svelte");
  if (isAlreadySvelteKitEdgeBff(wrangler, svelteDir)) continue;
  const changes = [];
  if (updateWrangler(wrangler)) changes.push("wrangler");
  if (updateOuterPackage(dir)) changes.push("package");
  if (migrateSvelteProject(svelteDir)) changes.push("svelte");
  if (changes.length) changed.push(`${dir} (${changes.join(",")})`);
}

for (const line of changed) console.log(line);
console.log(`${APPLY ? "updated" : "would update"} ${changed.length}/${wranglers.length} Svelte appviews`);
