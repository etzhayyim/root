import { test, expect } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL || 'https://g00h5zto.etzhayyim.com';

test.use({
	viewport: { width: 390, height: 844 },
	colorScheme: 'dark',
});

// NOTE: Legacy routes (/talk, /channel/*, /apps/*, /post/*, /embed/*, /video-feed,
// /topic/*, /saved, /public-companies) have been fully removed per CLAUDE.md.
// These tests verify that current Bluesky-compatible routes remain stable.

test.describe('Stable routes do not redirect', () => {
	test('/ does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/');
	});

	test('/profile/testuser does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/profile/testuser`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/profile/testuser');
	});

	test('/messages does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/messages`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/messages');
	});

	test('/search does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/search`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/search');
	});

	test('/notifications does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/notifications`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/notifications');
	});

	test('/feeds does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/feeds`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/feeds');
	});

	test('/settings does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/settings`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/settings');
	});

	test('/privacy does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/privacy`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/privacy');
	});

	test('/terms does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/terms`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/terms');
	});

	test('/welcome does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/welcome`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/welcome');
	});

	test('/moderation does not redirect', async ({ page }) => {
		await page.goto(`${BASE}/moderation`, { waitUntil: 'load', timeout: 30000 });
		const finalUrl = new URL(page.url());
		expect(finalUrl.pathname).toBe('/moderation');
	});
});
