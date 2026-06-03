/**
 * smoke.spec.ts — Generic SRE smoke tests executed per SpinApp.
 *
 * The target hostname is injected via the TARGET_URL environment variable.
 * The Playwright runner (run.ts) sets this before each test run.
 */
import { test, expect } from "@playwright/test";

const baseURL = process.env.TARGET_URL ?? "https://localhost";

test.describe("SRE smoke", () => {
  test("page loads and returns 200", async ({ page }) => {
    const response = await page.goto(baseURL, { waitUntil: "domcontentloaded" });
    expect(response?.status(), `${baseURL} should return 200`).toBe(200);
  });

  test("h1 is visible", async ({ page }) => {
    await page.goto(baseURL, { waitUntil: "domcontentloaded" });
    const h1 = page.locator("h1").first();
    await expect(h1).toBeVisible({ timeout: 10_000 });
  });

  test("/health endpoint returns 200", async ({ request }) => {
    const res = await request.get(`${baseURL}/health`);
    expect(res.status(), `${baseURL}/health should return 200`).toBe(200);
  });

  test("meta description is present", async ({ page }) => {
    await page.goto(baseURL, { waitUntil: "domcontentloaded" });
    const content = await page
      .locator('meta[name="description"]')
      .getAttribute("content");
    expect(content, "meta description should not be empty").toBeTruthy();
  });

  test("no JS console errors on load", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.goto(baseURL, { waitUntil: "domcontentloaded" });
    expect(errors, `console errors on ${baseURL}: ${errors.join(", ")}`).toHaveLength(0);
  });
});
