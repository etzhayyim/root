import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: ".",
  testMatch: ["debug-*.spec.ts"],
  timeout: 60_000,
  use: {
    baseURL: "https://yoro.gftd.ai",
    headless: false,
    viewport: { width: 390, height: 844 },
  },
});
