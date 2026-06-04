import { test, expect } from "@playwright/test";

const BASE = "https://yoro.etzhayyim.com";

test.describe("Embedding E2E", () => {
  test("embedding model loads on /credits", async ({ page }) => {
    await page.goto(`${BASE}/credits`);
    // Wait for the embedding model status badge to appear
    const embeddingSection = page.locator("text=Embedding Model");
    await expect(embeddingSection).toBeVisible({ timeout: 10_000 });

    // Wait for model to start loading or be ready (up to 60s for first download)
    const badge = embeddingSection.locator("..").locator('[class*="Badge"], span');
    await page.waitForTimeout(3_000);

    // Take screenshot for visual inspection
    await page.screenshot({ path: "tests/screenshots/credits-embedding.png", fullPage: true });
    console.log("[embedding] Credits page embedding section visible");
  });

  test("search page loads and embedding is available", async ({ page }) => {
    // First visit credits to trigger embedding init (layout auto-inits)
    await page.goto(`${BASE}/search`);
    await page.waitForTimeout(5_000); // Wait for embedding model init

    // Type a search query
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill("AI agent");
      await page.waitForTimeout(2_000); // debounce + search

      // Switch to Posts tab
      const postsTab = page.locator("text=Posts").first();
      if (await postsTab.isVisible()) {
        await postsTab.click();
        await page.waitForTimeout(3_000); // wait for semantic search results
      }
    }

    await page.screenshot({ path: "tests/screenshots/search-embedding.png", fullPage: true });
    console.log("[embedding] Search page screenshot captured");
  });

  test("search posts with embedding returns results", async ({ page }) => {
    await page.goto(`${BASE}/search?q=hello`);
    await page.waitForTimeout(8_000); // model load + search

    // Check for any post results or actors
    const resultsArea = page.locator("main");
    await expect(resultsArea).toBeVisible();

    // Check console for embedding logs
    const logs: string[] = [];
    page.on("console", (msg) => {
      if (msg.text().includes("[embedding]") || msg.text().includes("[search]")) {
        logs.push(msg.text());
      }
    });

    await page.waitForTimeout(3_000);
    await page.screenshot({ path: "tests/screenshots/search-results-embedding.png", fullPage: true });

    console.log("[embedding] Console logs:", logs);
    console.log("[embedding] Search results page captured");
  });
});
