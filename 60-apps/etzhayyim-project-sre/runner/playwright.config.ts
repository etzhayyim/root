import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 1,
  use: {
    headless: true,
    ignoreHTTPSErrors: false,
  },
  reporter: [["list"], ["json", { outputFile: "/tmp/pw-results.json" }]],
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
