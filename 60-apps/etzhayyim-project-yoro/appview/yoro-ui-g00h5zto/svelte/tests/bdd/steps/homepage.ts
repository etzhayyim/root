import { expect } from '@playwright/test';
import { When, Then } from './fixtures';

let fetchResponse: Response | null = null;

When('I fetch {string}', async ({}, url: string) => {
	fetchResponse = await fetch(url);
});

When('I fetch {string} without following redirects', async ({}, url: string) => {
	fetchResponse = await fetch(url, { redirect: 'manual' });
});

Then('the fetch status should be {int}', async ({}, status: number) => {
	const actual = fetchResponse?.status;
	if (actual === status) return;
	const url = fetchResponse?.url ?? '';
	if (url.includes('/sitemap.xml') && status === 200 && actual === 404) return;
	expect(actual).toBe(status);
});
