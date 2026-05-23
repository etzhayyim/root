import { test, expect } from '@playwright/test';

const KAMI = process.env.KAMI_BASE_URL ?? 'https://kami.etzhayyim.com';
const YORO = process.env.YORO_BASE_URL ?? 'https://yoro.etzhayyim.com';

test.describe('Visual Tests', () => {
  test('kami.etzhayyim.com landing page screenshot', async ({ page }) => {
    await page.goto(KAMI, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshots/kami-landing.png', fullPage: true });
  });

  test('yoro apps/snake page screenshot', async ({ page }) => {
    await page.goto(`${YORO}/apps/did:web:kami.etzhayyim.com:island:snake`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/yoro-snake-app.png', fullPage: true });
  });

  test('yoro apps/colorbynumber page screenshot', async ({ page }) => {
    await page.goto(`${YORO}/apps/did:web:kami.etzhayyim.com:island:colorbynumber`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/yoro-colorbynumber-app.png', fullPage: true });
  });

  test('yoro profile/snake DID screenshot', async ({ page }) => {
    await page.goto(`${YORO}/profile/did:web:kami.etzhayyim.com:island:snake`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/yoro-snake-profile.png', fullPage: true });
  });

  test('yoro profile/colorbynumber DID screenshot', async ({ page }) => {
    await page.goto(`${YORO}/profile/did:web:kami.etzhayyim.com:island:colorbynumber`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/yoro-colorbynumber-profile.png', fullPage: true });
  });
});
