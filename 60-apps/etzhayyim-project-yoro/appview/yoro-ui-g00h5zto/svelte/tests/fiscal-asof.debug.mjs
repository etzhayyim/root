// Extension-free live verification of the kotoba-native Resource Flow + as-of,
// driven through a REAL headless Chromium (Playwright) against the dev server.
// Proves the in-browser kotoba-sw.js intercepts com.etzhayyim.yoro.fiscal.getResourceFlow
// and applies Datomic-style as-of over the `:yoro.fiscal/*` datom log.
//
// Run: node tests/fiscal-asof.debug.mjs   (dev server must be on :5178)
import { chromium } from '@playwright/test';

const BASE = 'http://127.0.0.1:5178';
const DID = 'did:web:etzhayyim.com:actor:ooyake';
const NSID = 'com.etzhayyim.yoro.fiscal.getResourceFlow';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext();
const page = await ctx.newPage();

// surface kotoba-sw boot logs for debugging
page.on('console', (m) => {
	const t = m.text();
	if (/kotoba|fiscal|hydrat|datom/i.test(t)) console.log('  [browser]', t);
});

console.log('→ load app root (registers + activates kotoba-sw.js)…');
await page.goto(BASE + '/', { waitUntil: 'load' });

// wait until the SW controls the page and has hydrated the seed (poll the fiscal
// endpoint through the SW until it returns data, or give up after ~20s).
async function fiscal(asOf) {
	return page.evaluate(
		async ({ base, nsid, did, asOf }) => {
			const u = new URL(`/xrpc/${nsid}`, base);
			u.searchParams.set('did', did);
			if (asOf) u.searchParams.set('asOf', asOf);
			const r = await fetch(u, { headers: { accept: 'application/json' } });
			return { status: r.status, src: r.headers.get('x-kotoba-src'), sw: r.headers.get('x-kotoba-sw'), body: await r.json().catch(() => null) };
		},
		{ base: BASE, nsid: NSID, did: DID, asOf },
	);
}

let ready = null;
for (let i = 0; i < 40; i++) {
	const res = await fiscal('');
	if (res.sw && res.body && (res.body.totalIn > 0 || res.body.incoming?.length)) { ready = res; break; }
	await sleep(500);
}

if (!ready) {
	const probe = await fiscal('');
	console.error('✘ SW did not return fiscal data in time. Last probe:', JSON.stringify(probe));
	await browser.close();
	process.exit(1);
}

console.log(`✓ SW intercepting (x-kotoba-sw=${ready.sw}, x-kotoba-src=${ready.src})`);

const cur = await fiscal('');
const y2025 = await fiscal('2025-06-01');
const y2024 = await fiscal('2024-01-01');

const sum = (r) => ({
	in: r.body.incoming.length,
	totalIn: r.body.totalIn,
	out: r.body.outgoing.length,
	totalOut: r.body.totalOut,
	ubo: r.body.uboParents.length,
});
console.log('\n=== as-of via REAL browser SW ===');
console.log('current   :', JSON.stringify(sum(cur)));
console.log('2025-06-01:', JSON.stringify(sum(y2025)));
console.log('2024-01-01:', JSON.stringify(sum(y2024)));

// assertions: append-only time-travel must shrink the set going back in time
const ok =
	cur.body.totalIn === 2700000000 &&
	cur.body.incoming.length === 2 &&
	y2025.body.incoming.length === 1 &&
	y2025.body.totalIn === 1200000000 &&
	y2025.body.outgoing.length === 0 &&
	y2024.body.incoming.length === 0;
console.log(ok ? '\n✓ ASSERTIONS PASS — as-of time-travel verified in a real browser' : '\n✘ ASSERTIONS FAILED');

// bonus: render the profile + Resource Flow tab and screenshot (best-effort)
try {
	await page.goto(`${BASE}/profile/${DID}`, { waitUntil: 'load' });
	await page.waitForTimeout(2500);
	const tab = page.getByText(/Resource Flow|資金フロー/i).first();
	if (await tab.count()) {
		await tab.click().catch(() => {});
		await page.waitForTimeout(1500);
	}
	await page.screenshot({ path: 'tests/fiscal-asof.screenshot.png', fullPage: true });
	console.log('✓ screenshot → tests/fiscal-asof.screenshot.png');
} catch (e) {
	console.log('… UI screenshot skipped:', String(e).slice(0, 120));
}

await browser.close();
process.exit(ok ? 0 : 1);
