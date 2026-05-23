import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: '**/*.ts',
  timeout: 60000,
  use: {
    headless: true,
    viewport: { width: 1280, height: 720 },
    launchOptions: {
      args: ['--enable-unsafe-webgpu', '--enable-features=Vulkan', '--no-sandbox'],
    },
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
});
