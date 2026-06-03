import { expect, test } from '@playwright/test';

test('goriketsu local page boots and exposes HUD state', async ({ page }) => {
  await page.goto('/play-webgpu.html');
  await expect(page.locator('#gc')).toBeVisible();
  await expect(page.locator('#hud-phase')).toHaveText('Sneak');
  await expect(page.locator('#hud-stamina')).toContainText('100');
  await expect(page.locator('#hud-score')).toContainText('0');
  await expect(page.locator('#hud-banana')).toHaveText('BANANA: 0/0');
});
