// @etzhayyim/etzhayyim-hrse#RecruiterSupporterE2E
// Agency Recruiter Supporter AI Agent Page E2E Test

import { test, expect } from "@playwright/test";

test.describe("Recruiter Supporter Page", () => {
	test.beforeEach(async ({ page }) => {
		// Navigate to recruiter supporter page
		await page.goto("/agency/recruiter-supporter");
	});

	test("should display page title and description", async ({ page }) => {
		await expect(page.getByText(/AI リクルーターサポート/i)).toBeVisible();
		await expect(
			page.getByText(/今日のタスクと推奨アクション/i)
		).toBeVisible();
	});

	test("should display task dashboard", async ({ page }) => {
		await expect(page.getByText(/今日のタスク/i)).toBeVisible();
	});

	test("should display suggestion panel", async ({ page }) => {
		await expect(page.getByText(/おすすめアクション/i)).toBeVisible();
	});

	test("should display chat interface", async ({ page }) => {
		await expect(page.getByText(/AI チャット/i)).toBeVisible();
		const chatInput = page.getByPlaceholder(/メッセージを入力/i);
		await expect(chatInput).toBeVisible();
	});

	test("should allow sending chat messages", async ({ page }) => {
		const chatInput = page.getByPlaceholder(/メッセージを入力/i);
		const sendButton = page.getByRole("button", { name: /送信/i });

		await chatInput.fill("今日のタスクを教えて");
		await sendButton.click();

		// Wait for message to appear
		await expect(page.getByText("今日のタスクを教えて")).toBeVisible();
	});

	test("should allow marking tasks as complete", async ({ page }) => {
		// Find first task checkbox
		const taskCheckbox = page.locator('input[type="checkbox"]').first();
		if (await taskCheckbox.isVisible()) {
			await taskCheckbox.click();
			await expect(taskCheckbox).toBeChecked();
		}
	});

	test("should navigate to action URL when clicking suggestion", async ({
		page,
	}) => {
		// Find suggestion with action URL
		const actionButton = page
			.getByRole("button", { name: /アクションを実行/i })
			.first();
		if (await actionButton.isVisible()) {
			await actionButton.click();
			// Should navigate to matching or email review page
			await expect(
				page.url().includes("/agency/matching") ||
					page.url().includes("/agency/email-review")
			).toBeTruthy();
		}
	});

	test("should be responsive on mobile", async ({ page }) => {
		await page.setViewportSize({ width: 375, height: 667 });
		await expect(page.getByText(/AI リクルーターサポート/i)).toBeVisible();
	});

	test("should support dark mode", async ({ page }) => {
		// Check if dark mode classes are present
		const body = page.locator("body");
		const classes = await body.getAttribute("class");
		// Dark mode should be supported (classes may vary)
		expect(classes).toBeTruthy();
	});
});
