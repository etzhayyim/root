import { test, expect } from '@playwright/test';

const TARGET_PROFILE = '/profile/uqpel6i6.etzhayyim.com';

test.describe('Guest projector chat', () => {
	test.use({ storageState: { cookies: [], origins: [] } });

	test('logged-out actor profile exposes Gemma E2B web inference chat', async ({ page }) => {
		await page.addInitScript(() => {
			localStorage.clear();
			sessionStorage.clear();
		});

		await page.goto(TARGET_PROFILE, { waitUntil: 'networkidle' });

		const input = page.getByPlaceholder(/Gemma E2B \/ Web推論/).first();
		await expect(input).toBeVisible({ timeout: 20_000 });
		await expect(page.getByText(/ログインして.*会話/)).toHaveCount(0);

		await input.fill('こんにちは');
		await expect(page.getByRole('button', { name: '送信' }).first()).toBeEnabled();
	});
});
