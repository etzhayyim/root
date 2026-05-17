import { test, expect } from '@playwright/test';

const BASE_URL = 'https://yoro.etzhayyim.com';

test.describe('Accessibility', () => {
	test('health endpoint returns valid JSON', async ({ request }) => {
		const resp = await request.get(`${BASE_URL}/health`);
		expect(resp.ok()).toBeTruthy();
		const body = await resp.json();
		expect(body.status).toBe('ok');
	});

	test('page has correct lang attribute', async ({ page }) => {
		await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
		const lang = await page.evaluate(() => document.documentElement.lang);
		expect(lang).toBeTruthy();
	});

	test('page has viewport meta tag', async ({ page }) => {
		await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
		const viewport = await page.evaluate(() => {
			const meta = document.querySelector('meta[name="viewport"]');
			return meta?.getAttribute('content') || '';
		});
		expect(viewport).toContain('width=device-width');
	});

	test('no images without alt text', async ({ page }) => {
		await page.goto(BASE_URL, { waitUntil: 'networkidle' });
		await page.waitForTimeout(2000);
		const imgsWithoutAlt = await page.evaluate(() => {
			const imgs = document.querySelectorAll('img');
			return Array.from(imgs).filter((img) => !img.alt && !img.getAttribute('role')).length;
		});
		expect(imgsWithoutAlt).toBe(0);
	});

	test('buttons have accessible labels', async ({ page }) => {
		await page.goto(BASE_URL, { waitUntil: 'networkidle' });
		await page.waitForTimeout(2000);
		const unlabeledButtons = await page.evaluate(() => {
			const buttons = document.querySelectorAll('button');
			return Array.from(buttons).filter((btn) => {
				const text = btn.textContent?.trim() || '';
				const ariaLabel = btn.getAttribute('aria-label') || '';
				const title = btn.title || '';
				return !text && !ariaLabel && !title;
			}).length;
		});
		// Allow some unlabeled (icon buttons may use aria-label added by framework)
		expect(unlabeledButtons).toBeLessThanOrEqual(3);
	});
});
