// @etzhayyim/cyber-freelance#MatchingE2E
// マッチング機能のE2Eテスト

import { test, expect } from "@playwright/test";

test.describe("Matching Feature", () => {
	test("should display match score", async ({ page }) => {
		await page.goto("/job-seeker/jobs/job-1");

		// マッチングスコアの表示を確認
		const matchScore = page.locator('[data-testid="match-score"]');
		await expect(matchScore).toBeVisible();
	});

	test("should show recommended jobs", async ({ page }) => {
		await page.goto("/job-seeker/jobs");

		// おすすめ案件の表示を確認
		const recommendedSection = page.locator('[data-testid="recommended-jobs"]');
		await expect(recommendedSection).toBeVisible();
	});

	test("should show recommended job seekers", async ({ page }) => {
		await page.goto("/recruiter/jobs/job-1");

		// おすすめ求職者の表示を確認
		const recommendedSection = page.locator('[data-testid="recommended-job-seekers"]');
		await expect(recommendedSection).toBeVisible();
	});
});





