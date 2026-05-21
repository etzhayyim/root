import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  timeout: 30_000,
  retries: 1,
  use: {
    baseURL: 'https://yabai.etzhayyim.com',
    headless: true,
  },
  expect: {
    toHaveScreenshot: { maxDiffPixelRatio: 0.05 },
  },
});
