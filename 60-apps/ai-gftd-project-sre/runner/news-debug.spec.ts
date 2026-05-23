import { test, expect } from '@playwright/test';

test('news.etzhayyim.com debug', async ({ page }) => {
  await page.goto('https://news.etzhayyim.com/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.screenshot({ path: '/tmp/news-debug.png', fullPage: true });
  const title = await page.title();
  console.log('Title:', title);
  const hasNav = await page.locator('nav').count();
  const hasHeader = await page.locator('header').count();
  console.log('nav:', hasNav, 'header:', hasHeader);
  const bodyText = await page.locator('body').innerText();
  console.log('Body:', bodyText.slice(0, 300));
});
