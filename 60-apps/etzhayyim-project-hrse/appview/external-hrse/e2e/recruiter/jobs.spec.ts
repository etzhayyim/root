// @etzhayyim/cyber-freelance#RecruiterJobsE2E
// リクルーター案件管理ページのE2Eテスト

import { test, expect } from "@playwright/test";

test.describe("Recruiter Jobs Page", () => {
	test.beforeEach(async ({ page }) => {
		await page.goto("/recruiter/jobs");
	});

	test("should display jobs list", async ({ page }) => {
		await expect(page.getByText(/案件/i)).toBeVisible();
	});

	test("should allow creating new job", async ({ page }) => {
		const createButton = page.getByRole("button", { name: /新規作成/i });
		await expect(createButton).toBeVisible();

		await createButton.click();
		await expect(page).toHaveURL(/\/recruiter\/jobs\/new/);
	});

	test("should allow editing job", async ({ page }) => {
		// 案件編集のテストを実装
		const editButton = page.locator('[data-testid="edit-job"]').first();
		await expect(editButton).toBeVisible();
	});

	test("should display proposals for job", async ({ page }) => {
		// 案件の応募一覧表示テストを実装
		const proposalsLink = page.locator('[data-testid="view-proposals"]').first();
		await expect(proposalsLink).toBeVisible();

		await proposalsLink.click();
		await expect(page).toHaveURL(/\/recruiter\/jobs\/[^/]+\/proposals/);
	});
});





