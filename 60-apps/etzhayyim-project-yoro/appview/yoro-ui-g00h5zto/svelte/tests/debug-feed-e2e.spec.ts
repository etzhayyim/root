/**
 * E2E debug: yoro.etzhayyim.com feed display via kagami B+G DuckDB.
 *
 * Tests the full path:
 *   1. kagami /api/query returns Post data
 *   2. yoro page loads
 *   3. DuckDB-WASM initializes
 *   4. Feed items appear in DOM
 */
import { test, expect } from "@playwright/test";

const KAGAMI_URL = "https://etzhayyim-kagami-2604021830.04-feasts-minded.workers.dev";
const YORO_URL = "https://yoro.etzhayyim.com";

test.describe("Feed E2E Debug", () => {
  test("kagami /api/query returns Posts", async ({ request }) => {
    const res = await request.post(`${KAGAMI_URL}/api/query`, {
      headers: { "Content-Type": "application/json" },
      data: { statement: "MATCH (n:Post) RETURN count(*) AS cnt LIMIT 1" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    console.log("[kagami] Post count:", JSON.stringify(body));
    expect(body.rows).toBeDefined();
    expect(body.rows.length).toBeGreaterThan(0);
    // Should have > 0 posts
    const cnt = body.rows[0]?.[0] ?? body.rows[0]?.cnt ?? 0;
    expect(cnt).toBeGreaterThan(0);
  });

  test("kagami /api/query returns Post data with val", async ({ request }) => {
    const res = await request.post(`${KAGAMI_URL}/api/query`, {
      headers: { "Content-Type": "application/json" },
      data: { statement: "MATCH (n:Post) RETURN n LIMIT 3" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    console.log("[kagami] Post columns:", body.columns);
    console.log("[kagami] Post rows:", body.rows?.length);
    expect(body.rows.length).toBeGreaterThan(0);
  });

  test("yoro page loads and console output", async ({ page }) => {
    const logs: string[] = [];
    page.on("console", (msg) => {
      const text = msg.text();
      if (text.includes("kagami") || text.includes("duckdb") || text.includes("DuckDB") || text.includes("feed") || text.includes("error") || text.includes("Error")) {
        logs.push(`[${msg.type()}] ${text}`);
      }
    });

    page.on("requestfailed", (req) => {
      logs.push(`[FAIL] ${req.url()} ${req.failure()?.errorText}`);
    });

    // Track network requests to kagami
    const kagamiRequests: { url: string; status: number; body?: string }[] = [];
    page.on("response", async (res) => {
      const url = res.url();
      if (url.includes("kagami") || url.includes("api/query") || url.includes("transpile")) {
        let body = "";
        try {
          body = (await res.text()).slice(0, 200);
        } catch (error) {
          console.warn("[silent-fail] debug-feed-e2e.spec.ts: failed to read response body", error);
        }
        kagamiRequests.push({ url, status: res.status(), body });
      }
    });

    await page.goto(YORO_URL, { waitUntil: "domcontentloaded", timeout: 15000 });

    // Wait for DuckDB init + data load
    await page.waitForTimeout(12000);

    // Screenshot
    await page.screenshot({ path: "tests/screenshots/debug-feed-e2e.png", fullPage: false });

    console.log("\n=== Console Logs ===");
    for (const l of logs) console.log(l);

    console.log("\n=== Kagami Network Requests ===");
    for (const r of kagamiRequests) {
      console.log(`  ${r.status} ${r.url}`);
      if (r.body) console.log(`    body: ${r.body}`);
    }

    // Check if any feed items rendered
    const feedItems = await page.locator('[data-testid="feed-item"], .post-card, article, [class*="post"], [class*="feed"]').count();
    console.log(`\n=== Feed items in DOM: ${feedItems} ===`);

    // Check for error messages
    const errorText = await page.locator('[class*="error"], [role="alert"]').allTextContents();
    if (errorText.length > 0) console.log("Errors:", errorText);

    // Check page content
    const bodyText = await page.textContent("body");
    console.log(`\n=== Body text (first 500 chars) ===\n${bodyText?.slice(0, 500)}`);
  });
});
