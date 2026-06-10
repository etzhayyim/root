import { chromium } from '@playwright/test';
const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext()).newPage();
page.on('console', (m) => { if (/kotoba/i.test(m.text())) console.log('  [browser]', m.text().slice(0, 140)); });
console.log('→ load https://etzhayyim.com/ …');
await page.goto('https://etzhayyim.com/', { waitUntil: 'load', timeout: 60000 });
// wait for the SW to control the page
await page.evaluate(async () => {
  if (!navigator.serviceWorker.controller) {
    await new Promise((res) => navigator.serviceWorker.addEventListener('controllerchange', res, { once: true }));
  }
});
console.log('→ SW controls the page; fetching timeline THROUGH the SW…');
const out = await page.evaluate(async () => {
  const r = await fetch('/xrpc/app.bsky.feed.getTimeline?limit=5');
  const tag = r.headers.get('x-kotoba-sw') || '(none — live passthrough)';
  const j = await r.json().catch(() => null);
  const dates = (j && j.feed ? j.feed : []).map((it) => it?.post?.record?.createdAt || it?.post?.indexedAt).slice(0, 5);
  return { status: r.status, tag, dates };
});
console.log('timeline via SW:', JSON.stringify(out, null, 1));
const swSrc = await page.evaluate(async () => (await (await fetch('/kotoba-sw.js')).text()).includes('mergeLiveFeed'));
console.log('SW script has mergeLiveFeed:', swSrc);
await browser.close();
const newest = out.dates[0] || '';
if (out.status === 200 && newest >= '2026-06-0 9') process.exit(0);
process.exit(out.status === 200 && newest > '2026-06-01' ? 0 : 1);
