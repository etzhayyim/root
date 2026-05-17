import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const svelteDir = path.resolve(here, '..');
const buildDir = path.join(svelteDir, 'build');
const staticDir = path.resolve(svelteDir, '../static');
const passthroughFiles = ['_headers', '_redirects'];

if (!existsSync(buildDir)) {
  console.error(`Build output not found: ${buildDir}`);
  process.exit(1);
}

mkdirSync(staticDir, { recursive: true });
rmSync(path.join(staticDir, '_app'), { recursive: true, force: true });
rmSync(path.join(staticDir, 'assets'), { recursive: true, force: true });

cpSync(path.join(buildDir, 'index.html'), path.join(staticDir, 'index.html'));
if (existsSync(path.join(buildDir, 'assets'))) {
  cpSync(path.join(buildDir, 'assets'), path.join(staticDir, 'assets'), { recursive: true });
}
for (const name of passthroughFiles) {
  const src = path.join(staticDir, name);
  if (!existsSync(src)) continue;
  cpSync(src, path.join(buildDir, name));
}

console.log(`Synced SPA assets to ${staticDir}`);
