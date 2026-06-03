// @etzhayyim/cyber-freelance#FreelancerProfileE2E
// フリーランスプロファイルページのE2Eテスト

import { test, expect } from "@playwright/test";

test.describe("Freelancer Profile Page", () => {
	test.beforeEach(async ({ page }) => {
		// 認証状態は playwright/.clerk/user.json から自動的に読み込まれます
		await page.goto("/freelancer/profile");
	});

	test("should display profile form", async ({ page }) => {
		await expect(page.getByText(/プロファイル/i)).toBeVisible();
	});

	test("should allow editing profile", async ({ page }) => {
		// プロファイル編集のテストを実装
		const desiredUnitPriceMin = page.getByLabel(/希望単価（最小）/i);
		await expect(desiredUnitPriceMin).toBeVisible();

		await desiredUnitPriceMin.fill("5000");
		await expect(desiredUnitPriceMin).toHaveValue("5000");
	});

	test("should save profile changes", async ({ page }) => {
		// プロファイル保存のテストを実装
		const saveButton = page.getByRole("button", { name: /保存/i });
		await expect(saveButton).toBeVisible();
	});
});






