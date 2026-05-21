import { defineConfig } from '@playwright/test';

const KAMI_BASE_URL = process.env.KAMI_BASE_URL ?? 'https://kami.gftd.ai';
const WORLDS_BASE_URL = process.env.WORLDS_BASE_URL ?? 'https://worlds.gftd.ai';
const KAMI_RT_BASE_URL = process.env.KAMI_RT_BASE_URL ?? 'https://kami-rt.gftd.ai';
const YORO_BASE_URL = process.env.YORO_BASE_URL ?? 'https://yoro.gftd.ai';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  retries: 1,
  workers: 1,
  use: {
    baseURL: KAMI_BASE_URL,
    viewport: { width: 390, height: 844 },
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
  expect: {
    toHaveScreenshot: { maxDiffPixelRatio: 0.05 },
  },
});
