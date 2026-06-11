import { test, expect } from '@playwright/test';

/**
 * Debug: maps.etzhayyim.com hero section not showing map iframe
 */

const TARGET_URL = '/profile/did%3Aweb%3Amaps.etzhayyim.com';
const DECODED_DID = 'did:web:maps.etzhayyim.com';

test.describe('Debug: maps.etzhayyim.com hero section', () => {
	test('capture hero section state and network', async ({ page }) => {
		const errors: string[] = [];
		const consoleMessages: string[] = [];
		const failedRequests: string[] = [];

		page.on('pageerror', (err) => {
			errors.push(`PAGE_ERROR: ${err.message}`);
		});

		page.on('console', (msg) => {
			if (msg.type() === 'error' || msg.type() === 'warn') {
				consoleMessages.push(`${msg.type().toUpperCase()}: ${msg.text()}`);
			}
		});

		page.on('requestfailed', (req) => {
			failedRequests.push(`FAILED: ${req.method()} ${req.url()} — ${req.failure()?.errorText}`);
		});

		page.on('response', (res) => {
			const url = res.url();
			if (url.includes('_app/meta') || url.includes('_app/meta') || url.includes('maps.etzhayyim.com') || url.includes('uqpel6i6')) {
				console.log(`RESPONSE: ${res.status()} ${res.request().method()} ${url}`);
			}
			if (res.status() >= 400) {
				failedRequests.push(`HTTP ${res.status()}: ${res.request().method()} ${url}`);
			}
		});

		const response = await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 30000 });

		console.log('\n=== SSR Response ===');
		console.log(`Status: ${response?.status()}`);
		console.log(`URL: ${response?.url()}`);

		// Wait for client-side hydration and async loadAppPreview
		await page.waitForTimeout(5000);

		console.log('\n=== Page Errors ===');
		errors.forEach((e) => console.log(e));

		console.log('\n=== Console Warnings/Errors ===');
		consoleMessages.forEach((m) => console.log(m));

		console.log('\n=== Failed/Error Requests ===');
		failedRequests.forEach((r) => console.log(r));

		// Check for iframe in hero section
		const heroIframe = await page.locator('iframe').count();
		console.log(`\n=== iframe count: ${heroIframe} ===`);

		// Check iframe src attributes
		const iframeSrcs = await page.locator('iframe').evaluateAll((els) =>
			els.map((el) => ({ src: el.getAttribute('src'), width: el.offsetWidth, height: el.offsetHeight }))
		);
		console.log('iframe details:', JSON.stringify(iframeSrcs, null, 2));

		// Check hero section
		const heroSection = await page.locator('[class*="hero"], [class*="Hero"], [data-hero]').count();
		console.log(`hero section elements: ${heroSection}`);

		// Check for "status" hero (the fallback for system type)
		const statusBadge = await page.locator('text=online, text=offline, text=healthy, text=status').count();
		console.log(`status badge elements: ${statusBadge}`);

		// Screenshot
		await page.screenshot({ path: 'test-results/debug-maps-hero.png', fullPage: true });
		console.log('\nScreenshot saved: test-results/debug-maps-hero.png');

		// Page title
		const title = await page.title();
		console.log(`\n=== Page Title: ${title} ===`);

		// Body text snippet
		const bodyText = await page.locator('body').innerText().catch((_err) => '(empty)');
		console.log(`\n=== Page Body (first 2000 chars) ===\n${bodyText.slice(0, 2000)}`);
	});

	test('/_app/meta endpoints', async ({ request }) => {
		// Vanity host
		console.log('\n=== maps.etzhayyim.com/_app/meta ===');
		const vanity = await request.get('https://maps.etzhayyim.com/_app/meta');
		console.log(`Status: ${vanity.status()}`);
		console.log(`Body: ${await vanity.text()}`);

		// Nanoid host
		console.log('\n=== uqpel6i6.etzhayyim.com/_app/meta ===');
		const nanoid = await request.get('https://uqpel6i6.etzhayyim.com/_app/meta');
		console.log(`Status: ${nanoid.status()}`);
		console.log(`Body: ${await nanoid.text()}`);

		// Embed URL
		console.log('\n=== uqpel6i6.etzhayyim.com/?embed=1 ===');
		const embed = await request.get('https://uqpel6i6.etzhayyim.com/?embed=1');
		console.log(`Status: ${embed.status()}`);
		const html = await embed.text();
		console.log(`HTML (first 500 chars): ${html.slice(0, 500)}`);
	});

	test('/_app/meta fallback', async ({ request }) => {
		// This should 404 (host-sdk doesn't serve it)
		console.log('\n=== maps.etzhayyim.com/_app/meta ===');
		const res = await request.get('https://maps.etzhayyim.com/_app/meta').catch((e) =>
			({ status: () => 0, text: async () => `FETCH_ERROR: ${e.message}` })
		);
		console.log(`Status: ${res.status()}`);
		console.log(`Body: ${(await res.text()).slice(0, 500)}`);
	});

	test('PDS getProfile for maps DID', async ({ request }) => {
		const res = await request.post('https://atproto.etzhayyim.com/xrpc/app.bsky.actor.getProfile', {
			headers: { 'Content-Type': 'application/json' },
			data: { actor: DECODED_DID },
		});
		console.log(`\n=== getProfile Status: ${res.status()} ===`);
		const body = await res.text();
		console.log(`Response: ${body.slice(0, 2000)}`);
	});
});
