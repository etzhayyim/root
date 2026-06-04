import { test, expect } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL ?? 'https://yoro.etzhayyim.com';

test.use({
	viewport: { width: 390, height: 844 },
	colorScheme: 'dark',
});

// ─── Feed Loading ────────────────────────────────────────────────────────────

test.describe('Vibes feed', () => {
	test('posts load within 10s (no perpetual skeleton)', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		// Skeleton should appear initially
		const skeleton = page.locator('[class*="skeleton"], [class*="Skeleton"]').first();
		await expect(skeleton).toBeVisible({ timeout: 3000 });

		// Posts should load within 10s (SvelteKit hydration + PDS API call)
		const postCard = page.locator('[class*="touch-manipulation"]').first();
		await expect(postCard).toBeVisible({ timeout: 10_000 });
	});

	test('Discover tab shows at least 1 post', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		// Wait for feed to load
		const posts = page.locator('[class*="touch-manipulation"]');
		await expect(posts.first()).toBeVisible({ timeout: 10_000 });

		const count = await posts.count();
		expect(count).toBeGreaterThan(0);
	});

	test('feed error state shows retry button (not perpetual skeleton)', async ({ page }) => {
		// Block PDS API to simulate failure
		await page.route('**/xrpc/app.bsky.feed.getDiscoverFeed', (route) =>
			route.fulfill({ status: 500, body: '{"error":"test"}' }),
		);
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		// Should show error state with retry button
		const retryButton = page.getByRole('button', { name: '再試行' });
		await expect(retryButton).toBeVisible({ timeout: 10_000 });
	});
});

// ─── Tab Bar ─────────────────────────────────────────────────────────────────

test.describe('Tab bar', () => {
	test('tab bar stays at viewport bottom (flexbox layout)', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		// Wait for tab bar to render
		const nav = page.locator('nav[role="tablist"]');
		await expect(nav).toBeVisible({ timeout: 5000 });

		// Tab bar bottom edge should be at or near viewport bottom (within safe area)
		const box = await nav.boundingBox();
		expect(box).toBeTruthy();
		const viewportHeight = 844; // matches playwright config
		const bottomEdge = box!.y + box!.height;
		// Allow up to 34px for safe area inset
		expect(bottomEdge).toBeGreaterThan(viewportHeight - 34);
		expect(bottomEdge).toBeLessThanOrEqual(viewportHeight + 2);
	});

	test('tab bar is visible after scrolling', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		// Wait for posts to load
		const posts = page.locator('[class*="touch-manipulation"]');
		await expect(posts.first()).toBeVisible({ timeout: 10_000 });

		// Scroll down
		await page.evaluate(() => {
			const main = document.querySelector('main');
			if (main) main.scrollTop = 2000;
		});
		await page.waitForTimeout(500);

		// Tab bar should still be visible
		const nav = page.locator('nav[role="tablist"]');
		await expect(nav).toBeVisible();
		await expect(nav).toBeInViewport();
	});

	test('tab bar has opaque background (not transparent)', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		const nav = page.locator('nav[role="tablist"]');
		await expect(nav).toBeVisible({ timeout: 5000 });

		// Background should be opaque (alpha >= 0.95)
		const bgAlpha = await nav.evaluate((el) => {
			const cs = window.getComputedStyle(el);
			const bg = cs.backgroundColor;
			// Parse rgba(r, g, b, a) or rgb(r, g, b)
			const match = bg.match(/rgba?\([\d.]+,\s*[\d.]+,\s*[\d.]+(?:,\s*([\d.]+))?\)/);
			return match?.[1] !== undefined ? parseFloat(match[1]) : 1;
		});
		expect(bgAlpha).toBeGreaterThanOrEqual(0.95);
	});

	test('all 5 tabs are present', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		const nav = page.locator('nav[role="tablist"]');
		await expect(nav).toBeVisible({ timeout: 5000 });

		for (const label of ['Vibes', 'Search', 'Talk', 'Apps', 'Profile']) {
			await expect(nav.getByRole('tab', { name: label })).toBeVisible();
		}
	});

	test('tab navigation works', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		const nav = page.locator('nav[role="tablist"]');
		await expect(nav).toBeVisible({ timeout: 5000 });

		// Click Search tab
		await nav.getByRole('tab', { name: 'Search' }).click();
		await page.waitForTimeout(500);
		expect(page.url()).toContain('/search');

		// Click Vibes tab to go back
		await nav.getByRole('tab', { name: 'Vibes' }).click();
		await page.waitForTimeout(500);
		expect(page.url().endsWith('/')).toBeTruthy();
	});
});

// ─── Visual Regression ───────────────────────────────────────────────────────

test.describe('Visual regression', () => {
	test('vibes feed screenshot', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		// Wait for posts to load
		const posts = page.locator('[class*="touch-manipulation"]');
		await expect(posts.first()).toBeVisible({ timeout: 10_000 });
		await page.waitForTimeout(1000); // Let animations settle

		await expect(page).toHaveScreenshot('vibes-feed.png', {
			fullPage: false,
			maxDiffPixelRatio: 0.05,
		});
	});

	test('tab bar screenshot', async ({ page }) => {
		await page.goto(BASE, { waitUntil: 'domcontentloaded' });

		const nav = page.locator('nav[role="tablist"]');
		await expect(nav).toBeVisible({ timeout: 5000 });

		await expect(nav).toHaveScreenshot('tab-bar.png', {
			maxDiffPixelRatio: 0.05,
		});
	});
});
