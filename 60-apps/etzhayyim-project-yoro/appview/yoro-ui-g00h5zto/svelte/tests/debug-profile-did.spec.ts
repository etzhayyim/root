import { test, expect } from '@playwright/test';

/**
 * Debug: profile page error for did:web:atproto.etzhayyim.com:user:m9r4k8m0-etzhayyim-ai
 */

const TARGET_URL = '/profile/did%3Aweb%3Aatproto.etzhayyim.com%3Auser%3Am9r4k8m0-etzhayyim-ai';
const DECODED_DID = 'did:web:atproto.etzhayyim.com:user:m9r4k8m0-etzhayyim-ai';

test.describe('Debug: profile did:web:atproto.etzhayyim.com:user:*', () => {
	test('capture page errors and network failures', async ({ page }) => {
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
			if (res.status() >= 400) {
				failedRequests.push(`HTTP ${res.status()}: ${res.request().method()} ${res.url()}`);
			}
		});

		const response = await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 30000 });

		console.log('\n=== SSR Response ===');
		console.log(`Status: ${response?.status()}`);
		console.log(`URL: ${response?.url()}`);

		// Wait for client-side hydration and profile load
		await page.waitForTimeout(5000);

		console.log('\n=== Page Errors ===');
		errors.forEach((e) => console.log(e));

		console.log('\n=== Console Warnings/Errors ===');
		consoleMessages.forEach((m) => console.log(m));

		console.log('\n=== Failed/Error Requests ===');
		failedRequests.forEach((r) => console.log(r));

		// Check for visible error message on page
		const errorText = await page.locator('text=失敗').first().textContent().catch((_err) => null);
		const errorText2 = await page.locator('text=error').first().textContent().catch((_err) => null);
		const errorText3 = await page.locator('text=Error').first().textContent().catch((_err) => null);
		console.log('\n=== Visible Error Text ===');
		if (errorText) console.log(`Found: ${errorText}`);
		if (errorText2) console.log(`Found: ${errorText2}`);
		if (errorText3) console.log(`Found: ${errorText3}`);

		// Screenshot
		await page.screenshot({ path: 'test-results/debug-profile-did.png', fullPage: true });
		console.log('\nScreenshot saved: test-results/debug-profile-did.png');

		// Dump page title and body text snippet
		const title = await page.title();
		console.log(`\n=== Page Title: ${title} ===`);

		const bodyText = await page.locator('body').innerText().catch((_err) => '(empty)');
		console.log(`\n=== Page Body (first 2000 chars) ===\n${bodyText.slice(0, 2000)}`);
	});

	test('SSR server load returns valid data', async ({ request }) => {
		const res = await request.get(TARGET_URL, {
			headers: { Accept: 'text/html' },
		});
		console.log(`\n=== SSR Status: ${res.status()} ===`);
		const html = await res.text();

		// Check for OG tags
		const ogTitle = html.match(/<meta property="og:title" content="([^"]*)"/)?.[1];
		const ogDesc = html.match(/<meta property="og:description" content="([^"]*)"/)?.[1];
		console.log(`OG Title: ${ogTitle}`);
		console.log(`OG Description: ${ogDesc}`);

		// Check for SSR error patterns
		const hasError500 = html.includes('500') && html.includes('Internal');
		const hasSvelteError = html.includes('__error') || html.includes('SvelteKitError');
		console.log(`Has 500 error: ${hasError500}`);
		console.log(`Has SvelteKit error: ${hasSvelteError}`);

		// Print first 3000 chars of HTML
		console.log(`\n=== HTML (first 3000 chars) ===\n${html.slice(0, 3000)}`);

		expect(res.status()).toBeLessThan(500);
	});

	test('PDS profile resolution for this DID', async ({ request }) => {
		// Test the PDS query that the profile page makes
		const res = await request.post('https://atproto.etzhayyim.com/xrpc/app.bsky.actor.getProfile', {
			headers: { 'Content-Type': 'application/json' },
			data: { actor: DECODED_DID },
		});
		console.log(`\n=== PDS Query Status: ${res.status()} ===`);
		const body = await res.text();
		console.log(`PDS Response: ${body.slice(0, 2000)}`);
	});

	test('manifest fetch for atproto.etzhayyim.com', async ({ request }) => {
		// This is what the profile page tries — atproto.etzhayyim.com is not an App
		const res = await request.get('https://atproto.etzhayyim.com/_app/meta', {
			headers: { Accept: 'application/json' },
			timeout: 5000,
		}).catch((e) => ({ status: () => 0, text: async () => `FETCH_ERROR: ${e.message}` }));
		console.log(`\n=== Manifest Status: ${res.status()} ===`);
		const body = await res.text();
		console.log(`Manifest Response: ${body.slice(0, 1000)}`);
	});

	test('resolveHandle for the DID', async ({ request }) => {
		const res = await request.post(
			'https://atproto.etzhayyim.com/xrpc/com.atproto.identity.resolveHandle',
			{ headers: { 'Content-Type': 'application/json' }, data: { handle: DECODED_DID } },
		);
		console.log(`\n=== resolveHandle Status: ${res.status()} ===`);
		const body = await res.text();
		console.log(`resolveHandle Response: ${body.slice(0, 1000)}`);
	});

	test('getProfile SSR for the DID', async ({ request }) => {
		// This is the server-side load call
		const res = await request.post(
			'https://atproto.etzhayyim.com/xrpc/app.bsky.actor.getProfile',
			{ headers: { 'Content-Type': 'application/json' }, data: { actor: DECODED_DID } },
		);
		console.log(`\n=== getProfile Status: ${res.status()} ===`);
		const body = await res.text();
		console.log(`getProfile Response: ${body.slice(0, 1000)}`);
	});
});
