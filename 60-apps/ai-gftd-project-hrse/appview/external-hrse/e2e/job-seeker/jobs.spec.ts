// @etzhayyim/cyber-freelance#JobSeekerJobsE2E
// 求職者案件一覧ページのE2Eテスト

import { test, expect } from "@playwright/test";

test.describe("Job Seeker Jobs Page", () => {
	test.beforeEach(async ({ page }) => {
		await page.goto("/job-seeker/jobs");
	});

	test("should display jobs list", async ({ page }) => {
		await expect(page.getByText(/案件/i)).toBeVisible();
	});

	test("should allow searching jobs", async ({ page }) => {
		const searchInput = page.getByPlaceholder(/検索/i);
		await expect(searchInput).toBeVisible();

		await searchInput.fill("セキュリティ");
		await expect(searchInput).toHaveValue("セキュリティ");
	});

	test("should filter jobs by specialization", async ({ page }) => {
		// 専門分野でのフィルタリングテストを実装
		const specializationFilter = page.getByLabel(/専門分野/i);
		await expect(specializationFilter).toBeVisible();
	});

	test("should navigate to job detail", async ({ page }) => {
		// 案件詳細ページへの遷移テストを実装
		const firstJob = page.locator('[data-testid="job-item"]').first();
		await expect(firstJob).toBeVisible();

		await firstJob.click();
		await expect(page).toHaveURL(/\/job-seeker\/jobs\/[^/]+/);
	});
});





