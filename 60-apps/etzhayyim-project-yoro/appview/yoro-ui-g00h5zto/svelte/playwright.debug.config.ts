import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: ['kagami-provider-debug.spec.ts', 'pds-e2e.spec.ts'],
  timeout: 120_000,
  workers: 1,
  use: {
    baseURL: process.env.YORO_BASE_URL || 'https://yoro.etzhayyim.com',
    headless: false,
    viewport: { width: 390, height: 844 },
    trace: 'on',
    screenshot: 'on',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    bypassCSP: true,
    ignoreHTTPSErrors: true,
    contextOptions: {
      serviceWorkers: 'block',
    },
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
  reporter: [['list']],
});
