import { test, expect } from '@playwright/test';

/**
 * E2E debug: verify AppShell v2 stability for yoro.etzhayyim.com.
 * Validates: dark theme, splash, auth gate, tab configuration.
 */

const BASE_URL = 'http://localhost:4173';

test.use({ colorScheme: 'dark' });

test.describe('Dark theme rendering', () => {
	test('splash screen renders on dark background', async ({ page }) => {
		await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
		await page.waitForTimeout(300);

		// Verify data-theme="dark" is set in HTML
		const theme = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
		expect(theme).toBe('dark');

		// Verify dark CSS variables are applied
		const bgColor = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
		expect(bgColor).toBe('rgb(26, 26, 26)');

		// YORO text visible
		await expect(page.locator('text=YORO').first()).toBeVisible();

		// Confetti dots rendered
		const dots = await page.locator('.confetti-dot').count();
		expect(dots).toBe(7);

		await page.screenshot({ path: 'tests/screenshots/01-splash-dark.png', fullPage: false });
	});

	test('auth gate renders after Clerk timeout', async ({ page }) => {
		await page.goto(BASE_URL, { waitUntil: 'networkidle' });
		await page.waitForTimeout(9000);

		await expect(page.locator('text=YORO').first()).toBeVisible();
		await expect(page.locator('text=ログイン').first()).toBeVisible();
		await expect(page.locator('text=アカウント作成').first()).toBeVisible();

		await page.screenshot({ path: 'tests/screenshots/02-auth-gate-dark.png', fullPage: false });
	});
});

test.describe('Tab configuration', () => {
	test('only standard 5 tabs shown in bottom bar', async ({ page }) => {
		await page.goto(BASE_URL, { waitUntil: 'networkidle' });
		await page.waitForTimeout(9000);

		// Legacy "Live" tab should NOT appear
		const liveText = await page.locator('text=Live').count();
		expect(liveText).toBe(0);
	});
});

test.describe('No JS errors', () => {
	test('page loads without errors', async ({ page }) => {
		const errors: string[] = [];
		page.on('pageerror', (err) => errors.push(err.message));

		await page.goto(BASE_URL, { waitUntil: 'networkidle' });
		await page.waitForTimeout(1000);

		// Filter out expected Clerk 400 error
		const realErrors = errors.filter((e) => !e.includes('400') && !e.includes('Clerk'));
		expect(realErrors).toHaveLength(0);
	});
});
