// PROOF (real browser): drive serve/demo.html in the system Google Chrome via
// playwright-core. The page registers kotoba-sw.js (a Service Worker), seeds the
// REAL etzhayyim actor datoms, and answers GET /xrpc/app.bsky.actor.searchActors
// from the in-browser kotoba-wasm node (x-kotoba-sw: local-wasm) — no server pull.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve, extname } from 'node:path';
import { chromium } from 'playwright-core';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, 'serve');
const MIME = { '.html':'text/html', '.js':'text/javascript', '.mjs':'text/javascript',
  '.wasm':'application/wasm', '.json':'application/json' };

const server = createServer(async (req, res) => {
  try {
    const p = join(root, decodeURIComponent(req.url.split('?')[0]));
    const buf = await readFile(p);
    res.writeHead(200, { 'content-type': MIME[extname(p)] || 'application/octet-stream',
      'service-worker-allowed': '/' });
    res.end(buf);
  } catch { res.writeHead(404); res.end('nf'); }
});
await new Promise(r => server.listen(0, r));
const base = `http://localhost:${server.address().port}`;

let fails = 0;
const ok = (c, m) => { console.log(`${c ? 'PASS' : 'FAIL'}  ${m}`); if (!c) fails++; };

const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const ver = browser.version();
  await page.goto(`${base}/demo.html`);
  // demo.html reloads once if no SW controller; wait until it has seeded + searched.
  await page.waitForFunction(
    () => document.getElementById('out')?.textContent?.includes('served-by'),
    { timeout: 30000 });

  // Drive a kamado search through the SW-intercepted XRPC fetch.
  const served = await page.evaluate(async () => {
    const r = await fetch(`/xrpc/app.bsky.actor.searchActors?q=${encodeURIComponent('kamado')}`);
    return { hdr: r.headers.get('x-kotoba-sw'), body: await r.json() };
  });
  console.log(`chrome=${ver}  x-kotoba-sw=${served.hdr}`);
  ok(served.hdr === 'local-wasm', `searchActors answered by in-browser wasm (x-kotoba-sw: ${served.hdr})`);
  const acts = served.body.actors || [];
  ok(acts.length === 1 && acts[0].did === 'did:web:etzhayyim.com:actor:kamado',
     `kamado resolved in real Chrome → ${acts[0]?.did}`);
  ok(/竈|Kamado/.test(acts[0]?.displayName || ''), `displayName = ${acts[0]?.displayName}`);

  // node.status proves it is genuinely the local wasm node, not a network fallback.
  const status = await page.evaluate(async () =>
    (await fetch('/xrpc/com.etzhayyim.apps.kotoba.node.status')).json());
  ok((status.count || 0) >= 100, `local wasm node holds the seeded corpus (datoms=${status.count})`);

  await page.screenshot({ path: join(here, 'serve', 'proof-screenshot.png') });
  console.log('screenshot → serve/proof-screenshot.png');
} finally {
  await browser.close();
  server.close();
}
console.log(`\n${fails === 0 ? 'ALL PASS' : fails + ' FAILED'} — kotoba node ran in real Chrome, resolved kamado client-side.`);
process.exit(fails === 0 ? 0 : 1);
