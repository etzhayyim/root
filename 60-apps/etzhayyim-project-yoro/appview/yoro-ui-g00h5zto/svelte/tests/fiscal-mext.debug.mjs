// Real-browser verification that the kanae/danjo-projected JP gov fiscal datoms
// (文部科学省 / MEXT) render through kotoba-sw.js with as-of time-travel.
// Run: node tests/fiscal-mext.debug.mjs   (dev server on :5178, seed merged)
import { chromium } from '@playwright/test';

const BASE = 'http://127.0.0.1:5178';
const DID = 'did:web:etzhayyim.com:actor:gov-jp-mext';
const NSID = 'com.etzhayyim.yoro.fiscal.getResourceFlow';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext()).newPage();
await page.goto(BASE + '/', { waitUntil: 'load' });

async function fiscal(asOf) {
	return page.evaluate(async ({ base, nsid, did, asOf }) => {
		const u = new URL(`/xrpc/${nsid}`, base);
		u.searchParams.set('did', did);
		if (asOf) u.searchParams.set('asOf', asOf);
		const r = await fetch(u, { headers: { accept: 'application/json' } });
		return { sw: r.headers.get('x-kotoba-sw'), body: await r.json().catch(() => null) };
	}, { base: BASE, nsid: NSID, did: DID, asOf });
}

let ready = null;
for (let i = 0; i < 40; i++) {
	const r = await fiscal('');
	if (r.sw && r.body && (r.body.incoming?.length || r.body.outgoing?.length)) { ready = r; break; }
	await sleep(500);
}
if (!ready) { console.error('✘ no MEXT fiscal data via SW:', JSON.stringify(await fiscal(''))); await browser.close(); process.exit(1); }

const sum = (r) => ({ in: r.body.incoming.length, totalIn: r.body.totalIn, out: r.body.outgoing.length, totalOut: r.body.totalOut });
const cur = await fiscal(''), y2023 = await fiscal('2023-12-31'), y2022 = await fiscal('2022-01-01');
console.log('=== MEXT fiscal via REAL browser SW (kanae/danjo pipeline) ===');
console.log('current     :', JSON.stringify(sum(cur)));
console.log('asOf 2023-12-31:', JSON.stringify(sum(y2023)));
console.log('asOf 2022-01-01:', JSON.stringify(sum(y2022)));

const ok =
	cur.body.incoming.length === 2 && cur.body.totalIn === 10758300000000 &&
	cur.body.outgoing.length === 3 && cur.body.totalOut === 3555700000000 &&
	y2023.body.incoming.length === 1 && y2023.body.totalIn === 5294000000000 &&
	y2023.body.outgoing.length === 1 &&
	y2022.body.incoming.length === 0 && y2022.body.outgoing.length === 0;
console.log(ok ? '\n✓ PASS — real JP gov fiscal datoms + as-of verified in a real browser' : '\n✘ FAIL');

try {
	await page.goto(`${BASE}/profile/${DID}`, { waitUntil: 'load' });
	await page.waitForTimeout(2500);
	const tab = page.getByText(/Resource Flow|資金フロー/i).first();
	if (await tab.count()) { await tab.click().catch(() => {}); await page.waitForTimeout(1200); }
	await page.screenshot({ path: 'tests/fiscal-mext.screenshot.png', fullPage: true });
	console.log('✓ screenshot → tests/fiscal-mext.screenshot.png');
} catch (e) { console.log('… screenshot skipped:', String(e).slice(0, 100)); }

await browser.close();
process.exit(ok ? 0 : 1);
