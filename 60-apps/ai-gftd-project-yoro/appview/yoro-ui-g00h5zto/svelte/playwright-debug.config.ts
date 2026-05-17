import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: 'debug-edge-freeze.spec.ts',
  timeout: 120_000,
  workers: 1,
  use: {
    baseURL: process.env.YORO_BASE_URL || 'https://yoro.etzhayyim.com',
    headless: true,
    viewport: { width: 390, height: 844 },
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    {
      name: 'edge',
      use: {
        channel: 'msedge',
      },
    },
  ],
  reporter: [['list']],
});
