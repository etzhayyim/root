import { test, expect } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL ?? 'https://yoro.etzhayyim.com';
const DIR = '/tmp/yoro-iphone-screenshots';

/**
 * iPhone Visual UI/UX E2E Tests
 *
 * Validates mobile layout on iPhone SE / 12 / 14 Pro Max (via config projects):
 * - No horizontal scroll (overflow-x fix)
 * - Tab bar pinned to viewport bottom
 * - Header: no duplicate Credits/Tuner
 * - Content fits within viewport width
 */

// ─── No Horizontal Scroll ────────────────────────────────────────────────────

test('no horizontal scroll on home feed', async ({ page }, testInfo) => {
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });
	await page.waitForTimeout(3000);

	const hasHorizontalScroll = await page.evaluate(() =>
		document.documentElement.scrollWidth > document.documentElement.clientWidth
	);
	expect(hasHorizontalScroll).toBe(false);

	await page.screenshot({ path: `${DIR}/${testInfo.project.name}-home.png`, fullPage: false });
});

test('no horizontal scroll after feed loads', async ({ page }) => {
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });

	const post = page.locator('[class*="touch-manipulation"]').first();
	await expect(post).toBeVisible({ timeout: 10_000 });
	await page.waitForTimeout(500);

	const hasHorizontalScroll = await page.evaluate(() =>
		document.documentElement.scrollWidth > document.documentElement.clientWidth
	);
	expect(hasHorizontalScroll).toBe(false);
});

test('no element exceeds viewport width', async ({ page }) => {
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });
	await page.waitForTimeout(3000);

	const overflowingElements = await page.evaluate(() => {
		const vw = document.documentElement.clientWidth;
		const all = document.querySelectorAll('*');
		const overflows: string[] = [];
		for (const el of all) {
			const style = window.getComputedStyle(el);
			// Skip absolutely/fixed positioned elements (shimmer overlays, etc.) — visually clipped by parent
			if (style.position === 'absolute' || style.position === 'fixed') continue;
			const rect = el.getBoundingClientRect();
			if (rect.right > vw + 2) {
				const tag = el.tagName.toLowerCase();
				const cls = el.className?.toString().slice(0, 60) || '';
				overflows.push(`${tag}.${cls} right=${Math.round(rect.right)} vw=${vw}`);
			}
		}
		return overflows.slice(0, 10);
	});
	expect(overflowingElements).toEqual([]);
});

// ─── Tab Bar Position ────────────────────────────────────────────────────────

test('tab bar pinned to viewport bottom', async ({ page }) => {
	// Skip splash screen
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });
	await page.evaluate(() => {
		window.sessionStorage.setItem('yoro-splash-seen-v1', '1');
	});
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });

	// Wait for feed to load (splash dismissed, layout settled)
	const post = page.locator('[class*="touch-manipulation"]').first();
	await expect(post).toBeVisible({ timeout: 10_000 });

	const nav = page.locator('nav[role="tablist"]');
	await expect(nav).toBeVisible({ timeout: 5000 });

	const box = await nav.boundingBox();
	expect(box).toBeTruthy();

	const viewport = page.viewportSize()!;
	// Tab bar top should be in the lower portion of the screen
	expect(box!.y).toBeGreaterThan(viewport.height * 0.8);
});

test('tab bar stays pinned after scrolling', async ({ page }) => {
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });

	const post = page.locator('[class*="touch-manipulation"]').first();
	await expect(post).toBeVisible({ timeout: 10_000 });

	await page.evaluate(() => {
		const main = document.querySelector('main');
		if (main) main.scrollTop = 3000;
	});
	await page.waitForTimeout(500);

	const nav = page.locator('nav[role="tablist"]');
	await expect(nav).toBeVisible();

	// Verify tab bar is near the bottom (allow for safe area + WebKit URL bar shifts)
	const box = await nav.boundingBox();
	expect(box).toBeTruthy();
	const viewport = page.viewportSize()!;
	// Tab bar top should be in the lower portion of the viewport
	expect(box!.y).toBeGreaterThan(viewport.height * 0.7);
});

test('tab bar does not shift when content grows', async ({ page }) => {
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });

	const nav = page.locator('nav[role="tablist"]');
	await expect(nav).toBeVisible({ timeout: 5000 });

	const boxBefore = await nav.boundingBox();

	const post = page.locator('[class*="touch-manipulation"]').first();
	await expect(post).toBeVisible({ timeout: 10_000 });
	await page.waitForTimeout(500);

	const boxAfter = await nav.boundingBox();
	expect(Math.abs(boxAfter!.y - boxBefore!.y)).toBeLessThan(2);
});

// ─── Header: No Duplicates ───────────────────────────────────────────────────

test('header has at most one Credits badge', async ({ page }) => {
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });
	await page.waitForTimeout(3000);

	const creditsCount = await page.locator('header').locator('text=Credits').count();
	expect(creditsCount).toBeLessThanOrEqual(1);
});

test('header fits within viewport width', async ({ page }) => {
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });
	await page.waitForTimeout(2000);

	const header = page.locator('header').first();
	await expect(header).toBeVisible();

	const box = await header.boundingBox();
	const viewport = page.viewportSize()!;
	expect(box!.width).toBeLessThanOrEqual(viewport.width + 1);
});

// ─── Layout Integrity ────────────────────────────────────────────────────────

test('content area fills between header and tab bar', async ({ page }) => {
	await page.goto(BASE, { waitUntil: 'domcontentloaded' });
	await page.waitForTimeout(2000);

	const header = page.locator('header').first();
	const nav = page.locator('nav[role="tablist"]');
	const main = page.locator('main').first();

	await expect(header).toBeVisible();
	await expect(nav).toBeVisible();
	await expect(main).toBeVisible();

	const headerBox = await header.boundingBox();
	const navBox = await nav.boundingBox();
	const mainBox = await main.boundingBox();

	expect(mainBox!.y).toBeGreaterThanOrEqual(headerBox!.y + headerBox!.height - 2);
	expect(mainBox!.y + mainBox!.height).toBeLessThanOrEqual(navBox!.y + 2);
});

// ─── All Tabs Screenshots ───────────────────────────────────────────────────

const TABS = [
	{ path: '/', name: 'vibes' },
	{ path: '/search', name: 'search' },
	{ path: '/convo', name: 'talk' },
	{ path: '/apps', name: 'apps' },
	{ path: '/profile', name: 'profile' },
];

for (const tab of TABS) {
	test(`${tab.name} tab — no overflow + tab bar visible`, async ({ page }, testInfo) => {
		await page.goto(`${BASE}${tab.path}`, { waitUntil: 'domcontentloaded' });
		await page.waitForTimeout(2000);

		const hasHScroll = await page.evaluate(() =>
			document.documentElement.scrollWidth > document.documentElement.clientWidth
		);
		expect(hasHScroll).toBe(false);

		const nav = page.locator('nav[role="tablist"]');
		await expect(nav).toBeVisible({ timeout: 5000 });

		await page.screenshot({
			path: `${DIR}/${testInfo.project.name}-${tab.name}.png`,
			fullPage: false,
		});
	});
}
