import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.YORO_BASE_URL || 'https://yoro.etzhayyim.com';

export default defineConfig({
	testDir: './tests',
	testMatch: 'iphone-visual-uiux.spec.ts',
	timeout: 60_000,
	workers: 1,
	use: {
		baseURL,
		headless: true,
		colorScheme: 'dark',
		trace: 'on-first-retry',
		screenshot: 'only-on-failure',
	},
	projects: [
		{ name: 'iPhone SE', use: { ...devices['iPhone SE'] } },
		{ name: 'iPhone 12', use: { ...devices['iPhone 12'] } },
		{ name: 'iPhone 14 Pro Max', use: { ...devices['iPhone 14 Pro Max'] } },
	],
	reporter: [['list']],
});
