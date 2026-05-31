import { cpSync, existsSync, mkdirSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// adapter-cloudflare with `fallback: 'spa'` emits _app/ + index.html directly
// into the wrangler assets dir (svelte.config.js + wrangler.jsonc point both
// SPA shell and Vite output through the same path). This script's remaining
// job is to mirror svelte/public/* — Vite's default publicDir — into the
// parent static/ dir, since SvelteKit doesn't ingest it (only static/ is its
// canonical convention). Without this, llms.txt / favicon.png / robots.txt
// etc. disappear from the deployed Worker after each build.
const here = path.dirname(fileURLToPath(import.meta.url));
const svelteDir = path.resolve(here, '..');
const publicDir = path.join(svelteDir, 'public');
const staticDir = path.resolve(svelteDir, '../static');

if (!existsSync(publicDir)) {
  console.log(`No public/ dir at ${publicDir}; nothing to sync.`);
  process.exit(0);
}

mkdirSync(staticDir, { recursive: true });

let copied = 0;
for (const name of readdirSync(publicDir)) {
  // Skip stale _app/ from old build pipeline — current build writes _app/
  // directly to static/ via adapter-cloudflare fallback: 'spa'.
  if (name === '_app') continue;
  const src = path.join(publicDir, name);
  const dst = path.join(staticDir, name);
  const st = statSync(src);
  cpSync(src, dst, { recursive: st.isDirectory() });
  copied += 1;
}

console.log(`Mirrored ${copied} entries from public/ → ${staticDir}`);
